from flask_wtf import FlaskForm
from wtforms import (
    PasswordField,
    validators,
    StringField,
    SelectField,
    FormField,
    SelectMultipleField,
    TextAreaField,
    BooleanField,
)
from flask_mongoengine.wtf import model_form
from klabban.web import models
from klabban.models.users import USER_ROLES

BaseCreateUserForm = model_form(
    models.User,
    FlaskForm,
    field_args={
        "username": {"label": "ชื่อบัญชี (Username)"},
        "refugee_camp": {"label": "ศูนย์พักพิง", "label_attr": "name"},
        "first_name": {"label": "ชื่อจริง"},
        "last_name": {"label": "นามสกุล"},
    },
    exclude=[
        "roles",
        "status",
        "created_date",
        "updated_date",
        "last_login_date",
        "password",
    ],
)


class CreateUserForm(BaseCreateUserForm):
    password = PasswordField(
        "รหัสผ่าน",
        [validators.DataRequired(), validators.Length(min=6)],
        description="รหัสผ่านต้องมีความยาวอย่างน้อย 6 ตัวอักษร",
    )
    role = SelectField(
        "บทบาทผู้ใช้งาน",
        choices=USER_ROLES,
        coerce=str,
        validators=[validators.DataRequired()],
    )


class EditUserForm(BaseCreateUserForm):
    role = SelectField(
        "บทบาทผู้ใช้งาน",
        choices=USER_ROLES,
        coerce=str,
        validators=[validators.DataRequired()],
    )
    reset_password = PasswordField(
        "รีเซ็ตรหัสผ่าน",
        [validators.Optional(), validators.Length(min=6)],
        description="ระบุรหัสผ่านใหม่หากต้องการรีเซ็ตรหัสผ่าน (อย่างน้อย 6 ตัวอักษร)",
    )


class SearchCreateUserForm(FlaskForm):
    search = StringField(
        "ค้นหาผู้ใช้งาน",
        [validators.Optional(), validators.Length(min=0, max=64)],
        description="ค้นหาผู้ใช้งานโดยชื่อผู้ใช้งาน, ชื่อที่แสดง, บทบาท, สถานะ",
    )
