import datetime
from datetime import timedelta

from flask import Blueprint, redirect, render_template, url_for
from flask_login import login_required

from klabban import models

from ..utils.acl import roles_required

module = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@module.route("/")
@roles_required(["admin"])
def index():
    # Total active refugees
    total_active_refugees = models.Refugee.objects(status="active").count()
    total_back_home = models.Refugee.objects(status="back_home").count()
    total_refugees = total_active_refugees + total_back_home
    
    # Refugees per camp
    camps = models.RefugeeCamp.objects(status="active").order_by("name")
    camps_with_counts = []
    for camp in camps:
        count = models.Refugee.objects(refugee_camp=camp.id, status__ne="deactive").count()
        camps_with_counts.append({
            "camp": camp,
            "count": count
        })
    
    # Recently registered (last 7 days)
    seven_days_ago = datetime.datetime.now() - timedelta(days=7)
    recently_registered = models.Refugee.objects(
        registration_date__gte=seven_days_ago,
        status__ne="deactive"
    ).count()
    
    # Total camps
    total_camps = camps.count()
    
    return render_template(
        "/dashboard/index.html",
        total_active_refugees=total_active_refugees,
        total_back_home=total_back_home,
        total_refugees=total_refugees,
        camps_with_counts=camps_with_counts,
        recently_registered=recently_registered,
        total_camps=total_camps,
    )
