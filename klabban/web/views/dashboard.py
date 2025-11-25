from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required
import datetime

module = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@module.route("/")
def index():

    return render_template("/dashboard/index.html")
