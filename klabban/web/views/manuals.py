from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required
from ..utils.acl import roles_required


module = Blueprint("manuals", __name__, url_prefix="/manuals")


@module.route("/")
@roles_required(["admin", "refugee_camp_staff", "officer"])
def index():
    return render_template("manuals/index.html")
