from flask_wtf import FlaskForm
from flask_mongoengine.wtf import model_form
from klabban.web import models
from wtforms import StringField, SelectField, DateTimeLocalField
from datetime import datetime
from wtforms.validators import DataRequired, Optional


class RefugeeCampDashboardForm(FlaskForm):
    refugee_camp = SelectField("เลือกศูนย์พักพิง / Migrant Camp", choices=[])
