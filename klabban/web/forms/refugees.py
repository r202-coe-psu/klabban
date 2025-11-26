from flask_wtf import FlaskForm
from flask_mongoengine.wtf import model_form
from klabban.web import models
from wtforms import StringField, SelectField

BaseRefugeeForm = model_form(
    models.Refugee,
    FlaskForm,
    field_args={
        "refugee_camp": {"label": "ศูนย์พักพิง / Refugee Camp", "label_attr": "name"},
        "nick_name": {"label": "ชื่อเล่น / Nickname"},
        "name": {"label": "ชื่อ-นามสกุล / Full Name"},
        "nationality": {"label": "สัญชาติ / Nationality", "default": "ไทย"},
        "ethnicity": {"label": "เชื้อชาติ / Ethnicity", "default": "ไทย"},
        "country": {"label": "ประเทศ / Country", "default": "ไทย"},
        "remark": {"label": "หมายเหตุ / Remark"},
        "status": {"label": "สถานะ / Status"},
        "address": {"label": "ที่อยู่ / Address"},
        "phone": {"label": "เบอร์โทรศัพท์ / Phone"},
    },
)


class RefugeeForm(BaseRefugeeForm):
    pass


class RefugeeSearchForm(FlaskForm):
    search = StringField(
        "ค้นหา / Search", render_kw={"placeholder": "ค้นหาชื่อผู้อพยพ / Search Refugee Name"}
    )
    refugee_camp = SelectField("ศูนย์พักพิง / Refugee Camp", choices=[])
