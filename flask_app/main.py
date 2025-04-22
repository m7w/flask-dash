from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user
from flask_security.decorators import auth_required

main = Blueprint("main", __name__)

@main.route("/")
def home():
    return redirect(url_for("main.dashboards"))


@main.route("/dash")
@auth_required()
def dashboards():
    return render_template("dashboards.html")


@main.route("/profile")
@auth_required()
def profile():
    return render_template(
        "profile.html",
        name=current_user.username,
        last_login=current_user.last_login_at,
    )
