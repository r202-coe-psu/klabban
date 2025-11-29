from flask_wtf import FlaskForm
from flask_mongoengine.wtf import model_form
from klabban.web import models
from wtforms import StringField, SelectField, DateTimeLocalField
from datetime import datetime
from wtforms.validators import DataRequired, Optional

BaseRefugeeForm = model_form(
    models.Refugee,
    FlaskForm,
    field_args={
        "nick_name": {"label": "ชื่อเล่น / Migrant Nickname"},
        "name": {"label": "ชื่อ-นามสกุล / Migrant Full Name"},
        "identification_number": {"label": "หมายเลขบัตรประชาชน / Identification Number"},
        "nationality": {"label": "สัญชาติ / Nationality", "default": "ไทย"},
        "ethnicity": {"label": "เชื้อชาติ / Ethnicity", "default": "ไทย"},
        "country": {"label": "ประเทศ / Country", "default": "Thailand"},
        "remark": {"label": "หมายเหตุ / Remark"},
        "status": {"label": "สถานะ / Status"},
        "address": {"label": "ที่อยู่ / Address"},
        "phone": {"label": "เบอร์โทรศัพท์ / Phone"},
        "age": {"label": "อายุ / Age"},
        "gender": {"label": "เพศ / Gender"},
        "congenital_disease": {"label": "โรคประจำตัว / Congenital Disease"},
        "people_count": {"label": "จำนวนคน / People Count"},
        "pets": {"label": "สัตว์เลี้ยง / Pets"},
        "expected_days": {"label": "จำนวนวันที่คาดว่าจะพัก / Expected Days"},
        "emergency_contact": {"label": "กรณีติดต่อฉุกเฉิน / Emergency Contact"},
        "description": {
            "label": "รายละเอียดสำหรับแจ้งฝ่ายลงทะเบียน / Details for registration notification"
        },
    },
    exclude=[
        "status_log",
        "refugee_camp",
        "created_by",
        "updated_by",
        "created_date",
        "updated_date",
        "camps_log",
    ],
)


class RefugeeForm(BaseRefugeeForm):
    refugee_camp = SelectField("ศูนย์พักพิง / Migrant Camp", choices=[])
    registration_date = DateTimeLocalField(
        "วันที่ลงทะเบียน / Registration Date",
        default=datetime.now,
        format="%Y-%m-%dT%H:%M",
        render_kw={"placeholder": "เลือกวันที่และเวลา / Select Date and Time"},
        validators=[DataRequired()],
    )
    back_home_date = DateTimeLocalField(
        "วันที่กลับบ้าน / Back Home Date",
        format="%Y-%m-%dT%H:%M",
        render_kw={"placeholder": "เลือกวันที่และเวลา / Select Date and Time"},
        validators=[Optional()],
    )


class RefugeeSearchForm(FlaskForm):
    search = StringField(
        "ค้นหา / Search", render_kw={"placeholder": "ค้นหาชื่อผู้อพยพ / Search Migrant Name"}
    )
    country = StringField("ประเทศ / Country")
    refugee_camp = SelectField("ศูนย์พักพิง / Migrant Camp", choices=[])
    status = SelectField(
        "สถานะ / Status",
        choices=[
            ("", "ทั้งหมด / All"),
            ("active", "อยู่ในศูนย์พักพิง / In Camp"),
            ("back_home", "กลับบ้านแล้ว / Back Home"),
        ],
    )


class ChangeRefugeeCampForm(FlaskForm):
    refugee_camp = SelectField(
        "ศูนย์พักพิงใหม่ / New Migrant Camp", choices=[], validators=[DataRequired()]
    )


class RefugeeNoteForm(FlaskForm):
    description = StringField(
        "รายละเอียดสำหรับแจ้งฝ่ายลงทะเบียน / Details for registration notification",
        validators=[DataRequired()],
    )

    staff_note = StringField(
        "รายละเอียดจากเจ้าหน้าที่ / Details from the staff",
    )
