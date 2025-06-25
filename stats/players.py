import pandas as pd
from typing import List

from stats.models import Player, TeamSeason


def aggregate_players(
    xbl_abbrev_df: pd.DataFrame,
    aaa_abbrev_df: pd.DataFrame,
    aa_abbrev_df: pd.DataFrame,
):
    """Find everyone who ever played in any league and when they played"""
    players: dict[str, Player] = {}

    xbl_abbrev_df["league"] = "XBL"
    xbl_abbrev_df.rename(
        columns={"xbl_teams": "team_name", "xbl_abbreviations": "team_abbrev"},
        inplace=True,
    )
    aaa_abbrev_df["league"] = "AAA"
    aaa_abbrev_df.rename(
        columns={"aaa_teams": "team_name", "aaa_abbreviations": "team_abbrev"},
        inplace=True,
    )
    aa_abbrev_df["league"] = "AA"
    aa_abbrev_df.rename(
        columns={"aa_teams": "team_name", "aa_abbreviations": "team_abbrev"},
        inplace=True,
    )

    all_abbrev_df = pd.concat(
        [xbl_abbrev_df, aaa_abbrev_df, aa_abbrev_df], ignore_index=True
    )
    all_abbrev_df.sort_values(by="season", inplace=True)

    # TODO there's probably a clever way of handling this with df.groupby()
    for row in all_abbrev_df.itertuples():
        player = str(row.player)
        if row.player not in players:
            players[player] = {"player": player, "teams": []}

        players[player]["teams"].append(
            {
                "player": player,
                "team_name": str(row.team_name),
                "team_abbrev": str(row.team_abbrev),
                "league": str(row.league),
                "season": row.season,  # type: ignore
            }
        )

    return players


def get_active_players(
    players: dict[str, Player], season: int
) -> dict[str, List[TeamSeason]]:
    """get the players (usernames) who are playing this season. assumes a player is only in 1 league per season

    Args:
        players {player name: Player}
        season int
    Returns:
        {league: [TeamSeason]}
    """

    active_players: dict[str, List[TeamSeason]] = {"XBL": [], "AAA": [], "AA": []}

    for player_name in players:
        for team in players[player_name]["teams"]:
            if team["season"] == season:
                active_players[team["league"]].append(team)
                break

    return active_players
