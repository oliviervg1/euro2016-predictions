from flask import Flask, request, session, jsonify, redirect, url_for
from flask_oauth2_login import GoogleLogin

from football_data_client import FootballDataApiClient

from models import db
from utils import get_config, is_user_logged_in, is_valid_email_domain, \
    add_user, set_predictions, populate_teams_table

config = get_config("./config/config.cfg")

app = Flask(__name__)
app.config.update(
    SECRET_KEY=config.get("flask", "secret_key"),
    GOOGLE_LOGIN_REDIRECT_SCHEME=config.get("google_login", "redirect_scheme"),
    GOOGLE_LOGIN_CLIENT_ID=config.get("google_login", "client_id"),
    GOOGLE_LOGIN_CLIENT_SECRET=config.get("google_login", "client_secret"),
    SQLALCHEMY_DATABASE_URI=config.get("db", "sqlalchemy_db_url")
)

google_login = GoogleLogin(app)
db.init_app(app)

football_api_client = FootballDataApiClient(424)


@app.route("/status")
def status():
    return jsonify(response="OK")


@app.route("/")
def index():
    is_logged_in, user = is_user_logged_in(session)
    if not is_logged_in:
        return redirect(google_login.authorization_url())
    return jsonify(
        id=user.id,
        name=user.name,
        email=user.email,
        allocated_team=str(user.allocated_team),
        predictions=[str(p) for p in user.predictions]
    )


@app.route("/submit", methods=["POST"])
def submit():
    is_logged_in, user = is_user_logged_in(session)
    if not is_logged_in:
        return redirect(google_login.authorization_url())
    set_predictions(user, request.form)
    return redirect(url_for("index"))


@google_login.login_success
def login_success(token, profile):
    if not is_valid_email_domain(profile["email"]):
        return jsonify(error="Please use a Cloudreach email address!")
    add_user(session, token, profile)
    return redirect(url_for("index"))


@google_login.login_failure
def login_failure(e):
    return jsonify(error=str(e))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        populate_teams_table(football_api_client.get_all_teams())
    app.run(port=8000, debug=True)
