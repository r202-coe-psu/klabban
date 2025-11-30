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
from klabban.models.missing_persons import (
    TITLE_NAME_CHOICES,
    MISSING_PERSON_STATUS_CHOICES,
)
from bson import ObjectId

module = Blueprint("missing_persons", __name__, url_prefix="/missing_persons")


@module.route("/")
@login_required
@roles_required(["officer"])
def index():
    view_mode = request.args.get("view_mode", "list")

    page = request.args.get("page", 1, type=int)
    per_page = 50  # จำนวนรายการต่อหน้า
    search_form = forms.missing_persons.MissingPersonSearchForm(request.args)

    search = search_form.search.data
    status = search_form.status.data

    query = models.MissingPerson.objects(status__ne="inactive")

    if search:
        query = query.filter(
            Q(title_name__icontains=search)
            | Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(identification_number__icontains=search)
        )
    if status:
        query = query.filter(missing_person_status=status)

    try:
        missing_persons_pagination = Pagination(query, page=page, per_page=per_page)
    except ValueError:
        missing_persons_pagination = Pagination(query, page=1, per_page=per_page)

    total_missing = query.count()
    total_death = query.filter(missing_person_status="death").count()

    return render_template(
        "/missing_persons/index.html",
        missing_persons_pagination=missing_persons_pagination,
        search_form=search_form,
        view_mode=view_mode,
        total_missing=total_missing,
        total_death=total_death,
    )


@module.route("/create", methods=["GET", "POST"], defaults={"missing_person_id": None})
@module.route("/<missing_person_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required(["officer"])
def create_or_edit(missing_person_id=None):
    form = forms.missing_persons.MissingPersonForm()
    missing_person = models.MissingPerson()

    if missing_person_id:
        missing_person = models.MissingPerson.objects.get(id=missing_person_id)
        form = forms.missing_persons.MissingPersonForm(obj=missing_person)

    form.title_name.choices = TITLE_NAME_CHOICES
    form.reporter_title_name.choices = TITLE_NAME_CHOICES
    form.missing_person_status.choices = MISSING_PERSON_STATUS_CHOICES

    if not form.validate_on_submit() or request.method == "GET":
        return render_template(
            "/missing_persons/create_or_edit.html",
            form=form,
            missing_person=missing_person,
        )

    form.populate_obj(missing_person)
    missing_person.updated_date = datetime.datetime.now()
    missing_person.updated_by = current_user._get_current_object()
    if not missing_person_id:
        missing_person.created_date = datetime.datetime.now()
        missing_person.created_by = current_user._get_current_object()

    missing_person.save()

    flash("บันทึกข้อมูลบุคคลสูญหายเรียบร้อยแล้ว", "success")
    return redirect(url_for("missing_persons.index"))


@module.route("/<missing_person_id>/view", methods=["GET"])
@login_required
@roles_required(["officer"])
def view(missing_person_id):
    missing_person = models.MissingPerson.objects.get(id=missing_person_id)
    return render_template("/missing_persons/view.html", missing_person=missing_person)


@module.route("/<missing_person_id>/delete", methods=["POST"])
@login_required
@roles_required(["officer"])
def delete(missing_person_id):
    missing_person = models.MissingPerson.objects.get(id=missing_person_id)
    missing_person.status = "inactive"
    missing_person.updated_date = datetime.datetime.now()
    missing_person.updater = current_user._get_current_object()
    missing_person.save()

    flash("ลบข้อมูลบุคคลสูญหายเรียบร้อยแล้ว", "success")
    return redirect(url_for("missing_persons.index"))


@module.route("/import_missing_persons", methods=["GET", "POST"])
@roles_required(["officer"])
def import_missing_person_modal():
    form = forms.missing_persons.MissingPersonImportForm()
    modal_id = uuid4()

    # ดึง import logs
    import_logs = (
        models.ImportMissingPersonFile.objects().order_by("-uploaded_date").limit(20)
    )

    if not form.validate_on_submit():
        return render_template(
            "/components/missing_person/import_missing_person_modal.html",
            modal_id=modal_id,
            form=form,
            import_logs=import_logs,
        )

    file = form.file.data

    if file:
        import_missing_person_file = models.ImportMissingPersonFile(
            file_name=file.filename,
            source=form.source.data if form.source.data else None,
            created_by=current_user._get_current_object(),
            upload_status="pending",
        )
        file.seek(0)
        import_missing_person_file.file.put(
            file,
            filename=file.filename,
            content_type=file.content_type,
        )
        import_missing_person_file.save()

        redis_rq.redis_queue.queue.enqueue(
            utils.missing_person_excel.process_import_missing_person_file,
            args=(
                import_missing_person_file,
                current_user._get_current_object(),
                form.source.data if form.source.data else "",
            ),
            timeout=3600,
            job_timeout=1200,
        )

        flash("ระบบกำลังประมวลผลไฟล์ที่อัปโหลด กรุณารอสักครู่", "info")
    else:
        flash("กรุณาเลือกไฟล์ที่จะอัปโหลด", "error")

    return redirect(url_for("missing_persons.index"))


@module.route("/download_template")
@roles_required(["officer"])
def download_template():
    output = utils.missing_person_excel.get_template()
    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name="ข้อมูลผู้สูญหาย-เสียชีวิต.xlsx",
    )


@module.route("/import_logs/<import_id>/errors")
@roles_required(["officer"])
def get_import_errors(import_id):
    try:
        import_log = models.ImportMissingPersonFile.objects.get(id=import_id)
        return {
            "errors": import_log.error_messages,
            "file_name": import_log.file_name,
            "status": import_log.upload_status,
        }
    except Exception as e:
        return {"errors": [str(e)]}, 404


@module.route("/export")
@roles_required(["officer"])
def export_missing_person_data():
    job_id = redis_rq.redis_queue.queue.enqueue(
        utils.missing_person_excel.process_missing_person_export,
        args=(current_user._get_current_object(),),
        timeout=3600,
        job_timeout=1200,
    )
    flash("ระบบกำลังสร้างไฟล์ส่งออกข้อมูลบุคคลสูญหาย กรุณารอสักครู่", "info")
    return redirect(url_for("missing_persons.index"))


@module.route("/export_missing_person_modal")
@roles_required(["officer"])
def export_missing_person_modal():
    modal_id = uuid4()
    exported_file = models.ExportMissingPersonFile.objects(
        created_by=current_user._get_current_object()
    ).first()
    return render_template(
        "/components/missing_person/export_missing_person_modal.html",
        modal_id=modal_id,
        exported_file=exported_file,
    )


@module.route("/download_exported_missing_person_file/<export_id>")
@roles_required(["officer"])
def download_exported_file(export_id):
    export_missing_person_file = models.ExportMissingPersonFile.objects.get(
        id=export_id
    )
    if not export_missing_person_file or not export_missing_person_file.file:
        flash("ไม่พบไฟล์ที่ส่งออก กรุณาทำการส่งออกข้อมูลใหม่", "error")
        return redirect(url_for("missing_persons.index"))

    return send_file(
        export_missing_person_file.file,
        as_attachment=True,
        download_name=f"{export_missing_person_file.file_name}",
    )
