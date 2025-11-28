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

module = Blueprint("refugee_camps", __name__, url_prefix="/refugee_camps")


@module.route("/")
def index():
    refugee_camps = models.RefugeeCamp.objects(status="active").order_by("name")
    return render_template("/refugee_camps/index.html", refugee_camps=refugee_camps)


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
        refugee_camp_image = refugee_camp.image
    else:
        refugee_camp.created_by = current_user._get_current_object()
        refugee_camp_image = None

    if request.method == "GET":
        return render_template(
            "/components/refugee_camps/create_or_edit_modal.html",
            form=form,
            modal_id=modal_id,
            refugee_camp_id=refugee_camp_id,
            refugee_camp_image=refugee_camp_image,
        )

    if not form.validate_on_submit():
        return redirect(
            url_for(
                "refugee_camps.index",
                **request.args,
            )
        )

    form.populate_obj(refugee_camp)
    refugee_camp.updated_by = current_user._get_current_object()
    refugee_camp.updated_at = datetime.datetime.now()
    refugee_camp.save()

    if form.image_file.data:
        storage = form.image_file.data
        storage.seek(0, 2)
        filesize = storage.tell() / 1000
        storage.seek(0)

        file_doc = models.File(
            title=storage.filename,
            mimetype=storage.content_type,
            uploaded_by=current_user._get_current_object(),
            uploaded_date=datetime.datetime.now(),
            filesize=filesize,
            owner=current_user._get_current_object(),
        )
        print(file_doc.refugee_camp)
        file_doc.file.put(
            storage,
            content_type=storage.content_type,
            filename=storage.filename,
        )
        file_doc.save()

        refugee_camp.image = file_doc
        refugee_camp.save()
    return redirect(url_for("refugee_camps.index"))


@module.route("/delete/<refugee_camp_id>", methods=["POST"])
@roles_required(["admin"])
def delete_refugee_camp(refugee_camp_id):
    refugee_camp = models.RefugeeCamp.objects(id=refugee_camp_id).first()
    if refugee_camp:
        refugee_camp.status = "deactive"
        refugee_camp.updated_by = current_user._get_current_object()
        refugee_camp.updated_at = datetime.datetime.now()
        refugee_camp.save()
    return redirect(url_for("refugee_camps.index"))


@module.route("/export/<refugee_camp_id>")
@roles_required(["admin", "refugee_camp_staff"])
def export_refugee_data(refugee_camp_id):
    job_id = redis_rq.redis_queue.queue.enqueue(
        utils.export_refugees.process_refugee_export,
        args=(refugee_camp_id, current_user._get_current_object()),
        timeout=3600,
        job_timeout=1200,
    )
    flash("ระบบกำลังประมวลผลไฟล์ที่อัปโหลด กรุณารอสักครู่", "pending")
    return redirect(url_for("refugees.index"))


@module.route("/export_refugee_modal")
@roles_required(["admin", "refugee_camp_staff"])
def export_refugee_modal():
    modal_id = uuid4()
    form = forms.refugee_camps.ExportRefugeeDataForm()
    refugee_camps = []

    if "refugee_camp_staff" in current_user.roles:
        if current_user.refugee_camp:
            refugee_camps = models.RefugeeCamp.objects(id=current_user.refugee_camp.id)
    if not refugee_camps:
        refugee_camps = models.RefugeeCamp.objects(status="active").order_by("name")

    form.refugee_camp_export.choices = [(str(rc.id), rc.name) for rc in refugee_camps]
    all_exported_files = []
    if "refugee_camp_staff" in current_user.roles:
        all_exported_files = models.ExportRefugeeFile.objects(
            refugee_camp=current_user.refugee_camp
        ).order_by("-created_date")
    elif "admin" in current_user.roles:
        all_exported_files = models.ExportRefugeeFile.objects().order_by(
            "-created_date"
        )
    return render_template(
        "/components/refugee_camps/export_refugee_modal.html",
        modal_id=modal_id,
        form=form,
        all_exported_files=all_exported_files,
    )


@module.route("/download_exported_file/<refugee_camp_id>")
@roles_required(["admin", "refugee_camp_staff"])
def download_exported_file(refugee_camp_id):
    refugee_camp = models.RefugeeCamp.objects.get(id=refugee_camp_id)
    export_refugee_file = models.ExportRefugeeFile.objects(
        refugee_camp=refugee_camp
    ).first()
    if not export_refugee_file or not export_refugee_file.file:
        flash("ไม่พบไฟล์ที่ส่งออก กรุณาทำการส่งออกข้อมูลใหม่", "error")
        return redirect(url_for("refugees.index"))

    return send_file(
        export_refugee_file.file,
        as_attachment=True,
        download_name=f"refugee_data_{refugee_camp.name}.xlsx",
    )


@module.route("/file/<file_id>")
def serve_file(file_id):
    file_doc = models.File.objects.get(id=file_id)
    return send_file(file_doc.file, mimetype=file_doc.mimetype)
