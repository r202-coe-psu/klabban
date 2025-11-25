from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required
import datetime

from .. import models

module = Blueprint("dashboard", __name__, url_prefix="/dashboard")


# @module.route("/")
# def index():
#     refugee_camps = models.RefugeeCamp.objects(status="active").order_by("created_at")
#     return render_template("/dashboard/index.html", refugee_camps=refugee_camps)
