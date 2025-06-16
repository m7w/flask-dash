from datetime import datetime

from flask import (
    Blueprint,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_user, logout_user

from . import security
from .database import db_session

auth = Blueprint("auth", __name__)

@auth.before_app_request
def require_login():
    if request.endpoint in ["auth.login"]:
        return

    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))


@auth.route("/mlogin", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        remember = True if request.form.get("remember") else False

        user = security.datastore.find_user(username=username)

        if not user or not user.verify_and_update_password(password):
            return render_template("login.html", error="Invalid username or password")

        login_user(user, remember=remember)
        user.last_login_at = user.current_login_at
        user.current_login_at = datetime.now()
        db_session.merge(user)
        db_session.commit()
        response = make_response(redirect(url_for("main.dashboards")))
        response.set_cookie("permissions", ",".join(user.get_permissions()))
        return response
    return render_template("login.html")


@auth.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))

