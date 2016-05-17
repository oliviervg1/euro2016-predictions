import requests


class GoogleOauth2Client(object):

    def __init__(self):
        self.base_endpoint = "https://www.googleapis.com/oauth2/v3"

    def is_access_token_valid(self, access_token):
        response = requests.get(
            "{0}/tokeninfo?access_token={1}".format(
                self.base_endpoint, access_token
            )
        )
        try:
            response.raise_for_status()
            return True
        except:
            return False
