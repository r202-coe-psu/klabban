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
from bson import ObjectId

module = Blueprint("missing_persons", __name__, url_prefix="/missing_persons")

@module.route("/")
def index():
    missing_persons = models.MissingPerson.objects(status="active").order_by("name")
    return render_template("/missing_persons/index.html", missing_persons=missing_persons)

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

@module.route("/<missing_person_id>/view", methods=["GET"])
def view_missing_person(missing_person_id):
    missing_person = models.MissingPerson.objects.get(id=missing_person_id)
    return render_template(
        "/missing_persons/view_missing_person.html", missing_person=missing_person
    )

@module.route("/<missing_person_id>/delete", methods=["POST"])
@roles_required(["admin", "refugee_camp_staff"])
def delete_missing_person(missing_person_id):
    missing_person = models.MissingPerson.objects.get(id=missing_person_id)
    missing_person.status = "deactive"
    missing_person.updated_date = datetime.datetime.now()
    missing_person.updater = current_user._get_current_object()
    missing_person.save()

    flash("ลบข้อมูลบุคคลสูญหายเรียบร้อยแล้ว", "success")
    return redirect(url_for("missing_persons.index"))

