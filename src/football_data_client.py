import requests


class FootballDataApiClient(object):

    def __init__(self, api_key, soccer_season_id):
        self.base_endpoint = "http://api.football-data.org/v1"
        self.soccer_season_id = soccer_season_id
        self.requests = requests.Session()
        self.requests.headers.update({"X-Auth-Token": api_key})
        self._all_teams = None
        self._all_fixtures = None

    def get_all_teams(self):
        if self._all_teams is None:
            response = self.requests.get(
                "{0}/soccerseasons/{1}/teams".format(
                    self.base_endpoint, self.soccer_season_id
                )
            )
            response.raise_for_status()
            data = response.json()
            self._all_teams = [
                (team["name"], team["crestUrl"]) for team in data["teams"]
            ]
        return self._all_teams

    def get_all_fixtures(self):
        if self._all_fixtures is None:
            response = self.requests.get(
                "{0}/soccerseasons/{1}/fixtures".format(
                    self.base_endpoint, self.soccer_season_id
                )
            )
            response.raise_for_status()
            self._all_fixtures = response.json()["fixtures"]
        return self._all_fixtures

    def get_results(self):
        response = self.requests.get(
            "{0}/soccerseasons/{1}/fixtures".format(
                self.base_endpoint, self.soccer_season_id
            )
        )
        response.raise_for_status()
        return {
            "{}_{}_{}".format(
                fixture["matchday"],
                fixture["homeTeamName"],
                fixture["awayTeamName"]
            ):
                {
                    "home_score": fixture["result"]["goalsHomeTeam"],
                    "away_score": fixture["result"]["goalsAwayTeam"]
                }
            for fixture in response.json()["fixtures"]
            if fixture["result"]["goalsHomeTeam"] is not None and fixture["result"]["goalsAwayTeam"] is not None  # noqa
        }

    def check_predictions_validity(self, predictions):
        fixtures = self.get_all_fixtures()

        def find_fixture(matchday, home_team, away_team):
            games = [
                fixture for fixture in fixtures
                if fixture["matchday"] == matchday and
                fixture["homeTeamName"] == home_team and
                fixture["awayTeamName"] == away_team
            ]
            if len(games) != 1:
                raise Exception(
                    "Looks like you tried to predict the score for a game "
                    "that doesn't exist!"
                )
            return games[0]

        for prediction in predictions:
            fixture = find_fixture(
                prediction["matchday"],
                prediction["home_team"],
                prediction["away_team"]
            )
            if fixture["status"] == "FINISHED":
                raise Exception(
                    "You can't set a prediction for a game that has already "
                    "happened!"
                )

        return True
