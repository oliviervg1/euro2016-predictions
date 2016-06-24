import pytz
import random

from datetime import datetime
from collections import OrderedDict
from ConfigParser import SafeConfigParser

from sqlalchemy import desc

from google_oauth_client import GoogleOauth2Client

from models import db, User, Prediction, Team, Result


def get_config(config_path):
    config = SafeConfigParser()
    config.read(config_path)
    return config


def is_user_logged_in(session):
    google_oauth2_client = GoogleOauth2Client()
    access_token = session.get("access_token")
    if not google_oauth2_client.is_access_token_valid(access_token):
        return False, None
    user = User.query.filter_by(email=session["user"]["email"]).first()
    if not user:
        return False, None
    return True, user


def is_valid_email_domain(domain_name, whitelisted_domains):
    allowed_domains = whitelisted_domains.split(",")
    if domain_name in allowed_domains or "_all_" in allowed_domains:
        return True
    return False


def allocate_team():
    teams = Team.query.all()
    unallocated_teams = []
    i = 0
    while unallocated_teams == []:
        unallocated_teams = [
            team for team in teams if len(team.allocated_users) <= i
        ]
        i += 1
    return random.choice(unallocated_teams)


def add_user(session, token, profile):
    session["access_token"] = token["access_token"]
    user = User.query.filter_by(email=profile["email"]).first()
    if user is None:
        user = User(email=profile["email"], name=profile["name"], points=0)
        user.allocated_team = allocate_team()
        db.session.add(user)
        db.session.commit()
    session["user"] = profile
    return user


def get_user_information(user_id):
    return User.query.filter_by(id=user_id).one()


def get_user_count():
    return User.query.count()


def get_team_allocations():
    all_teams = Team.query.all()
    return {
        team.name: ", ".join([user.name for user in team.allocated_users])
        for team in all_teams
    }


def get_predictions_leaderboard():
    all_users = User.query.order_by(desc(User.points)).all()
    leaderboard = OrderedDict()
    for user in all_users:
        leaderboard[user.name] = {
            "id": user.id,
            "points": user.points
        }
    return leaderboard


def convert_submit_form_to_dict(form_predictions):
    predictions = []
    i = 1
    while True:
        try:
            predictions.append({
                "matchday": int(form_predictions["matchday_{0}".format(i)]),
                "home_team": form_predictions["home_team_{0}".format(i)],
                "home_score": form_predictions["home_score_{0}".format(i)],
                "away_team": form_predictions["away_team_{0}".format(i)],
                "away_score": form_predictions["away_score_{0}".format(i)]
            })
            i += 1
        except KeyError:
            break
    return predictions


def set_predictions(user, predictions):
    for prediction in predictions:
        try:
            db_prediction = Prediction.query.filter_by(
                matchday=prediction["matchday"],
                home_team=prediction["home_team"],
                away_team=prediction["away_team"]
            ).first()

            if db_prediction is None:
                db_prediction = Prediction(
                    matchday=prediction["matchday"],
                    home_team=prediction["home_team"],
                    home_score=prediction["home_score"],
                    away_team=prediction["away_team"],
                    away_score=prediction["away_score"]
                )
                db.session.add(db_prediction)
                user.predictions.append(db_prediction)
            else:
                db_prediction.home_score = prediction["home_score"]
                db_prediction.away_score = prediction["away_score"]
        except:
            db.session.rollback()
            raise
    db.session.commit()
    return True


def populate_teams_table(teams):
    db_teams = []
    for team, crest_url in teams:
        db_teams.append(Team(
            name=team,
            crest_url=crest_url
        ))
    db.session.add_all(db_teams)
    try:
        db.session.commit()
    except:
        db.session.rollback()


def get_current_time():
    return datetime.utcnow().replace(tzinfo=pytz.utc)


def get_points_for_user(user_predictions):
    # Cater for fact that results table might not exist
    try:
        results = Result.query.all()
    except:
        return {}

    user_points = {}

    for result in results:
        game = result.get_key()
        if game in user_predictions:
            score = result.get_value()
            score_str = "{home_score} - {away_score}".format(**score)
            if (
                score["home_score"] == user_predictions[game]["home_score"] and
                score["away_score"] == user_predictions[game]["away_score"]
            ):
                user_points[game] = {
                    "result": score_str,
                    "points": 3
                }
            elif (
                score["home_score"] == score["away_score"] and
                user_predictions[game]["home_score"] == user_predictions[game]["away_score"]  # noqa
            ):
                user_points[game] = {
                    "result": score_str,
                    "points": 1
                }
            elif (
                score["home_score"] > score["away_score"] and
                user_predictions[game]["home_score"] > user_predictions[game]["away_score"]  # noqa
            ):
                user_points[game] = {
                    "result": score_str,
                    "points": 1
                }
            elif (
                score["home_score"] < score["away_score"] and
                user_predictions[game]["home_score"] < user_predictions[game]["away_score"]  # noqa
            ):
                user_points[game] = {
                    "result": score_str,
                    "points": 1
                }
            else:
                user_points[game] = {
                    "result": score_str,
                    "points": 0
                }

    return user_points
