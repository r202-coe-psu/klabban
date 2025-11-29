from flask_wtf import FlaskForm
from flask_mongoengine.wtf import model_form
from klabban.web import models
from wtforms import SelectField, FileField, StringField
from flask_wtf.file import FileAllowed, FileRequired


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


class ExportRefugeeDataForm(FlaskForm):
    refugee_camp_export = SelectField("เลือกศูนย์พักพิง / Migrant Camp", choices=[])


class ImportRefugeeDataForm(FlaskForm):
    excel_file = FileField(
        "อัปโหลดไฟล์",
        validators=[
            FileRequired(),
            FileAllowed(["xlsx", "csv"], "ไฟล์ที่อนุญาต: excel, csv"),
        ],
        description="หมายเหตุ: ช่อง วันที่ ใช้เป็นรูปแบบ ปปปป-ดด-วว ชช:นน:วว",
    )
    refugee_camp = SelectField("เลือกศูนย์พักพิง / Migrant Camp", choices=[])
    source = StringField("แหล่งที่มา / Source", description="เช่น ชื่อองค์กรที่ส่งข้อมูลมา")
