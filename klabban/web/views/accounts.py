from flask import (
    Blueprint,
    render_template,
    url_for,
    request,
    session,
    redirect,
    Response,
    send_file,
    flash,
)
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

from .. import oauth2
from .. import forms
from klabban.web import models

module = Blueprint("accounts", __name__)


@module.route("/login", methods=["GET", "POST"])
def login():
    form = forms.accounts.LoginForm()
    if not form.validate_on_submit():
        error_msg = form.errors
        if form.errors == {"password": ["Field must be at least 6 characters long."]}:
            error_msg = "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"
        if form.errors == {"password": ["This field is required."]}:
            error_msg = "กรุณากรอกรหัสผ่าน"

        return render_template("/accounts/login.html", form=form, error_msg=error_msg)

    user = models.User.objects(username=form.username.data).first()
    if not user or not user.check_password(form.password.data):
        error_msg = "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"
        return render_template("/accounts/login.html", form=form, error_msg=error_msg)

    if user.status == "disactive":
        error_msg = "บัญชีของท่านถูกลบออกจากระบบ"
        return render_template("/accounts/login.html", form=form, error_msg=error_msg)

    login_user(user)
    user.last_login_date = datetime.datetime.now()
    user.save()
    next = request.args.get("next")
    if next:
        return redirect(next)

    return redirect(url_for("index.index"))


@module.route("/login/<name>")
def login_oauth(name):
    client = oauth2.oauth2_client

    scheme = request.environ.get("HTTP_X_FORWARDED_PROTO", "http")

    redirect_uri = url_for(
        "accounts.authorized_oauth", name=name, _external=True, _scheme=scheme
    )
    response = None
    if name == "google":
        response = client.google.authorize_redirect(redirect_uri)
    elif name == "facebook":
        response = client.facebook.authorize_redirect(redirect_uri)
    elif name == "line":
        response = client.line.authorize_redirect(redirect_uri)

    elif name == "psu":
        response = client.psu.authorize_redirect(redirect_uri)
    elif name == "engpsu":
        response = client.engpsu.authorize_redirect(redirect_uri)
    return response


@module.route("/auth/<name>")
def authorized_oauth(name):
    client = oauth2.oauth2_client
    remote = None
    try:
        if name == "google":
            remote = client.google
        elif name == "facebook":
            remote = client.facebook
        elif name == "line":
            remote = client.line
        elif name == "psu":
            remote = client.psu
        elif name == "engpsu":
            remote = client.engpsu

        token = remote.authorize_access_token()

    except Exception as e:
        print("autorize access error =>", e)
        return redirect(url_for("accounts.login"))

    session["oauth_provider"] = name
    return oauth2.handle_authorized_oauth2(remote, token)


@module.route("/logout", methods=["POST", "GET"])
@login_required
def logout():
    logout_user()
    return redirect("/")
