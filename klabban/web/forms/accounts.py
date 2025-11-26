from flask_wtf import FlaskForm
from wtforms import (
    PasswordField,
    validators,
    StringField,
    SelectField,
    SelectMultipleField,
)


class LoginForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[validators.InputRequired(), validators.Length(min=3, max=64)],
    )
    password = PasswordField(
        "Password", validators=[validators.InputRequired(), validators.Length(min=6)]
    )


class SetupPasswordForm(FlaskForm):
    password = PasswordField(
        "รหัสผ่าน", validators=[validators.InputRequired(), validators.Length(min=6)]
    )
    confirm_password = PasswordField(
        "ยืนยันรหัสผ่าน",
        validators=[
            validators.InputRequired(),
            validators.EqualTo("password", message="รหัสผ่านทั้งสองช่องไม่ตรงกัน"),
        ],
    )
