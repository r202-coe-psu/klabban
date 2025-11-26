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
        "nick_name": {"label": "ชื่อเล่น / Nickname"},
        "name": {"label": "ชื่อ-นามสกุล / Full Name"},
        "nationality": {"label": "สัญชาติ / Nationality", "default": "ไทย"},
        "ethnicity": {"label": "เชื้อชาติ / Ethnicity", "default": "ไทย"},
        "country": {"label": "ประเทศ / Country", "default": "ไทย"},
        "remark": {"label": "หมายเหตุ / Remark"},
        "status": {"label": "สถานะ / Status"},
        "address": {"label": "ที่อยู่ / Address"},
        "phone": {"label": "เบอร์โทรศัพท์ / Phone"},
        "age": {"label": "อายุ / Age"},
        "gender": {"label": "เพศ / Gender"},
        "people_count": {"label": "จำนวนคน / People Count"},
    },
    exclude=[
        "refugee_camp",
        "created_by",
        "updated_by",
        "created_date",
        "updated_date",
    ],
)


class RefugeeForm(BaseRefugeeForm):
    refugee_camp = SelectField("ศูนย์พักพิง / Refugee Camp", choices=[])
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
    refugee_camp = SelectField("ศูนย์พักพิง / Refugee Camp", choices=[])
