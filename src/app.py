from dateutil.parser import parse as parse_date

from flask import Flask, request, flash, session, jsonify, redirect, url_for, \
    render_template
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
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SQLALCHEMY_DATABASE_URI=config.get("db", "sqlalchemy_db_url")
)

google_login = GoogleLogin(app)
db.init_app(app)

football_api_client = FootballDataApiClient(
    config.get("football_data", "api_key"), 424
)


@app.template_filter("strftime")
def filter_datetime(date_time):
    date_time_object = parse_date(date_time)
    return date_time_object.strftime("%a %d %B %Y - %H:%M UTC")


@app.errorhandler(Exception)
def error(error):
    return jsonify(error=str(error)), 500


@app.route("/status")
def status():
    return jsonify(response="OK")


@app.route("/")
def index():
    return jsonify(response="OK")


@app.route("/my-predictions")
def my_predictions():
    is_logged_in, user = is_user_logged_in(session)
    if not is_logged_in:
        return redirect(google_login.authorization_url())
    fixtures = football_api_client.get_all_fixtures()
    return render_template(
        "my-predictions.html", user=user.to_json(), fixtures=fixtures
    )


@app.route("/submit", methods=["POST"])
def submit():
    is_logged_in, user = is_user_logged_in(session)
    if not is_logged_in:
        return redirect(google_login.authorization_url())
    set_predictions(user, request.form)
    flash("Your predictions were successfully saved!")
    return redirect(url_for("my-predictions"))


@google_login.login_success
def login_success(token, profile):
    whitelisted_domains = config.get("google_login", "whitelisted_domains")
    if not is_valid_email_domain(profile["hd"], whitelisted_domains):
        return jsonify(error="Please use a valid email address!")
    add_user(session, token, profile)
    return redirect(url_for("my-predictions"))


@google_login.login_failure
def login_failure(error):
    return error(error)


if __name__ == "__main__":
    google_login.redirect_scheme = "http"
    with app.app_context():
        db.create_all()
        populate_teams_table(football_api_client.get_all_teams())
    app.run(port=8000, debug=True)
