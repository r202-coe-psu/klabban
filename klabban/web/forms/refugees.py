from flask_wtf import FlaskForm
from flask_mongoengine.wtf import model_form
from klabban.web import models
from wtforms import StringField, SelectField

BaseRefugeeForm = model_form(
    models.Refugee,
    FlaskForm,
    field_args={
        "refugee_camp": {"label": "ศูนย์พักพิง", "label_attr": "name"},
        "nick_name": {"label": "ชื่อเล่น"},
        "name": {"label": "ชื่อ-นามสกุล"},
        "nationality": {"label": "สัญชาติ", "default": "ไทย"},
        "ethnicity": {"label": "เชื้อชาติ", "default": "ไทย"},
        "remark": {"label": "หมายเหตุ"},
        "status": {"label": "สถานะ"},
        "address": {"label": "ที่อยู่"},
        "phone": {"label": "เบอร์โทรศัพท์"},
    },
)


class RefugeeForm(BaseRefugeeForm):
    pass


class RefugeeSearchForm(FlaskForm):
    search = StringField("ค้นหา", render_kw={"placeholder": "ค้นหาชื่อผู้อพยพ"})
    refugee_camp = SelectField("ศูนย์พักพิง")
