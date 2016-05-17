from football_data_client import FootballDataApiClient
from google_oauth_client import GoogleOauth2Client

from flask import Flask, session, jsonify, redirect, url_for
from flask_oauth2_login import GoogleLogin

app = Flask(__name__)
app.config.update(
    SECRET_KEY="secret",
    GOOGLE_LOGIN_REDIRECT_SCHEME="http",
    GOOGLE_LOGIN_CLIENT_ID="1071286879712-h5ibu7s009v31lte976k7357190258b4.apps.googleusercontent.com",  # noqa
    GOOGLE_LOGIN_CLIENT_SECRET="DuprXHx4cvd4asJx2oTEPbhI"
)

google_login = GoogleLogin(app)

football_api_client = FootballDataApiClient(424)
google_oauth2_client = GoogleOauth2Client()


@app.route("/status")
def status():
    return jsonify(response="OK")


@app.route("/")
def index():
    access_token = session.get("access_token")
    if not google_oauth2_client.is_access_token_valid(access_token):
        return redirect(google_login.authorization_url())
    return jsonify(session)


@google_login.login_success
def login_success(token, profile):
    session["access_token"] = token["access_token"]
    session["profile"] = profile
    return redirect(url_for("index"))


@google_login.login_failure
def login_failure(e):
    return jsonify(error=str(e))


if __name__ == '__main__':
    app.run(port=8000, debug=True)
