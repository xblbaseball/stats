import copy
import pandas as pd
from typing import List

from stats.models import PlayoffsGameResults, PlayoffsRound, PlayoffsTeamRecord


def collect_playoffs_team_records(normalized_df: pd.DataFrame):
    """figure out how each round of the playoffs is going for each team"""
    records_by_team: dict[str, PlayoffsTeamRecord] = {}

    default_round = {"wins": 0, "losses": 0, "remaining": 0}

    for game in normalized_df.itertuples():
        team = str(game.team)
        opponent = str(game.opponent_team)
        this_round = str(game.round)

        # win and loss are either 1 or 0
        win: int = game.win  # type: ignore
        loss: int = game.loss  # type: ignore

        if team not in records_by_team:
            records_by_team[team] = {"team": team, "rounds": {}}

        if this_round not in records_by_team[team]["rounds"]:
            playoffs_round: PlayoffsRound = default_round | {
                "round": this_round,
                "team": team,
                "opponent": opponent,
            }  # type: ignore
            records_by_team[team]["rounds"][this_round] = playoffs_round

        team_record = copy.deepcopy(records_by_team[team]["rounds"][this_round])

        team_record["wins"] += win
        team_record["losses"] += loss

        # TODO it'd be nice to have access to something that tells us how many games are in the series

        records_by_team[team]["rounds"][this_round] = team_record

    return records_by_team
