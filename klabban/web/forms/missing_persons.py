from datetime import datetime
from flask_wtf import FlaskForm
from flask_mongoengine.wtf import model_form
from klabban.web import models
from wtforms import DateTimeLocalField, SelectField, FileField, StringField
from flask_wtf.file import FileAllowed, FileRequired

BaseMissingPersonForm = model_form(
    models.MissingPerson,
    FlaskForm,
    field_args={
        "title_name": {"label": "คำนำหน้าชื่อ"},
        "first_name": {"label": "ชื่อ"},
        "last_name": {"label": "นามสกุล"},
        "age": {"label": "อายุ"},
        "identification_number": {"label": "หมายเลขบัตรประชาชน"},
        "country": {"label": "ประเทศของ"},
        "province_info": {"label": "จังหวัดของ"},
        "district_info": {"label": "อําเภอของ"},
        "subdistrict_info": {"label": "ตําบลของ"},
        "address_info": {"label": "ที่อยู่บ้านเลขที่ของ"},
        "missing_person_status": {"label": "สถานะ"},
        "physical_mark": {"label": "ลักษณะรูปพรรณของ"},
        "statement": {"label": "สอบปากคําจากผู้แจ้ง/คําให้การ"},
        "body_received_date": {"label": "วันที่รับศพ"},
        "deceased_relationship": {"label": "ความสัมพันธ์กับผู้หาย/เสียชีวิต"},
        "reporter_title_name": {"label": "คำนำหน้าชื่อผู้แจ้ง"},
        "reporter_first_name": {"label": "ชื่อผู้แจ้ง"},
        "reporter_last_name": {"label": "นามสกุลผู้แจ้ง"},
        "reporter_age": {"label": "อายุผู้แจ้ง"},
        "reporter_identification_number": {"label": "หมายเลขบัตรประชาชนผู้แจ้ง"},
        "reporter_country": {"label": "ประเทศของผู้แจ้ง"},
        "reporter_province_info": {"label": "จังหวัดของผู้แจ้ง"},
        "reporter_district_info": {"label": "อําเภอของผู้แจ้ง"},
        "reporter_subdistrict_info": {"label": "ตําบลของผู้แจ้ง"},
        "reporter_address_info": {"label": "ที่อยู่บ้านเลขที่ของผู้แจ้ง"},
        "reporter_phone_number": {"label": "เบอร์โทรศัพท์ผู้แจ้ง"},
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
    title_name = SelectField("คำนำหน้าชื่อ", choices=[])
    country = SelectField("ประเทศของ", choices=[])
    reporter_country = SelectField("ประเทศของผู้แจ้ง", choices=[])
    body_received_date = DateTimeLocalField(
        "วันที่รับศพ",
        default=datetime.now,
        format="%Y-%m-%dT%H:%M",
        render_kw={"placeholder": "เลือกวันที่และเวลา / Select Date and Time"},
    )
    reporter_country = SelectField("ประเทศของผู้แจ้ง", choices=[])


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
