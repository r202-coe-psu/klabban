from flask import abort, Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from ..utils.acl import roles_required
from klabban import models
from klabban.web import forms
from mongoengine.queryset.visitor import Q
from uuid import uuid4
from flask_mongoengine import Pagination
from datetime import datetime

module = Blueprint("refugees", __name__, url_prefix="/refugees")


@module.route("/")
def index():
    view_mode = request.args.get("view_mode", "list")

    page = request.args.get("page", 1, type=int)
    per_page = 50  # จำนวนรายการต่อหน้า

    search_form = forms.refugees.RefugeeSearchForm(request.args)
    search_form.refugee_camp.choices = [("", "ทั้งหมด")] + [
        (str(camp.id), camp.name)
        for camp in models.RefugeeCamp.objects(status__ne="deactive").order_by("name")
    ]
    search = search_form.search.data
    refugee_camp_id = search_form.refugee_camp.data
    country = search_form.country.data
    query = models.Refugee.objects(id=None)
    try:
        if "refugee_camp_staff" in current_user.roles or "admin" in current_user.roles:
            query = models.Refugee.objects(status__ne="deactive").order_by("name")
    except Exception:
        query = models.Refugee.objects(id=None)
    if search or country:
        query = models.Refugee.objects(status__ne="deactive").order_by("name")
    if search:
        query = query.filter(
            Q(name__icontains=search)
            | Q(nick_name__icontains=search)
            | Q(phone__icontains=search)
        )
    if refugee_camp_id:
        query = query.filter(refugee_camp=refugee_camp_id)
    if country:
        query = query.filter(country__icontains=country)
    if request.args.get("exclude_thai"):
        query = query.filter(country__ne="ไทย")
    try:
        refugees_pagination = Pagination(query, page=page, per_page=per_page)
    except ValueError:
        refugees_pagination = Pagination(query, page=1, per_page=per_page)

    return render_template(
        "/refugees/index.html",
        refugees_pagination=refugees_pagination,
        search_form=search_form,
        view_mode=view_mode,
    )


@module.route("/<refugee_id>/change_status/", methods=["POST", "GET"])
def change_status(refugee_id):
    refugee = models.Refugee.objects.get(id=refugee_id)
    # name_confirmation = request.form.get("name_confirmation")
    # refugee_name_confirm = request.form.get("refugee_name_confirm")

    if refugee.status == "active":
        refugee.status = "back_home"
        flash(f"สถานะของ **{refugee.name}** ถูกเปลี่ยนเป็น 'กลับบ้านแล้ว' สำเร็จ.", "success")

    elif refugee.status == "back_home":
        refugee.status = "active"
        flash(
            f"สถานะของ **{refugee.name}** ถูกเปลี่ยนกลับเป็น 'อยู่ในศูนย์พักพิง' สำเร็จ.", "success"
        )

    else:
        flash(
            f"ไม่สามารถเปลี่ยนสถานะของ **{refugee.name}** ได้ เนื่องจากสถานะปัจจุบันคือ {refugee.status}.",
            "error",
        )
        return redirect(url_for("refugees.index", **request.args))

    log = models.RefugeeStatusLog(
        status=refugee.status,
        changed_by=(
            current_user._get_current_object()
            if current_user.is_authenticated
            else None
        ),
        ip_address=request.headers.get("X-Forwarded-For", request.remote_addr),
    )
    refugee.status_log.append(log)
    refugee.save()

    return redirect(url_for("refugees.index", **request.args))


