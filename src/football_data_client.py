import requests


class FootballDataApiClient(object):

    def __init__(self, soccer_season_id):
        self.base_endpoint = "http://api.football-data.org/v1"
        self.soccer_season_id = soccer_season_id

    def get_all_teams(self):
        response = requests.get(
            "{0}/soccerseasons/{1}/teams".format(
                self.base_endpoint, self.soccer_season_id
            )
        ).json()
        return [(team["name"], team["crestUrl"]) for team in response["teams"]]

    def get_all_fixtures(self):
        return requests.get(
            "{0}/soccerseasons/{1}/fixtures".format(
                self.base_endpoint, self.soccer_season_id
            )
        ).json()
