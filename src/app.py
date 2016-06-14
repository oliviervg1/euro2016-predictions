from dateutil.parser import parse as parse_date

from flask import Flask, request, flash, session, jsonify, redirect, url_for, \
    render_template
from flask_oauth2_login import GoogleLogin

from football_data_client import FootballDataApiClient

from models import db
from utils import get_config, is_user_logged_in, is_valid_email_domain, \
    add_user, set_predictions, populate_teams_table, get_user_count, \
    get_team_allocations, get_predictions_leaderboard, get_user_information, \
    has_euros_started, get_points_for_user

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
    is_logged_in, user = is_user_logged_in(session)
    if is_logged_in:
        return redirect(url_for("my_predictions"))
    if session.get("seen"):
        return redirect(google_login.authorization_url())
    user_count = get_user_count()
    return render_template(
        "index.html",
        google_login_url=google_login.authorization_url(),
        user_count=user_count
    )


@app.route("/my-predictions")
def my_predictions():
    is_logged_in, user = is_user_logged_in(session)
    if not is_logged_in:
        return redirect(url_for("index"))
    user_info = user.to_json()
    return render_template(
        "my-predictions.html",
        user=user_info,
        fixtures=football_api_client.get_all_fixtures(),
        points=get_points_for_user(user_info["predictions"]),
        editable=not has_euros_started()
    )


@app.route("/submit", methods=["POST"])
def submit():
    is_logged_in, user = is_user_logged_in(session)
    if not is_logged_in:
        return redirect(url_for("index"))
    # Has the Euro tournament started?
    if not has_euros_started():
        set_predictions(user, request.form)
        flash("Your predictions were successfully saved!", "info")
    else:
        flash(
            "The Euros has started! You are no longer allowed to change your "
            "predictions...",
            "danger"
        )
    return redirect(url_for("my_predictions"))


@app.route("/user/<int:user_id>")
def user(user_id):
    is_logged_in, user = is_user_logged_in(session)
    if not is_logged_in:
        return redirect(url_for("index"))
    return render_template(
        "my-predictions.html",
        user=user.to_json(),
        fixtures=football_api_client.get_all_fixtures(),
        other_user=get_user_information(user_id).to_json(),
        editable=False
    )


@app.route("/sweepstakes")
def sweepstakes():
    is_logged_in, user = is_user_logged_in(session)
    if not is_logged_in:
        return redirect(url_for("index"))
    return render_template(
        "sweepstakes.html",
        user=user.to_json(),
        allocations=get_team_allocations()
    )


@app.route("/predictions")
def predictions():
    is_logged_in, user = is_user_logged_in(session)
    if not is_logged_in:
        return redirect(url_for("index"))
    return render_template(
        "predictions.html",
        user=user.to_json(),
        leaderboard=get_predictions_leaderboard()
    )


@google_login.login_success
def login_success(token, profile):
    whitelisted_domains = config.get("google_login", "whitelisted_domains")
    if not is_valid_email_domain(profile.get("hd"), whitelisted_domains):
        return jsonify(error="Please use a valid email address!")
    add_user(session, token, profile)
    session["seen"] = True
    return redirect(url_for("my_predictions"))


@google_login.login_failure
def login_failure(error):
    return error(error)


if __name__ == "__main__":
    google_login.redirect_scheme = "http"
    with app.app_context():
        db.create_all()
        populate_teams_table(football_api_client.get_all_teams())
    app.run(port=8000, debug=True)
