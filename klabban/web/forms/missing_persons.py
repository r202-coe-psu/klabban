from datetime import datetime
from flask_wtf import FlaskForm
from flask_mongoengine.wtf import model_form
from klabban.web import models
from wtforms import DateTimeLocalField, SelectField, FileField, StringField
from flask_wtf.file import FileAllowed, FileRequired
from klabban.models.missing_persons import MISSING_PERSON_STATUS_CHOICES

BaseMissingPersonForm = model_form(
    models.MissingPerson,
    FlaskForm,
    field_args={
        "title_name": {"label": "คำนำหน้าชื่อ"},
        "first_name": {"label": "ชื่อ"},
        "last_name": {"label": "นามสกุล"},
        "age": {"label": "อายุ"},
        "identification_number": {"label": "หมายเลขบัตรประชาชน"},
        "country": {"label": "ประเทศ"},
        "province_info": {"label": "จังหวัด"},
        "district_info": {"label": "อําเภอ"},
        "subdistrict_info": {"label": "ตําบล"},
        "address_info": {"label": "ที่อยู่บ้านเลขที่"},
        "missing_person_status": {"label": "สถานะ"},
        "physical_mark": {"label": "ลักษณะรูปพรรณ"},
        "statement": {"label": "สอบปากคําจากผู้แจ้ง/คําให้การ"},
        "body_received_date": {"label": "วันที่รับศพ"},
        "deceased_relationship": {"label": "ความสัมพันธ์กับผู้หาย/เสียชีวิต"},
        "reporter_title_name": {"label": "คำนำหน้าชื่อ"},
        "reporter_first_name": {"label": "ชื่อ"},
        "reporter_last_name": {"label": "นามสกุล"},
        "reporter_age": {"label": "อายุ"},
        "reporter_identification_number": {"label": "หมายเลขบัตรประชาชน"},
        "reporter_country": {"label": "ประเทศ"},
        "reporter_province_info": {"label": "จังหวัด"},
        "reporter_district_info": {"label": "อําเภอ"},
        "reporter_subdistrict_info": {"label": "ตําบล"},
        "reporter_address_info": {"label": "ที่อยู่บ้านเลขที่"},
        "reporter_phone_number": {"label": "เบอร์โทรศัพท์"},
        "code": {"label": "Code"},
    },
    exclude=[
        "created_by",
        "updated_by",
        "created_date",
        "updated_date",
        "status",
    ],
)


class MissingPersonForm(BaseMissingPersonForm):
    title_name = SelectField("คำนำหน้า", choices=[])
    missing_person_status = SelectField("สถานะ", choices=[])
    body_received_date = DateTimeLocalField(
        "วันที่รับศพ",
        default=datetime.now,
        format="%Y-%m-%dT%H:%M",
        render_kw={"placeholder": "เลือกวันที่และเวลา / Select Date and Time"},
    )


class MissingPersonImportForm(FlaskForm):
    file = FileField(
        "ไฟล์นำเข้าข้อมูล (.xlsx)",
        validators=[
            FileRequired(),
            FileAllowed(["xlsx"], "เฉพาะไฟล์ .xlsx เท่านั้น"),
        ],
    )
    source = StringField("แหล่งที่มา / Source", description="เช่น ชื่อองค์กรที่ส่งข้อมูลมา")


class MissingPersonSearchForm(FlaskForm):
    search = StringField(
        "ค้นหา / Search",
        render_kw={"placeholder": "ค้นหาจาก ชื่อ นามสกุล หรือ หมายเลขบัตรประชาชน"},
    )
    status = SelectField(
        "สถานะ",
        choices=[
            ("", "ทั้งหมด"),
            ("missing", "คนหาย"),
            ("death", "เสียชีวิต"),
        ],
    )
