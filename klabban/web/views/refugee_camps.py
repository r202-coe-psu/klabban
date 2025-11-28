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
    else:
        refugee_camp.created_by = current_user._get_current_object()

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
    refugee_camp.updated_by = current_user._get_current_object()
    refugee_camp.updated_at = datetime.datetime.now()
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


@module.route("/download_template")
@roles_required(["admin", "refugee_camp_staff"])
def download_template():
    output = utils.import_refugee_excel.get_template()
    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name="ข้อมูลผู้อพยพ.xlsx",
    )


@module.route("/import_refugees", methods=["GET", "POST"])
@roles_required(["admin", "refugee_camp_staff"])
def import_refugee_modal():
    form = forms.refugee_camps.ImportRefugeeDataForm()
    modal_id = uuid4()

    refugee_camps = []
    if "refugee_camp_staff" in current_user.roles:
        if current_user.refugee_camp:
            refugee_camps = models.RefugeeCamp.objects(id=current_user.refugee_camp.id)
    if not refugee_camps:
        refugee_camps = models.RefugeeCamp.objects(status="active").order_by("name")

    form.refugee_camp.choices = [("all", "ทั้งหมด")] + [
        (str(rc.id), rc.name) for rc in refugee_camps
    ]
    print(form.refugee_camp.choices)
    # ดึง import logs
    import_logs = (
        models.ImportRefugeeFile.objects().order_by("-uploaded_date").limit(20)
    )

    if not form.validate_on_submit():
        return render_template(
            "/components/refugee_camps/import_refugee_modal.html",
            modal_id=modal_id,
            form=form,
            import_logs=import_logs,
        )

    refugee_camp = form.refugee_camp.data

    # ถ้าเลือกทั้งหมดในถ้าเป้น all จะส่ง string all ถ้าเลือกอย่างอื่น จะส่ง refugee_camp object
    if refugee_camp != "all":
        refugee_camp = models.RefugeeCamp.objects.get(id=ObjectId(refugee_camp))

    file = form.excel_file.data

    if file:
        import_refugee_file = models.ImportRefugeeFile(
            file_name=file.filename,
            source=form.source.data if form.source.data else None,
            created_by=current_user._get_current_object(),
            upload_status="pending",
        )
        file.seek(0)
        import_refugee_file.file.put(
            file,
            filename=file.filename,
            content_type=file.content_type,
        )
        import_refugee_file.save()

        job_id = redis_rq.redis_queue.queue.enqueue(
            utils.import_refugee_excel.process_import_refugee_file,
            args=(
                import_refugee_file,
                current_user._get_current_object(),
                refugee_camp,
            ),
            timeout=3600,
            job_timeout=1200,
        )

        flash("ระบบกำลังประมวลผลไฟล์ที่อัปโหลด กรุณารอสักครู่", "pending")
    else:
        flash("กรุณาเลือกไฟล์ที่จะอัปโหลด", "error")
    return redirect(url_for("refugees.index"))


@module.route("/import_logs/<log_id>/errors")
@roles_required(["admin", "refugee_camp_staff"])
def get_import_log_errors(log_id):
    try:
        import_log = models.ImportRefugeeFile.objects.get(id=log_id)
        return {"success": True, "errors": import_log.error_messages}
    except Exception as e:
        return {"success": False, "message": str(e)}
