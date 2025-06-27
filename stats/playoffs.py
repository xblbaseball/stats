import copy
import pandas as pd
from typing import List

from stats.models import PlayoffsGameResults, PlayoffsRound, PlayoffsTeamRecord


def collect_playoffs_team_records(df: pd.DataFrame):
    """figure out how each round of the playoffs is going for each team"""
    records_by_team: dict[str, PlayoffsTeamRecord] = {}

    default_round = {"wins": 0, "losses": 0, "remaining": 0}

    # todo maybe just groupby [team, opponent] in the normalized results?

    for game in df.itertuples():
        away_team = game["away"]
        home_team = game["home"]
        this_round = game["round"]

        if home_team not in records_by_team:
            records_by_team[home_team] = {"team": home_team, "rounds": {}}

        if away_team not in records_by_team:
            records_by_team[away_team] = {"team": away_team, "rounds": {}}

        if this_round not in records_by_team[home_team]["rounds"]:
            playoffs_round: PlayoffsRound = default_round | {
                "round": this_round,
                "team": home_team,
                "opponent": away_team,
            }  # type: ignore
            records_by_team[home_team]["rounds"][this_round] = playoffs_round

        if this_round not in records_by_team[away_team]["rounds"]:
            playoffs_round: PlayoffsRound = default_round | {
                "round": this_round,
                "team": away_team,
                "opponent": home_team,
            }  # type: ignore
            records_by_team[away_team]["rounds"][this_round] = playoffs_round

        home_round_record = copy.deepcopy(
            records_by_team[home_team]["rounds"][this_round]
        )
        away_round_record = copy.deepcopy(
            records_by_team[away_team]["rounds"][this_round]
        )

        winner = away_team if game["away_score"] > game["home_score"] else home_team

        if winner == away_team:
            away_round_record["wins"] += 1
            home_round_record["losses"] += 1
        else:
            home_round_record["wins"] += 1
            away_round_record["losses"] += 1

        # TODO it'd be nice to have access to something that tells us how many games are in the series

        records_by_team[away_team]["rounds"][this_round] = away_round_record
        records_by_team[home_team]["rounds"][this_round] = home_round_record

    return records_by_team
