from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from mongoengine.queryset.visitor import Q
import datetime
import uuid
from flask_mongoengine import Pagination
from klabban.web import forms
from klabban import models
from klabban.web.utils.acl import roles_required

module = Blueprint("users", __name__, url_prefix="/users")


@module.route("", methods=["GET"])
@roles_required(["admin", "refugee_camp_staff"])
def index():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "", type=str).strip()

    users = models.User.objects()
    if "refugee_camp_staff" in current_user.roles:
        users = users.filter(refugee_camp=current_user.refugee_camp)
    if search:
        users = users.filter(
            (Q(username__icontains=search))
            | (Q(first_name__icontains=search))
            | (Q(last_name__icontains=search))
            | (Q(display_name__icontains=search))
            | (Q(email__icontains=search))
        )
    try:
        pagination = Pagination(users, page, per_page=20)
    except Exception as e:
        pagination = Pagination(users, 1, per_page=20)

    form = forms.users.SearchCreateUserForm()
    form.search.data = search

    return render_template(
        "/users/index.html", users_pagination=pagination, form=form, total=users.count()
    )


@module.route("/create", methods=["GET", "POST"], defaults={"user_id": None})
@module.route("/<user_id>/edit", methods=["GET", "POST"])
@roles_required(["admin", "refugee_camp_staff"])
def create_or_edit_user(user_id):
    form = forms.users.CreateUserForm()

    user = models.User()
    USER_ROLES = [
        ("user", "ผู้ใช้งานทั่วไป"),
        ("admin", "ผู้ดูแลระบบ"),
        ("refugee_camp_staff", "เจ้าหน้าที่ศูนย์พักพิง"),
        ("officer", "เจ้าหน้าที่"),
    ]
    if user_id:
        user = models.User.objects.get(id=user_id)
        form = forms.users.EditUserForm(obj=user)

    if "admin" in current_user.roles:
        refugee_camps = models.RefugeeCamp.objects().order_by("name")
        form.refugee_camp.choices = [
            (str(camp.id), camp.name) for camp in refugee_camps
        ]
        print("All refugee camps:", form.refugee_camp.choices)
        form.roles.choices = USER_ROLES

    elif "refugee_camp_staff" in current_user.roles:
        if not current_user.refugee_camp:
            flash("คุณไม่มีศูนย์พักพิงที่ถูกกำหนด โปรดติดต่อผู้ดูแลระบบ", "error")
            return redirect(url_for("users.index"))

        form.refugee_camp.choices = [
            (str(current_user.refugee_camp.id), current_user.refugee_camp.name)
        ]

        form.roles.choices = [
            ("refugee_camp_staff", "เจ้าหน้าที่ศูนย์พักพิง"),
            ("user", "ผู้ใช้งานทั่วไป"),
        ]
    if not form.validate_on_submit():
        form.roles.data = [role for role in user.roles]

        return render_template("/users/create_or_edit.html", form=form, user_id=user_id)

    if (
        not user_id
        and models.User.objects(username=form.username.data, id__ne=user_id).first()
    ):
        flash("ชื่อบัญชีนี้มีผู้ใช้งานแล้ว กรุณาเปลี่ยนชื่อบัญชีใหม่", "error")
        return render_template("/users/create_or_edit.html", form=form, user_id=user_id)

    if "refugee_camp_staff" in form.roles.data:
        if not form.refugee_camp.data:
            flash("กรุณาเลือกศูนย์พักพิงสำหรับเจ้าหน้าที่ศูนย์พักพิง", "error")
            return render_template(
                "/users/create_or_edit.html", form=form, user_id=user_id
            )

    form.populate_obj(user)
    if not user_id and form.password.data:
        user.set_password(form.password.data)
    user.refugee_camp = models.RefugeeCamp.objects.get(id=form.refugee_camp.data)
    user.roles = [role for role in form.roles.data]
    user.save()

    return redirect(url_for("users.index"))


@module.route("/<user_id>/delete", methods=["POST"])
@roles_required(["admin", "refugee_camp_staff"])
def delete_user(user_id):
    user = models.User.objects(id=user_id).first()
    if user:
        user.status = "inactive"
        user.updated_date = datetime.datetime.now()
        user.updated_by = current_user._get_current_object()
        user.save()
    return redirect(url_for("users.index"))


@module.route("/<user_id>/reset_password", methods=["POST"])
@roles_required(["admin", "refugee_camp_staff"])
def reset_password_user(user_id):
    user = models.User.objects(id=user_id).first()
    if user:
        user.set_password(user.username)
        user.save()
    return redirect(url_for("users.index"))
