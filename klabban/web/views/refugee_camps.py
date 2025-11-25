import datetime
import re
from urllib.parse import parse_qs, quote, unquote, urlparse
from uuid import uuid4

import pandas as pd
from flask import Blueprint, abort, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from mongoengine.queryset.visitor import Q

from klabban import models
from klabban.web import forms
from klabban.web.utils.acl import roles_required

module = Blueprint("refugee_camps", __name__, url_prefix="/refugee_camps")


@module.route("/")
def index():
    refugee_camps = models.RefugeeCamp.objects(status="active").order_by("name")
    return render_template("/refugee_camps/index.html", refugee_camps=refugee_camps)


@module.route("/<refugee_camp_id>")
def detail(refugee_camp_id):
    refugee_camp = models.RefugeeCamp.objects(id=refugee_camp_id).first()
    if not refugee_camp or refugee_camp.status == "deactive":
        abort(404)
    
    return render_template(
        "/refugee_camps/detail.html",
        refugee_camp=refugee_camp,
    )

@module.route("/create", methods=["GET", "POST"], defaults={"refugee_camp_id": None})
@module.route("/<refugee_camp_id>/edit", methods=["GET", "POST"])
@roles_required(["admin"])
def create_or_edit_refugee_camp(refugee_camp_id):
    form = forms.refugee_camps.RefugeeCampForm()
    refugee_camp = models.RefugeeCamp()
    modal_id = uuid4()

    if refugee_camp_id:
        refugee_camp = models.RefugeeCamp.objects.get(id=refugee_camp_id)
        form = forms.refugee_camps.RefugeeCampForm(obj=refugee_camp)
    # else:
    #   refugee_camp.created_by = current_user._get_current_object()

    if request.method == "GET":

        return render_template(
            "/components/refugee_camps/create_or_edit_modal.html",
            form=form,
            modal_id=modal_id,
            refugee_camp_id=refugee_camp_id,
        )

    if not form.validate_on_submit():
        return redirect(
            url_for(
                "refugee_camps.index",
                **request.args,
            )
        )

    form.populate_obj(refugee_camp)
    # refugee_camp.updated_by = current_user._get_current_object()
    refugee_camp.save()

    return redirect(url_for("refugee_camps.index"))


@module.route("/delete/<refugee_camp_id>", methods=["POST"])
@roles_required(["admin"])
def delete_refugee_camp(refugee_camp_id):
    refugee_camp = models.RefugeeCamp.objects(id=refugee_camp_id).first()
    if refugee_camp:
        refugee_camp.status = "deactive"
        refugee_camp.save()
    return redirect(url_for("refugee_camps.index"))
