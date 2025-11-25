from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
import datetime
import uuid

from klabban.web import forms
from klabban import models

module = Blueprint("users", __name__, url_prefix="/users")


@module.route("", methods=["GET"])
# @login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)

    users = []
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

    return render_template(
        "/users/index.html",
        users_pagination=pagination,
        form=form
    )
