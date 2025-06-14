import pandas as pd
from typing import List

from stats.models import Player


def aggregate_players(
    xbl_abbrev_df: pd.DataFrame,
    aaa_abbrev_df: pd.DataFrame,
    aa_abbrev_df: pd.DataFrame,
) -> dict[str, Player]:
    """Find everyone who ever played in any league and when they played"""
    players: dict[str, Player] = {}

    xbl_abbrev_df["league"] = "XBL"
    xbl_abbrev_df.rename(
        columns={"xbl_teams": "teams", "xbl_abbreviations": "abbreviations"},
        inplace=True,
    )
    aaa_abbrev_df["league"] = "AAA"
    aaa_abbrev_df.rename(
        columns={"aaa_teams": "teams", "aaa_abbreviations": "abbreviations"},
        inplace=True,
    )
    aa_abbrev_df["league"] = "AA"
    aa_abbrev_df.rename(
        columns={"aa_teams": "teams", "aa_abbreviations": "abbreviations"}, inplace=True
    )

    all_abbrev_df = pd.concat(
        [xbl_abbrev_df, aaa_abbrev_df, aa_abbrev_df], ignore_index=True
    )

    # all_abbrev_df.groupby("player").agg(
    #     # teams=("pd.DataFrame())
    # )

    print(all_abbrev_df)

    # for row in xbl_abbrev_data[1:]:
    #     season = int(row[0])
    #     team_name = row[1]
    #     team_abbrev = row[2]
    #     player = row[3]

    #     if player not in players:
    #         players[player] = {"player": player, "teams": []}

    #     players[player]["teams"].append(
    #         {
    #             "player": player,
    #             "team_name": team_name,
    #             "team_abbrev": team_abbrev,
    #             "league": "XBL",
    #             "season": season,
    #         }
    #     )

    # for row in aaa_abbrev_data[1:]:
    #     season = int(row[0])
    #     team_name = row[1]
    #     team_abbrev = row[2]
    #     player = row[3]

    #     if player not in players:
    #         players[player] = {"player": player, "teams": []}

    #     players[player]["teams"].append(
    #         {
    #             "player": player,
    #             "team_name": team_name,
    #             "team_abbrev": team_abbrev,
    #             "league": "AAA",
    #             "season": season,
    #         }
    #     )

    # for row in aa_abbrev_data[1:]:
    #     season = int(row[0])
    #     team_name = row[1]
    #     team_abbrev = row[2]
    #     player = row[3]

    #     if player not in players:
    #         players[player] = {"player": player, "teams": []}

    #     players[player]["teams"].append(
    #         {
    #             "player": player,
    #             "team_name": team_name,
    #             "team_abbrev": team_abbrev,
    #             "league": "AA",
    #             "season": season,
    #         }
    #     )

    # # sort teams in order of ascending season
    # for player in players.keys():
    #     sorted_teams = sorted(players[player]["teams"], key=lambda team: team["season"])
    #     players[player]["teams"] = sorted_teams

    return players


# def get_active_players(
#     players: dict[str, Player], season: int
# ) -> dict[str, List[TeamSeason]]:
#     """get the players (usernames) who are playing this season. assumes a player is only in 1 league per season"""

#     active_players: dict[str, List[TeamSeason]] = {"XBL": [], "AAA": [], "AA": []}

#     for player_name in players:
#         for team in players[player_name]["teams"]:
#             if team["season"] == season:
#                 active_players[team["league"]].append(team)
#                 break

#     return active_players
