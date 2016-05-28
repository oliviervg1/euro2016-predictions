import random

from ConfigParser import SafeConfigParser

from google_oauth_client import GoogleOauth2Client

from models import db, User, Prediction, Team


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
        user = User(email=profile["email"], name=profile["name"])
        user.allocated_team = allocate_team()
        db.session.add(user)
        db.session.commit()
    session["user"] = profile
    return user


def set_predictions(user, form_predictions):
    predictions = []
    i = 1
    while True:
        try:
            predictions.append(Prediction(
                home_team=form_predictions["home_team_{0}".format(i)],
                home_score=form_predictions["home_score_{0}".format(i)],
                away_team=form_predictions["away_team_{0}".format(i)],
                away_score=form_predictions["away_score_{0}".format(i)]
            ))
            i += 1
        except KeyError:
            break
    db.session.add_all(predictions)
    user.predictions = predictions
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
