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

    return render_template("/users/index.html", users_pagination=pagination, form=form, total=users.count())


@module.route("/create", methods=["GET", "POST"], defaults={"user_id": None})
@module.route("/<user_id>/edit", methods=["GET", "POST"])
@roles_required(["admin", "refugee_camp_staff"])
def create_or_edit_user(user_id):
    form = forms.users.CreateUserForm()

    user = models.User()

    if user_id:
        user = models.User.objects.get(id=user_id)
        form = forms.users.EditUserForm(obj=user)
    if "refugee_camp_staff" in current_user.roles:
        form.refugee_camp.choices = [
            (str(current_user.refugee_camp.id), current_user.refugee_camp.name)
        ]
        print("Refugee camp staff, limited choices:", form.refugee_camp.choices)
    else:
        refugee_camps = models.RefugeeCamp.objects().order_by("name")
        form.refugee_camp.choices = [
            (str(camp.id), camp.name) for camp in refugee_camps
        ]
        print("All refugee camps:", form.refugee_camp.choices)
    form.role.choices = [
        ("refugee_camp_staff", "เจ้าหน้าที่ศูนย์พักพิง"),
    ]
    if not form.validate_on_submit():
        print("Form errors:", form.errors)
        form.role.data = user.roles[0] if user.roles else "user"
        return render_template("/users/create_or_edit.html", form=form, user_id=user_id)

    if (
        not user_id
        and models.User.objects(username=form.username.data, id__ne=user_id).first()
    ):
        flash("ชื่อบัญชีนี้มีผู้ใช้งานแล้ว กรุณาเปลี่ยนชื่อบัญชีใหม่", "error")
        return render_template("/users/create_or_edit.html", form=form, user_id=user_id)

    if "refugee_camp_staff" == form.role.data:
        if not form.refugee_camp.data:
            flash("กรุณาเลือกศูนย์พักพิงสำหรับเจ้าหน้าที่ศูนย์พักพิง", "error")
            return render_template(
                "/users/create_or_edit.html", form=form, user_id=user_id
            )

    form.populate_obj(user)
    if not user_id and form.password.data:
        user.set_password(form.password.data)
    user.refugee_camp = models.RefugeeCamp.objects.get(id=form.refugee_camp.data)
    user.roles = [form.role.data]
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
