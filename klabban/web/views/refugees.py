from flask import abort, Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from ..utils.acl import roles_required
from klabban import models
from klabban.web import caches, forms
from mongoengine.queryset.visitor import Q
from uuid import uuid4
from flask_mongoengine import Pagination
from datetime import datetime

module = Blueprint("refugees", __name__, url_prefix="/refugees")


@caches.cache.memoize(timeout=60)
def get_refugee_camp_choices():
    camps = models.RefugeeCamp.objects(status__ne="deactive").order_by("name")
    camp_choice = [(str(camp.id), camp.name) for camp in camps]
    active_camps = []
    for camp in camps:
        # Count refugees in this camp
        refugee_count = models.Refugee.objects(
            refugee_camp=camp.id, status__ne="deactive"
        ).count()
        if refugee_count > 0:
            active_camps.append((str(camp.id), camp.name))
    return camp_choice, active_camps


@module.route("/")
def index():
    view_mode = request.args.get("view_mode", "list")

    page = request.args.get("page", 1, type=int)
    per_page = 50  # จำนวนรายการต่อหน้า
    camp_choice, active_camps = get_refugee_camp_choices()

    search_form = forms.refugees.RefugeeSearchForm(request.args)
    search_form.refugee_camp.choices = [("", "ทั้งหมด")] + active_camps
    search = search_form.search.data
    refugee_camp_id = search_form.refugee_camp.data
    country = search_form.country.data
    status = search_form.status.data
    exclude_thai = request.args.get("exclude_thai", None)

    change_camp_form = forms.refugees.ChangeRefugeeCampForm()
    change_camp_form.refugee_camp.choices = camp_choice
    change_camp_form.refugee_camp.data = ""

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
    if status:
        query = query.filter(status=status)
    if exclude_thai:
        query = query.filter(country__ne="Thailand")
    try:
        refugees_pagination = Pagination(query, page=page, per_page=per_page)
    except ValueError:
        refugees_pagination = Pagination(query, page=1, per_page=per_page)

    return render_template(
        "/refugees/index.html",
        refugees_pagination=refugees_pagination,
        search_form=search_form,
        change_camp_form=change_camp_form,
        view_mode=view_mode,
    )


@module.route("/<refugee_id>/change_status/", methods=["POST", "GET"])
def change_status(refugee_id):
    refugee = models.Refugee.objects.get(id=refugee_id)
    # name_confirmation = request.form.get("name_confirmation")
    # refugee_name_confirm = request.form.get("refugee_name_confirm")

    if refugee.status == "active":
        refugee.status = "back_home"
        refugee.back_home_date = datetime.now()
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
        old_status = refugee.status
        old_camp = refugee.refugee_camp

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
    else:
        # 3. ถ้าไม่ใช่ admin หรือ refugee_camp_staff ให้ตั้งค่า refugee_camp ตาม request args
        form.refugee_camp.choices = []
    # ถ้ามีค่าจาก request args ให้ตั้งค่า refugee_camp
    refugee_camp_id = request.args.get("refugee_camp_id", None)
    if refugee_camp_id:
        refugee_camp = models.RefugeeCamp.objects(id=refugee_camp_id).first()
        form.refugee_camp.data = str(refugee_camp.id)

    if not form.validate_on_submit() or request.method == "GET":
        if refugee_id:
            form.refugee_camp.data = str(refugee.refugee_camp.id)

        if current_user.is_authenticated and "refugee_camp_staff" in current_user.roles:
            form.refugee_camp.data = str(current_user.refugee_camp.id)

        if request.args.get("refugee_camp_id"):
            refugee_camp = models.RefugeeCamp.objects(
                id=request.args.get("refugee_camp_id")
            ).first()
            form.refugee_camp.choices = [(str(refugee_camp.id), refugee_camp.name)]
            form.refugee_camp.data = str(refugee_camp.id)

        return render_template(
            "refugees/create_or_edit.html",
            form=form,
            refugee_id=refugee_id,
        )

    is_confirm = request.form.get("is_confirm", "no")
    form.name.data = form.name.data.strip()
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

    user = current_user._get_current_object() if current_user.is_authenticated else None
    ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)

    log = models.RefugeeStatusLog(
        status=refugee.status,
        changed_by=user,
        ip_address=ip_address,
    )
    camp_log = models.RefugeeCampsLog(
        refugee_camp=refugee.refugee_camp,
        changed_by=user,
        ip_address=ip_address,
    )

    if not refugee_id:
        refugee.status_log.append(log)
        refugee.camp_log.append(camp_log)
    elif refugee_id:
        if form.status.data != old_status:
            refugee.status_log.append(log)
        elif form.refugee_camp.data != old_camp:
            refugee.camp_log.append(camp_log)

    refugee.save()

    return redirect(url_for("refugees.index"))


@module.route("/<refugee_id>/change_camp/<camp_id>", methods=["POST", "GET"])
@roles_required(["admin", "refugee_camp_staff"])
def change_camp(refugee_id, camp_id):
    refugee = models.Refugee.objects.get(id=refugee_id)
    new_camp = models.RefugeeCamp.objects.get(id=camp_id)
    refugee.refugee_camp = new_camp
    # Log the camp change
    camp_log = models.RefugeeCampsLog(
        refugee_camp=new_camp,
        changed_by=(
            current_user._get_current_object()
            if current_user.is_authenticated
            else None
        ),
        ip_address=request.headers.get("X-Forwarded-For", request.remote_addr),
    )
    refugee.camp_log.append(camp_log)
    refugee.save()

    return redirect(url_for("refugees.index", **request.args))


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


# ผู้อพยพไม่สามารถกดยืนยันชื่อได้(Error) ให้ทิ้ง note ไว้ให้ผู้ดูแลระบบมาตรวจสอบที่หลัง
@module.route("/description/create/<refugee_id>", methods=["GET", "POST"])
def create_description(refugee_id):

    # form = forms.refugees.RefugeeForm()
    if refugee_id:
        refugee = models.Refugee.objects.get(id=refugee_id)
        form = forms.refugees.RefugeeForm(obj=refugee)

    if not form.validate_on_submit():

        return render_template("refugees/note_on_validation_fail.html", form=form)

    ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)

    # Log
    # log = ...(
    # ip_address=ip_address,
    # )

    return redirect("dashboard.index")


@module.route("/view_descriptions")
def view_description():

    # pagination

    return render_template("refugees/view_description.html")


@module.route("change_status_description")
def change_status_description():

    # if

    return redirect(url_for("refugees.view_description"))
