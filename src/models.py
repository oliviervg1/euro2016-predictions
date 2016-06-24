import datetime
import urllib

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow())
    allocated_team_id = db.Column(db.Integer, db.ForeignKey("teams.id"))
    points = db.Column(db.Integer, nullable=False)

    allocated_team = db.relationship("Team")
    predictions = db.relationship(
        "Prediction", cascade="delete, delete-orphan"
    )

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "joined_date": self.created_at,
            "allocated_team": self.allocated_team.to_json(),
            "predictions": {
                prediction.get_key(): prediction.get_value()
                for prediction in self.predictions
            },
            "points": self.points
        }


class Team(db.Model):
    __tablename__ = "teams"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    crest_url = db.Column(db.String(100), nullable=False)

    allocated_users = db.relationship("User", back_populates="allocated_team")

    def to_json(self):
        return {
            "name": self.name,
            "crest_url": urllib.quote_plus(self.crest_url, safe="/:")
        }


class Prediction(db.Model):
    __tablename__ = "predictions"

    id = db.Column(db.Integer, primary_key=True)
    matchday = db.Column(db.Integer, nullable=False, default=0)
    home_team = db.Column(db.String(100), nullable=False)
    home_score = db.Column(db.Integer, nullable=False)
    away_team = db.Column(db.String(100), nullable=False)
    away_score = db.Column(db.Integer, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    user = db.relationship("User", back_populates="predictions")

    def get_key(self):
        return "{0}_{1}_{2}".format(
            self.matchday, self.home_team, self.away_team
        )

    def get_value(self):
        return {
            "home_score": self.home_score,
            "away_score": self.away_score
        }


class Result(db.Model):
    __tablename__ = "results"

    matchday = db.Column(db.Integer, nullable=False, default=0)
    home_team = db.Column(db.String(100), primary_key=True, nullable=False)
    home_score = db.Column(db.Integer, nullable=False)
    away_team = db.Column(db.String(100), primary_key=True, nullable=False)
    away_score = db.Column(db.Integer, nullable=False)

    def get_key(self):
        return "{0}_{1}_{2}".format(
            self.matchday, self.home_team, self.away_team
        )

    def get_value(self):
        return {
            "home_score": self.home_score,
            "away_score": self.away_score
        }
