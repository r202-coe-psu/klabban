from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
import datetime
import uuid

from klabban.web import forms
from klabban import models

module = Blueprint("users", __name__, url_prefix="/users")


@module.route("", methods=["GET"])
@login_required
def index():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "", type=str)

    users = models.User.objects()
    total = 0

    class Pagination:
        def __init__(self, items, page, per_page, total):
            self.items = items
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = max(1, (total + per_page - 1) // per_page)
            self.has_prev = page > 1
            self.has_next = page < self.pages
            self.prev_num = page - 1 if self.has_prev else None
            self.next_num = page + 1 if self.has_next else None

    pagination = Pagination(users, page, 20, total)

    form = forms.users.SearchUserForm()
    form.search.data = search

    return render_template("/users/index.html", users_pagination=pagination, form=form)


@module.route("/create", methods=["GET", "POST"], defaults={"user_id": None})
@module.route("/<user_id>/edit", methods=["GET", "POST"])
@login_required
def create_or_edit_user(user_id):
    form = forms.accounts.CreateAccountForm()
    user = models.User()

    if user_id:
        user = models.User.objects.get(id=user_id)
        form = forms.accounts.CreateAccountForm(obj=user)

    if not form.validate_on_submit():
        print("Form errors:", form.errors)
        return render_template("/users/create_or_edit.html", form=form, user_id=user_id)

    # ตรวจสอบ email ซ้ำ (ยกเว้นกรณี edit ตัวเอง)
    existing_email = models.User.objects(email=form.email.data).first()
    if existing_email and (not user_id or str(existing_email.id) != user_id):
        flash("อีเมลนี้ถูกใช้แล้ว", "error")
        return render_template("/users/create_or_edit.html", form=form, user_id=user_id)

    # อัปเดตข้อมูลผู้ใช้
    if not user_id:
        # สร้างใหม่
        user.created_date = datetime.datetime.now()
        user.status = "active"  # default status
        user.roles = ["user"]  # default role
        user.last_login_date = datetime.datetime.now()

    user.first_name = form.first_name.data
    user.last_name = form.last_name.data
    user.username = form.email.data
    user.email = form.email.data
    user.phone_number = form.phone_number.data or ""
    user.updated_date = datetime.datetime.now()

    if form.password.data:
        user.set_password(form.password.data)

    try:
        user.save()
        if user_id:
            flash("อัปเดตบัญชีเรียบร้อยแล้ว", "success")
        else:
            flash("สร้างบัญชีเรียบร้อยแล้ว", "success")
        return redirect(url_for("users.index"))
    except Exception as e:
        flash(f"เกิดข้อผิดพลาด: {str(e)}", "error")
        return render_template("/users/create_or_edit.html", form=form, user_id=user_id)


@module.route("/<user_id>/delete", methods=["POST"])
@login_required
def delete_user(user_id):
    # TODO: ลบบัญชี
    return redirect(url_for("users.index"))