@module.route("/create", methods=["GET", "POST"], defaults={"refugee_id": None})
@module.route("/<refugee_id>/edit", methods=["GET", "POST"])
# @roles_required(["admin", "refugee_camp_staff"])
def create_or_edit(refugee_id):
    form = forms.refugees.RefugeeForm()
    refugee = models.Refugee()
    if refugee_id:
        refugee = models.Refugee.objects.get(id=refugee_id)
        form = forms.refugees.RefugeeForm(obj=refugee)

    if current_user.is_authenticated and "admin" in current_user.roles:
        # 1. ถ้าเป็น admin ให้แสดงตัวเลือก refugee_camp ทั้งหมด
        form.refugee_camp.choices = [
            (str(camp.id), camp.name)
            for camp in models.RefugeeCamp.objects(status__ne="deactive").order_by(
                "name"
            )
        ]
    elif current_user.is_authenticated and "refugee_camp_staff" in current_user.roles:
        # 2. ถ้าเป็น refugee_camp_staff ให้ตั้งค่า refugee_camp เป็นของตัวเอง
        form.refugee_camp.choices = [
            (str(current_user.refugee_camp.id), current_user.refugee_camp.name)
        ]
        form.refugee_camp.data = str(current_user.refugee_camp.id)
    else:
        # 3. ถ้าไม่ใช่ admin หรือ refugee_camp_staff ให้ตั้งค่า refugee_camp ตาม request args
        form.refugee_camp.choices = []
        if request.args.get("refugee_camp_id"):
            refugee_camp = models.RefugeeCamp.objects(
                id=request.args.get("refugee_camp_id")
            ).first()
            form.refugee_camp.choices = [(str(refugee_camp.id), refugee_camp.name)]
            form.refugee_camp.data = str(refugee_camp.id)

    # ถ้ามีค่าจาก request args ให้ตั้งค่า refugee_camp
    refugee_camp_id = request.args.get("refugee_camp_id", None)
    if refugee_camp_id:
        refugee_camp = models.RefugeeCamp.objects(id=refugee_camp_id).first()
        form.refugee_camp.data = str(refugee_camp.id)

    if not form.validate_on_submit() or request.method == "GET":
        return render_template(
            "refugees/create_or_edit.html",
            form=form,
            refugee_id=refugee_id,
        )

    is_confirm = request.form.get("is_confirm", "no")
    duplicated_refugee = models.Refugee.objects(
        name=form.name.data,
    )
    if duplicated_refugee and is_confirm != "yes" and not refugee_id:
        return render_template(
            "refugees/create_or_edit.html",
            form=form,
            refugee_id=refugee_id,
            duplicated_refugee=duplicated_refugee,
        )

    # ถ้าไม่ระบุวันที่กลับบ้าน แต่สถานะเปลี่ยนเป็นกลับบ้าน ให้ตั้งค่าวันที่กลับบ้านเป็นวันที่ปัจจุบัน
    if form.status.data == "back_home" and not form.back_home_date.data:
        form.back_home_date.data = datetime.now()

    form.populate_obj(refugee)
    refugee.refugee_camp = models.RefugeeCamp.objects.get(id=form.refugee_camp.data)
    if current_user.is_authenticated:
        if not refugee_id:
            refugee.created_by = current_user._get_current_object()
        refugee.updated_by = current_user._get_current_object()

    refugee.save()

    return redirect(url_for("refugees.index"))


@module.route("/<refugee_id>", methods=["GET"])
@roles_required(["admin", "refugee_camp_staff"])
def view_refugee(refugee_id):
    refugee = models.Refugee.objects(id=refugee_id).first()
    if (
        "admin" not in current_user.roles
        and refugee.refugee_camp.id != current_user.refugee_camp.id
    ):
        return abort(403)
    return render_template("refugees/view.html", refugee=refugee)


@module.route("/delete/<refugee_id>", methods=["POST"])
@roles_required(["admin", "refugee_camp_staff"])
def delete_refugee(refugee_id):
    refugee = models.Refugee.objects(id=refugee_id).first()
    if (
        "admin" not in current_user.roles
        and refugee.refugee_camp.id != current_user.refugee_camp.id
    ):
        return abort(403)
    if refugee:
        refugee.status = "deactive"
        refugee.save()
    return redirect(url_for("refugees.index"))
