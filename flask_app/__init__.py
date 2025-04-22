import os
from datetime import timedelta

from flask import Flask, g
from flask_security.core import Security
from flask_security.datastore import SQLAlchemySessionUserDatastore
from flask_security.utils import hash_password
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from .dash_apps.dash1 import app1
from .dash_apps.dash2 import app2
from .database import db_session, engine, init_db
from .models import Role, User

app = Flask(__name__)
app.config["DEBUG"] = True

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "5JVCn2hlBu04FU6KofbaQkGnL9geDwCE80-AaaGq1lY"
)
app.config["SECURITY_PASSWORD_SALT"] = os.environ.get(
    "SECURITY_PASSWORD_SALT", "237825570490125930873220258115310108673"
)
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)
app.config["SECURITY_LOGIN_USER_TEMPLATE"] = "login.html"

# manage sessions per request - make sure connections are closed and returned
app.teardown_appcontext(lambda exc: db_session.close())

user_datastore = SQLAlchemySessionUserDatastore(db_session, User, Role)
security = Security(app, user_datastore)

from .auth import auth

app.register_blueprint(auth)

from .main import main

app.register_blueprint(main)

with app.app_context():
    init_db()
    security.datastore.find_or_create_role(
        name="editor", permissions={"user-read", "user-write"}
    )
    security.datastore.find_or_create_role(name="reader", permissions={"user-read"})
    db_session.commit()
    if not security.datastore.find_user(username="editor"):
        security.datastore.create_user(
            email="editor",
            username="editor",
            password=hash_password("password"),
            roles=["editor"],
        )
    if not security.datastore.find_user(username="editor"):
        security.datastore.create_user(
            email="reader",
            username="reader",
            password=hash_password("password"),
            roles=["reader"],
        )
    db_session.commit()

    g.engine = engine
    dash_app = DispatcherMiddleware(
        app,
        {
            "/dash1": app1.init_app("/dash1/", app),
            "/dash2": app2.init_app("/dash2/", app),
        },
    )

if __name__ == "__main__":
    app.run(debug=True)
