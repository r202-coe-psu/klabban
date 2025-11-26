import datetime

from flask import Blueprint, redirect, render_template, url_for
from flask_login import login_required

from klabban import models

module = Blueprint("index", __name__)


@module.route("/")
def index():
    refugee_camps = models.RefugeeCamp.objects(status="active").order_by("created_at")
    
    # Count refugees for each camp (only active refugees) and attach to camp object
    for camp in refugee_camps:
        camp.refugee_count = models.Refugee.objects(
            refugee_camp=camp.id,
            status__ne="deactive"
        ).count()
    
    return render_template("index/index.html", refugee_camps=refugee_camps)


@module.route("/robots.txt")
def robots_txt():
    return redirect(url_for("static", filename="robots.txt"))
