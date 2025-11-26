from flask import Blueprint

from klabban.web import models

module = Blueprint("api", __name__)


@module.route("/master/countries", methods=["GET", "POST"])
def master_countries():
    countries = list(set(models.Refugee.objects.distinct("country")))
    countries.sort()
    return {"countries": countries}
