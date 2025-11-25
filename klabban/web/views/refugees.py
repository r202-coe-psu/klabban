from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user

from klabban import models
from klabban.web import forms
from mongoengine.queryset.visitor import Q
from uuid import uuid4

import pandas as pd
import datetime

module = Blueprint("refugees", __name__, url_prefix="/refugees")


@module.route("/")
def index():
    search_form = forms.refugees.RefugeeSearchForm(request.args)
    search_form.refugee_camp.choices = [("", "ทั้งหมด")] + [
        (str(camp.id), camp.name)
        for camp in models.RefugeeCamp.objects(status__ne="deactive").order_by("name")
    ]
    search = search_form.search.data
    refugee_camp_id = search_form.refugee_camp.data

    refugees = models.Refugee.objects(status__ne="deactive").order_by("name")
    if search:
        refugees = refugees.filter(
            Q(name__icontains=search) | Q(nick_name__icontains=search)
        )
    if refugee_camp_id:
        refugees = refugees.filter(refugee_camp=refugee_camp_id)

    return render_template(
        "/refugees/index.html", refugees=refugees, search_form=search_form
    )


@module.route("/create", methods=["GET", "POST"], defaults={"refugee_id": None})
@module.route("/<refugee_id>/edit", methods=["GET", "POST"])
@login_required
def create_or_edit(refugee_id):
    form = forms.refugees.RefugeeForm()
    form.refugee_camp.choices = [
        (str(camp.id), camp.name)
        for camp in models.RefugeeCamp.objects(status__ne="deactive").order_by("name")
    ]
    refugee = models.Refugee()

    if refugee_id:
        refugee = models.Refugee.objects.get(id=refugee_id)
        form = forms.refugees.RefugeeForm(obj=refugee)
    # else:
    #   refugee.created_by = current_user._get_current_object()

    if request.method == "GET":
        return render_template(
            "refugees/create_or_edit.html",
            form=form,
            refugee_id=refugee_id,
        )

    if not form.validate_on_submit():
        return redirect(
            url_for(
                "refugees.index",
                **request.args,
            )
        )

    form.populate_obj(refugee)
    # refugee.updated_by = current_user._get_current_object()
    refugee.save()

    return redirect(url_for("refugees.index"))


@module.route("/delete/<refugee_id>", methods=["POST"])
@login_required
def delete_refugee(refugee_id):
    print("Deleting refugee:", refugee_id)
    refugee = models.Refugee.objects(id=refugee_id).first()
    if refugee:
        refugee.status = "deactive"
        refugee.save()
    return redirect(url_for("refugees.index"))
