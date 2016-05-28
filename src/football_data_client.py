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
