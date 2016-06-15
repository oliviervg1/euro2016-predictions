#!/usr/bin/env python

import logging
from pprint import pprint
from ConfigParser import SafeConfigParser

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from football_data_client import FootballDataApiClient
from models import User, Result


def setup_logger():
    logging.info("Starting logger for...")
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    return logger


def get_config(config_path):
    config = SafeConfigParser()
    config.read(config_path)
    return config


def get_db_session(db_url):
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    return Session()


def update_results(session, results):
    for game in results:
        try:
            result = session.query(Result).filter_by(
                home_team=game.split("_")[0], away_team=game.split("_")[-1]
            ).first()
            if not result:
                result = Result(
                    home_team=game.split("_")[0],
                    home_score=results[game]["home_score"],
                    away_team=game.split("_")[-1],
                    away_score=results[game]["away_score"]
                )
            else:
                result.home_score = results[game]["home_score"]
                result.away_score = results[game]["away_score"]
            session.add(result)
            session.commit()
        except:
            session.rollback()


def calculate_points(predictions, results):
    points = 0
    for prediction in predictions:
        game = prediction.get_key()
        if game in results:
            predicted_score = prediction.get_value()
            if (
                predicted_score["home_score"] == results[game]["home_score"] and  # noqa
                predicted_score["away_score"] == results[game]["away_score"]
            ):
                points += 3
            elif (
                predicted_score["home_score"] == predicted_score["away_score"] and  # noqa
                results[game]["home_score"] == results[game]["away_score"]
            ):
                points += 1
            elif (
                predicted_score["home_score"] > predicted_score["away_score"] and  # noqa
                results[game]["home_score"] > results[game]["away_score"]
            ):
                points += 1
            elif (
                predicted_score["home_score"] < predicted_score["away_score"] and  # noqa
                results[game]["home_score"] < results[game]["away_score"]
            ):
                points += 1
    return points


def lambda_handler(event, context):
    logger = setup_logger()
    config = get_config("./config.cfg")
    session = get_db_session(config.get("db", "sqlalchemy_db_url"))
    football_api_client = FootballDataApiClient(
        config.get("football_data", "api_key"), 424
    )

    # Get game results
    results = football_api_client.get_results()
    logger.info("Results are:")
    pprint(results)

    # Update results
    update_results(session, results)

    # Update points
    users = session.query(User).all()
    for user in users:
        logger.info("Updating points for {}".format(user.name))
        user.points = calculate_points(user.predictions, results)
    try:
        logger.info("Committing points update")
        session.commit()
        logger.info("Success!")
    except Exception as e:
        session.rollback()
        logger.exception(e)


if __name__ == "__main__":
    lambda_handler(None, None)
