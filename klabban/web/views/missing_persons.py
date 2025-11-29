from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    send_file,
    current_app,
    flash,
)
from flask_login import login_required, current_user
from mongoengine.queryset.visitor import Q
from uuid import uuid4

import pandas as pd
import datetime

from klabban import models
from klabban.web import forms, utils, redis_rq
from klabban.web.utils.acl import roles_required
from flask_mongoengine import Pagination

from bson import ObjectId

module = Blueprint("missing_persons", __name__, url_prefix="/missing_persons")


@login_required
@roles_required(["officer"])
@module.route("/")
def index():
    view_mode = request.args.get("view_mode", "list")

    page = request.args.get("page", 1, type=int)
    per_page = 50  # จำนวนรายการต่อหน้า
    search_form = forms.missing_persons.MissingPersonSearchForm(request.args)

    search = search_form.search.data
    status = search_form.status.data

    query = models.MissingPerson.objects(id=None)

    if search:
        query &= Q(
            Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(identification_number__icontains=search)
        )
    if status:
        query &= Q(missing_person_status=status)

    try:
        missing_persons_pagination = Pagination(query, page=page, per_page=per_page)
    except ValueError:
        missing_persons_pagination = Pagination(query, page=1, per_page=per_page)

    return render_template(
        "/missing_persons/index.html",
        missing_persons_pagination=missing_persons_pagination,
        search_form=search_form,
        view_mode=view_mode,
    )


@login_required
@roles_required(["officer"])
@module.route("/create", methods=["GET", "POST"], defaults={"missing_person_id": None})
def create_or_edit_missing_person(missing_person_id=None):
    form = forms.missing_persons.MissingPersonForm()
    missing_person = models.MissingPerson()

    if missing_person_id:
        missing_person = models.MissingPerson.objects.get(id=missing_person_id)
        form = forms.missing_persons.MissingPersonForm(obj=missing_person)

    if form.validate_on_submit():
        form.populate_obj(missing_person)
        missing_person.updated_date = datetime.datetime.now()
        missing_person.updater = current_user._get_current_object()
        if not missing_person_id:
            missing_person.created_date = datetime.datetime.now()
            missing_person.creator = current_user._get_current_object()
        missing_person.save()

        flash("บันทึกข้อมูลบุคคลสูญหายเรียบร้อยแล้ว", "success")
        return redirect(url_for("missing_persons.index"))

    return render_template(
        "/missing_persons/create_or_edit_missing_person.html",
        form=form,
        missing_person=missing_person,
    )


@login_required
@roles_required(["officer"])
@module.route("/<missing_person_id>/view", methods=["GET"])
def view_missing_person(missing_person_id):
    missing_person = models.MissingPerson.objects.get(id=missing_person_id)
    return render_template(
        "/missing_persons/view_missing_person.html", missing_person=missing_person
    )


@login_required
@roles_required(["officer"])
@module.route("/<missing_person_id>/delete", methods=["POST"])
def delete_missing_person(missing_person_id):
    missing_person = models.MissingPerson.objects.get(id=missing_person_id)
    missing_person.status = "deactive"
    missing_person.updated_date = datetime.datetime.now()
    missing_person.updater = current_user._get_current_object()
    missing_person.save()

    flash("ลบข้อมูลบุคคลสูญหายเรียบร้อยแล้ว", "success")
    return redirect(url_for("missing_persons.index"))


@login_required
@roles_required(["officer"])
@module.route("/import_missing_person_modal", methods=["GET"])
def import_missing_person_modal():
    form = forms.missing_persons.MissingPersonImportForm()
    return render_template(
        "/missing_persons/modals/import_missing_person_modal.html", form=form
    )


@login_required
@roles_required(["officer"])
@module.route("/export_missing_person_modal", methods=["GET"])
def export_missing_person_modal():
    form = forms.missing_persons.MissingPersonExportForm()
    refugee_camps = models.RefugeeCamp.objects(status="active").order_by("name")
    form.refugee_camp_export.choices = [("", "ทั้งหมด")] + [
        (str(camp.id), camp.name) for camp in refugee_camps
    ]
    return render_template(
        "/missing_persons/modals/export_missing_person_modal.html", form=form
    )
