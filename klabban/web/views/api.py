from flask import Blueprint
from flask_login import login_required

from klabban.web import models

module = Blueprint("apis", __name__, url_prefix="/apis")


@module.route("/master/countries", methods=["GET", "POST"])
def master_countries():
    countries = list(models.Refugee.objects(country__ne=None).distinct("country"))
    return {"countries": countries}
