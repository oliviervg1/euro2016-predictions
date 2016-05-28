import requests


class FootballDataApiClient(object):

    def __init__(self, api_key, soccer_season_id):
        self.base_endpoint = "http://api.football-data.org/v1"
        self.soccer_season_id = soccer_season_id
        self.requests = requests.Session()
        self.requests.headers.update({"X-Auth-Token": api_key})

    def get_all_teams(self):
        response = self.requests.get(
            "{0}/soccerseasons/{1}/teams".format(
                self.base_endpoint, self.soccer_season_id
            )
        )
        response.raise_for_status()
        data = response.json()
        return [(team["name"], team["crestUrl"]) for team in data["teams"]]

    def get_all_fixtures(self):
        response = self.requests.get(
            "{0}/soccerseasons/{1}/fixtures".format(
                self.base_endpoint, self.soccer_season_id
            )
        )
        response.raise_for_status()
        return response.json()
