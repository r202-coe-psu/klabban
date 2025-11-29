from flask_wtf import FlaskForm
from flask_mongoengine.wtf import model_form
from wtforms import StringField, SelectField, DateTimeLocalField
from klabban.web import models
from wtforms.validators import DataRequired, Optional


BaseReportForm = model_form(
    models.Report,
    FlaskForm,
    field_args={
        "title": {"label": "หัวข้อ / Title"},
        "description": {"label": "รายละเอียด / Description"},
        "phone_number": {"label": "เบอร์โทรศัพท์ / Phone Number"},
        "report_type": {"label": "ประเภทการรายงาน / Report Type"},
    },
    exclude=[
        "status",
        "created_date",
        "ip_address",
        "staff",
        "report_status",
    ],
)


class ReportNoteForm(BaseReportForm):
    description = StringField(
        "รายละเอียดสำหรับแจ้งฝ่ายลงทะเบียน / Details for registration notification",
        validators=[DataRequired()],
    )
    
class ReportStaffNoteForm(FlaskForm):
    staff_note = StringField(
        "หมายเหตุจากเจ้าหน้าที่ / Staff Note",
    )

class ReportSearchForm(FlaskForm):
    search = StringField(
        "ค้นหา / Search",
    )
    report_type = SelectField(
        "ประเภทการรายงาน / Report Type",
        choices=[("", "ทั้งหมด / All")] + models.REPORT_TYPE_CHOICES,
    )
    
    report_status = SelectField(
        "สถานะการรายงาน / Report Status",
        choices=[("", "ทั้งหมด / All")] + models.REPORT_STATUS_CHOICES,
    )