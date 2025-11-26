from flask import Blueprint

from klabban.web import models

module = Blueprint("api", __name__)


@module.route("/master/countries", methods=["GET", "POST"])
def master_countries():
    countries = list(models.Refugee.objects(country__ne=None).distinct("country"))
    return {"countries": countries}
