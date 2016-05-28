import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow())
    allocated_team_id = db.Column(db.Integer, db.ForeignKey("teams.id"))

    allocated_team = db.relationship("Team")
    predictions = db.relationship("Prediction")

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "joined_date": self.created_at,
            "allocated_team": self.allocated_team.to_json(),
            "predictions": [
                prediction.to_json() for prediction in self.predictions
            ]
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
            "crest_url": self.crest_url
        }


class Prediction(db.Model):
    __tablename__ = "predictions"

    id = db.Column(db.Integer, primary_key=True)
    home_team = db.Column(db.String(100), nullable=False)
    home_score = db.Column(db.Integer, nullable=False)
    away_team = db.Column(db.String(100), nullable=False)
    away_score = db.Column(db.Integer, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    user = db.relationship("User", back_populates="predictions")

    def to_json(self):
        return {
            "home_team": self.home_team,
            "home_score": self.home_score,
            "away_score": self.away_score,
            "away_team": self.away_team
        }
