#!/usr/bin/env python

import app as euro2016


def main():
    with euro2016.app.app_context():
        euro2016.db.create_all()
        euro2016.populate_teams_table(
            euro2016.football_api_client.get_all_teams()
        )


if __name__ == "__main__":
    main()
