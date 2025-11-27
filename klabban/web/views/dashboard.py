import datetime

from flask import Blueprint, render_template, request
from flask_login import current_user, login_required
from mongoengine.queryset.queryset import QuerySet
from mongoengine.queryset.visitor import Q
from .. import models
from .. import forms
from ..utils.acl import roles_required
from ..utils.template_filters import format_thai_date

module = Blueprint("dashboard", __name__, url_prefix="/dashboard")


def get_refugee_age_stats(refugee_queryset):
    age_stats = []
    age_ranges = [(0, 5), (6, 12), (13, 17), (18, 59), (60, 200)]
    age_labels = ["0-5 ปี", "6-12 ปี", "13-17 ปี", "18-59 ปี", "60+ ปี"]
    for index, age_range in enumerate(age_ranges):
        count = refugee_queryset.filter(
            age__gte=age_range[0], age__lte=age_range[1]
        ).sum("people_count")
        age_stats.append({"label": age_labels[index], "count": count})

    # ไม่ทราบอายุ
    unknown_age_count = refugee_queryset.filter(age=None).sum("people_count")
    age_stats.append({"label": "ไม่ทราบอายุ", "count": unknown_age_count})
    return age_stats


def get_refugee_daily_stats(refugee_queryset: QuerySet):
    sorted_registration_dates = list(
        refugee_queryset.only("registration_date").order_by("registration_date")
    )
    if len(sorted_registration_dates) == 0:
        return []

    min_date = sorted_registration_dates[0].registration_date.date()
    max_date = sorted_registration_dates[-1].registration_date.date()

    stats = []
    oneday = datetime.timedelta(days=1)
    current_date = min_date

    while current_date <= max_date:
        current_date_min = datetime.datetime.combine(current_date, datetime.time.min)
        current_date_max = datetime.datetime.combine(current_date, datetime.time.max)
        qs = refugee_queryset.filter(
            Q(registration_date__gte=current_date_min)
            & Q(registration_date__lt=current_date_max)
        )
        count = qs.sum("people_count") if qs else 0
        stats.append({"label": f"วันที่ {format_thai_date(current_date)}", "count": count})
        current_date += oneday
    return stats


def get_refugee_country_stats(refugee_queryset):
    country_stats = []
    countries = refugee_queryset.distinct("country")
    unknown_count = 0

    for country in countries:
        count = refugee_queryset.filter(country=country).sum("people_count")
        if not country:  # This handles both None and empty string
            unknown_count += count
        else:
            country_stats.append({"label": country, "value": country, "count": count})

    if unknown_count > 0:
        country_stats.append(
            {"label": "ไม่ทราบประเทศ", "value": "", "count": unknown_count}
        )

    country_stats = sorted(country_stats, key=lambda x: x["count"], reverse=True)
    return country_stats


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


@module.route("/refugee-camp")
@login_required
@roles_required(["admin", "refugee_camp_staff"])
def refugee_camp_dashboard():
    form = forms.dashboard.RefugeeCampDashboardForm(request.args)
    if "admin" not in current_user.roles:
        # ถ้าไม่ได้เป็นแอดมิน ให้เลือกศูนย์พักพิงของตัวเองโดยอัตโนมัติ
        refugee_camp = current_user.refugee_camp
    else:
        refugee_camps = models.RefugeeCamp.objects(status__ne="deactive")
        form.refugee_camp.choices = [
            (str(camp.id), camp.name) for camp in refugee_camps
        ]
        if form.refugee_camp.data:
            refugee_camp = models.RefugeeCamp.objects.get(id=form.refugee_camp.data)
        else:
            refugee_camp = refugee_camps.first()
        form.refugee_camp.data = str(refugee_camp.id) if refugee_camp else None

    if not refugee_camp:
        return render_template(
            "dashboard/refugee_camp.html",
            form=form,
            total_refugees=0,
            active_refugees=0,
            returned_refugees=0,
            registrations_last_week=0,
            return_rate=0,
            recent_refugees=[],
            now=datetime.datetime.utcnow(),
            refugee_camp=None,
            age_stats=[],
            daily_stats=[],
            country_stats=[],
        )

    now = datetime.datetime.utcnow()
    seven_days_ago = now - datetime.timedelta(days=7)

    refugees = models.Refugee.objects(refugee_camp=refugee_camp, status__ne="deactive")

    total_refugees = refugees.sum("people_count")
    active_refugees = refugees.filter(status="active").sum("people_count")
    returned_refugees = refugees.filter(status="back_home").sum("people_count")

    recent_refugees = refugees.order_by("-registration_date").limit(5)
    registrations_last_week = refugees.filter(
        registration_date__gte=seven_days_ago
    ).sum("people_count")

    age_stats = get_refugee_age_stats(refugees)
    daily_stats = get_refugee_daily_stats(refugees)
    country_stats = get_refugee_country_stats(refugees)

    return render_template(
        "dashboard/refugee_camp.html",
        now=now,
        form=form,
        total_refugees=total_refugees,
        active_refugees=active_refugees,
        returned_refugees=returned_refugees,
        registrations_last_week=registrations_last_week,
        return_rate=((returned_refugees / total_refugees) if total_refugees else 0),
        recent_refugees=recent_refugees,
        refugee_camp=refugee_camp,
        age_stats=age_stats,
        daily_stats=daily_stats,
        country_stats=country_stats,
    )
