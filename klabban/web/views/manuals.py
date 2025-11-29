from flask import Blueprint, render_template, redirect, url_for


module = Blueprint("manuals", __name__, url_prefix="/manuals")


@module.route("/")
def index():
    return render_template("manuals/index.html")
