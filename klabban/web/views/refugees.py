from flask import abort, Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from ..utils.acl import roles_required
from klabban import models
from klabban.web import forms
from mongoengine.queryset.visitor import Q
from uuid import uuid4
from flask_mongoengine import Pagination


module = Blueprint("refugees", __name__, url_prefix="/refugees")


@module.route("/")
def index():
    page = request.args.get("page", 1, type=int)
    per_page = 50  # จำนวนรายการต่อหน้า

    search_form = forms.refugees.RefugeeSearchForm(request.args)
    search_form.refugee_camp.choices = [("", "ทั้งหมด")] + [
        (str(camp.id), camp.name)
        for camp in models.RefugeeCamp.objects(status__ne="deactive").order_by("name")
    ]
    search = search_form.search.data
    refugee_camp_id = search_form.refugee_camp.data

    query = models.Refugee.objects(status__ne="deactive").order_by("name")
    
    if search:
        query = query.filter(
            Q(name__icontains=search) | Q(nick_name__icontains=search)
        )
    if refugee_camp_id:
        query = query.filter(refugee_camp=refugee_camp_id)
    try:
        refugees_pagination = Pagination(query, page=page, per_page=per_page)
    except ValueError:
        refugees_pagination = Pagination(query, page=1, per_page=per_page)

    return render_template(
        "/refugees/index.html", 
        refugees_pagination=refugees_pagination,
        search_form=search_form,
    )


@module.route("/create", methods=["GET", "POST"], defaults={"refugee_id": None})
@module.route("/<refugee_id>/edit", methods=["GET", "POST"])
@roles_required(["admin", "refugee_camp_staff"])
def create_or_edit(refugee_id):
    form = forms.refugees.RefugeeForm()
    refugee = models.Refugee()

    if "admin" in current_user.roles:
        form.refugee_camp.choices = [
            (str(camp.id), camp.name)
            for camp in models.RefugeeCamp.objects(status__ne="deactive").order_by(
                "name"
            )
        ]
    elif "refugee_camp_staff" in current_user.roles:
        form.refugee_camp.choices = [
            (str(current_user.refugee_camp.id), current_user.refugee_camp.name)
        ]
        form.refugee_camp.data = str(current_user.refugee_camp.id)
    else:
        form.refugee_camp.choices = []

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
