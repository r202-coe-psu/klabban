from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required
import datetime


module = Blueprint("index", __name__)


@module.route("/")
def index():

    return redirect(url_for("dashboard.index"))
