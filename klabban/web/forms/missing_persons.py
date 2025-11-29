from flask_wtf import FlaskForm
from flask_mongoengine.wtf import model_form
from klabban.web import models
from wtforms import SelectField, FileField, StringField
from flask_wtf.file import FileAllowed, FileRequired

BaseMissingPersonForm = model_form(
    models.MissingPerson,
    FlaskForm,
    field_args={
        "title_name": {"label": "คำนำหน้าชื่อคนหาย/เสียชีวิต"},
        "first_name": {"label": "ชื่อคนหาย/เสียชีวิต"},
        "last_name": {"label": "นามสกุลคนหาย/เสียชีวิต"},
        "age": {"label": "อายุคนหาย/เสียชีวิต"},
        "identification_number": {"label": "หมายเลขบัตรประชาชน"},
        "country": {"label": "ประเทศของคนหาย/เสียชีวิต"},
        "province_info": {"label": "จังหวัดของคนหาย/เสียชีวิต"},
        "district_info": {"label": "อําเภอของคนหาย/เสียชีวิต"},
        "subdistrict_info": {"label": "ตําบลของคนหาย/เสียชีวิต"},
        "address_info": {"label": "ที่อยู่บ้านเลขที่ของคนหาย/เสียชีวิต"},
        "missing_person_status": {"label": "สถานะคนหาย/เสียชีวิต"},
        "physical_mark": {"label": "ลักษณะรูปพรรณของคนหาย/เสียชีวิต"},
        "statement": {"label": "สอบปากคําจากผู้แจ้ง/คําให้การ"},
        "body_received_date": {"label": "วันที่รับศพ"},
        "deceased_relationship": {"label": "ความสัมพันธ์กับผู้หาย/เสียชีวิต"},
        "reporter_title_name": {"label": "คำนำหน้าชื่อผู้แจ้ง"},
        "reporter_first_name": {"label": "ชื่อผู้แจ้ง"},
        "reporter_last_name": {"label": "นามสกุลผู้แจ้ง"},
        "reporter_age": {"label": "อายุผู้แจ้ง"},
        "reporter_identification_number": {"label": "หมายเลขบัตรประชาชนผู้แจ้ง"},
        "reporter_country": {"label": "ประเทศของผู้แจ้ง"},
        "reporter_proince_info": {"label": "จังหวัดของผู้แจ้ง"},
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
    pass


class MissingPersonImportForm(FlaskForm):
    file = FileField(
        "ไฟล์นำเข้าข้อมูลคนหาย/เสียชีวิต (.xlsx)",
        validators=[
            FileRequired(),
            FileAllowed(["xlsx"], "เฉพาะไฟล์ .xlsx เท่านั้น"),
        ],
    )


class MissingPersonSearchForm(FlaskForm):
    search = StringField(
        "ค้นหา / Search",
        render_kw={"placeholder": "ค้นหาจาก ชื่อ นามสกุล หรือ หมายเลขบัตรประชาชน"},
    )
    status = SelectField(
        "สถานะคนหาย/เสียชีวิต",
        choices=[
            ("", "ทั้งหมด"),
            ("missing", "คนหาย"),
            ("death", "เสียชีวิต"),
        ],
    )
