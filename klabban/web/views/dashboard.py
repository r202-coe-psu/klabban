import datetime

from flask import Blueprint, render_template
from flask_login import login_required

from .. import models
from ..utils.acl import roles_required

module = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@module.route("/admin")
@login_required
@roles_required(["admin"])
def admin_dashboard():
    now = datetime.datetime.utcnow()
    seven_days_ago = now - datetime.timedelta(days=7)

    total_refugees = models.Refugee.objects(status__ne="deactive").sum("people_count")
    active_refugees = models.Refugee.objects(status="active").sum("people_count")
    returned_refugees = models.Refugee.objects(status="back_home").sum("people_count")
    active_camps = models.RefugeeCamp.objects(status="active").count()

    recent_refugees = (
        models.Refugee.objects(status__ne="deactive")
        .order_by("-registration_date")
        .limit(5)
    )
    registrations_last_week = models.Refugee.objects(
        status__ne="deactive", registration_date__gte=seven_days_ago
    ).sum("people_count")

    camp_stats = []
    for camp in models.RefugeeCamp.objects(status="active").order_by("name"):
        camp_stats.append(
            {
                "id": camp.id,
                "name": camp.name,
                "refugee_count": models.Refugee.objects(
                    refugee_camp=camp.id, status__ne="deactive"
                ).sum("people_count"),
            }
        )

    return render_template(
        "dashboard/admin.html",
        total_refugees=total_refugees,
        active_refugees=active_refugees,
        returned_refugees=returned_refugees,
        active_camps=active_camps,
        registrations_last_week=registrations_last_week,
        return_rate=((returned_refugees / total_refugees) if total_refugees else 0),
        camp_stats=camp_stats,
        recent_refugees=recent_refugees,
        now=now,
    )
