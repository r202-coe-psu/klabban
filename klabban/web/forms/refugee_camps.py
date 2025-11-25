from flask_wtf import FlaskForm
from flask_mongoengine.wtf import model_form
from klabban.web import models

BaseRefugeeCampForm = model_form(
    models.RefugeeCamp,
    FlaskForm,
    field_args={
        "name": {"label": "ชื่อศูนย์พักพิง"},
        "location_url": {"label": "ลิงก์ที่ตั้ง (Google Maps)"},
        "contact_info": {"label": "ข้อมูลติดต่อ"},
        "line_id": {"label": "Line ID"},
        "other_link": {"label": "ลิงก์อื่น ๆ"},
        "description": {"label": "รายละเอียด"},
    },
)


class RefugeeCampForm(BaseRefugeeCampForm):
    pass
