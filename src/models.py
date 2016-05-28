import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow())

    predictions = db.relationship("Prediction")


class Prediction(db.Model):
    __tablename__ = "predictions"

    id = db.Column(db.Integer, primary_key=True)
    home_team = db.Column(db.String(100), nullable=False)
    home_score = db.Column(db.Integer, nullable=False)
    away_team = db.Column(db.String(100), nullable=False)
    away_score = db.Column(db.Integer, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    user = db.relationship("User", back_populates="predictions")

    def __repr__(self):
        return "{home_team} {home_score}-{away_score} {away_team}".format(
            home_team=self.home_team,
            home_score=self.home_score,
            away_score=self.away_score,
            away_team=self.away_team
        )
