"""logic for aggregating stats across games"""

import numpy as np
import pandas as pd
from typing import List

from .models import GameResults, League


def annotate_game_results(games_df: pd.DataFrame, league: str, playoffs: bool = False):
    """Update the DataFrame in place. Add wins, losses, run_rule, etc columns to game results. Used as preparation for aggregating stats across games"""
    games_df["league"] = league
    games_df.league = games_df.league.astype("string")

    games_df["a_win"] = np.where(
        games_df.a_score > games_df.h_score,
        1,
        0,
    )
    games_df["h_win"] = np.where(
        games_df.a_score < games_df.h_score,
        1,
        0,
    )
    games_df["a_loss"] = np.where(
        games_df.a_score < games_df.h_score,
        1,
        0,
    )
    games_df["h_loss"] = np.where(
        games_df.a_score > games_df.h_score,
        1,
        0,
    )
    games_df["a_run_rule_win"] = np.where(
        (games_df.ip <= 8.0) & (games_df.a_score > games_df.h_score), 1, 0
    )
    games_df["h_run_rule_win"] = np.where(
        (games_df.ip <= 8.0) & (games_df.a_score < games_df.h_score), 1, 0
    )
    games_df["a_run_rule_loss"] = np.where(
        (games_df.ip <= 8.0) & (games_df.a_score < games_df.h_score), 1, 0
    )
    games_df["h_run_rule_loss"] = np.where(
        (games_df.ip <= 8.0) & (games_df.a_score > games_df.h_score), 1, 0
    )

    if playoffs:
        games_df.week = pd.NA
        games_df["playoffs"] = True
    else:
        games_df["round"] = pd.NA
        games_df["playoffs"] = False


def annotate_computed_stats(team_stats_df: pd.DataFrame, league_era: float):
    """Update the DataFrame in place. Use raw aggregated stats to compute all the stats that depend on more than one column"""

    team_stats_df.rename(columns={"r": "rs", "oppr": "ra"}, inplace=True)

    # hitting
    team_stats_df["rs9"] = (team_stats_df.rs / team_stats_df.innings_hitting) * 9
    team_stats_df["ba"] = team_stats_df.h / team_stats_df.ab
    team_stats_df["ab9"] = (team_stats_df.ab / team_stats_df.innings_hitting) * 9
    team_stats_df["h9"] = (team_stats_df.h / team_stats_df.innings_hitting) * 9
    team_stats_df["hr9"] = (team_stats_df.hr / team_stats_df.innings_hitting) * 9
    team_stats_df["abhr"] = team_stats_df.ab / team_stats_df.hr
    team_stats_df["so9"] = (team_stats_df.so / team_stats_df.innings_hitting) * 9
    team_stats_df["bb9"] = (team_stats_df.bb / team_stats_df.innings_hitting) * 9
    team_stats_df["obp"] = (
        (team_stats_df.h + team_stats_df.bb) / (team_stats_df.ab + team_stats_df.bb) * 9
    )
    team_stats_df["rc"] = team_stats_df.h / team_stats_df.rs
    team_stats_df["babip"] = (team_stats_df.h - team_stats_df.hr) / (
        team_stats_df.ab - team_stats_df.so - team_stats_df.hr
    )
    # keep k and so so we don't break any current ticker configs
    team_stats_df["k"] = team_stats_df["so"]

    # pitching
    team_stats_df["ra9"] = (team_stats_df.ra / team_stats_df.innings_pitching) * 9
    team_stats_df["oppba"] = team_stats_df.opph / team_stats_df.oppab
    team_stats_df["oppab9"] = (team_stats_df.oppab / team_stats_df.innings_pitching) * 9
    team_stats_df["opph9"] = (team_stats_df.opph / team_stats_df.innings_pitching) * 9
    team_stats_df["opphr9"] = (team_stats_df.opphr / team_stats_df.innings_pitching) * 9
    team_stats_df["oppabhr"] = team_stats_df.oppab / team_stats_df.opphr
    team_stats_df["oppk"] = team_stats_df.oppso
    team_stats_df["oppk9"] = (team_stats_df.oppk / team_stats_df.innings_pitching) * 9
    team_stats_df["oppbb9"] = (team_stats_df.oppbb / team_stats_df.innings_pitching) * 9
    team_stats_df["whip"] = (
        team_stats_df.opph + team_stats_df.oppbb
    ) / team_stats_df.innings_pitching
    team_stats_df["lob"] = (
        team_stats_df.opph + team_stats_df.oppbb - team_stats_df.ra
    ) / (team_stats_df.opph + team_stats_df.oppbb - 1.4 * team_stats_df.opphr)
    team_stats_df["fip"] = (
        league_era
        - (team_stats_df.opphr * 13 + 3 * team_stats_df.oppbb - 2 * team_stats_df.oppk)
        / team_stats_df.innings_pitching
    )

    # mixed
    team_stats_df["rd"] = team_stats_df.rs - team_stats_df.ra
    team_stats_df["rd9"] = team_stats_df.rs9 - team_stats_df.ra9
    team_stats_df["innings_played"] = (
        team_stats_df.innings_hitting + team_stats_df.innings_pitching
    ) / 2
    team_stats_df["innings_game"] = (
        team_stats_df.innings_played / team_stats_df.games_played
    )


def normalize_games(games_df: pd.DataFrame, playoffs=False):
    """Return a DF that has been normalized to match the standard columns described in docs/data-structures.md. There should be two rows for every game, one from away's perspective, another from home's. It expects that the games have been run through `annotate_game_results()` to get basic info, and that both player and team names (i.e., `away`, `away_player`, `home`, and `home_player` columns) are available.

    Args:
        df DataFrame

    Returns
        DataFrame that matches docs/data-structures.md
    """
    # we want each game from the home and away perspective so we can index by team
    away_games_df = games_df.copy()

    # rename columns for a single-team-centric row. it doesn't matter that we're starting the new normalized DF from the away games. we'll vertically append the home games afterwards

    # rename columns for away teams
    away_games_df.rename(
        columns={
            "away_player": "player",
            "home_player": "opponent",
            "away": "team",
            "home": "opponent_team",
            "a_win": "win",
            "a_loss": "loss",
            "a_run_rule_win": "run_rule_win",
            "a_run_rule_loss": "run_rule_loss",
            "a_score": "rs",
            "h_score": "ra",
            "ip": "innings",
            "a_ab": "ab",
            "a_h": "h",
            "a_hr": "hr",
            "a_rbi": "rbi",
            "a_bb": "bb",
            "a_so": "so",
            "h_ab": "oppab",
            "h_h": "opph",
            "h_hr": "opphr",
            "h_rbi": "opprbi",
            "h_bb": "oppbb",
            "h_so": "oppso",
        },
        inplace=True,
    )

    # for some unknown reason, errors aren't tracked in the playoffs. thanks Wishbone
    if not playoffs:
        away_games_df.rename(
            columns={
                "a_e": "e",
            },
            inplace=True,
        )

    away_games_df["innings_hitting"] = away_games_df["innings"].apply(
        lambda ip: np.ceil(ip)
    )
    away_games_df["innings_pitching"] = away_games_df["innings"].apply(
        lambda ip: np.floor(ip)
    )

    # follow the same renaming and dropping for home teams
    home_games_df = games_df.copy()

    # rename columns for home teams
    home_games_df.rename(
        columns={
            "home_player": "player",
            "away_player": "opponent",
            "home": "team",
            "away": "opponent_team",
            "h_win": "win",
            "h_loss": "loss",
            "h_run_rule_win": "run_rule_win",
            "h_run_rule_loss": "run_rule_loss",
            "h_score": "rs",
            "a_score": "ra",
            "ip": "innings",
            "h_ab": "ab",
            "h_h": "h",
            "h_hr": "hr",
            "h_rbi": "rbi",
            "h_bb": "bb",
            "h_so": "so",
            "a_ab": "oppab",
            "a_h": "opph",
            "a_hr": "opphr",
            "a_rbi": "opprbi",
            "a_bb": "oppbb",
            "a_so": "oppso",
        },
        inplace=True,
    )

    if not playoffs:
        home_games_df.rename(
            columns={
                "h_e": "e",
            },
            inplace=True,
        )

    home_games_df["innings_hitting"] = home_games_df["innings"].apply(
        lambda ip: np.floor(ip)
    )
    home_games_df["innings_pitching"] = home_games_df["innings"].apply(
        lambda ip: np.ceil(ip)
    )

    # get rid of extraneous columns
    away_games_df.drop(
        columns=[
            # redundant
            "a_r",
            "h_r",
            # not relevant for the away team
            "h_loss",
            "h_run_rule_win",
            "h_run_rule_loss",
            "h_win",
        ],
        inplace=True,
    )

    if not playoffs:
        away_games_df.drop(columns=["h_e"], inplace=True)

    home_games_df.drop(
        columns=[
            # redundant
            "a_r",
            "h_r",
            # not relevant for the home team
            "a_loss",
            "a_run_rule_win",
            "a_run_rule_loss",
            "a_win",
        ],
        inplace=True,
    )

    if not playoffs:
        home_games_df.drop(columns=["a_e"], inplace=True)

    normalized_df = pd.concat([away_games_df, home_games_df], ignore_index=True)
    return normalized_df


def make_game_results(annotated_game_df: pd.DataFrame) -> List[GameResults]:
    df = annotated_game_df.copy()
    # take steps to match GameResults
    df.rename(
        columns={
            "away": "away_team",
            "a_score": "away_score",
            "a_ab": "away_ab",
            "a_r": "away_r",
            "a_h": "away_hits",
            "a_hr": "away_hr",
            "a_rbi": "away_rbi",
            "a_bb": "away_bb",
            "a_so": "away_so",
            "a_e": "away_e",
            "home": "home_team",
            "h_score": "home_score",
            "h_ab": "home_ab",
            "h_r": "home_r",
            "h_h": "home_hits",
            "h_hr": "home_hr",
            "h_rbi": "home_rbi",
            "h_bb": "home_bb",
            "h_so": "home_so",
            "h_e": "home_e",
        },
        inplace=True,
    )

    df["winner"] = df.apply(
        lambda row: (row["home_team"] if row["h_win"] else row["away_team"]),
        axis=1,
    )

    df["run_rule"] = df.apply(
        lambda row: row["a_run_rule_win"] or row["h_run_rule_win"], axis=1
    )

    # remove a couple more columns that aren't needed in the JSON
    df.drop(
        columns=[
            "a_loss",
            "a_run_rule_win",
            "a_run_rule_loss",
            "a_win",
            "h_loss",
            "h_run_rule_win",
            "h_run_rule_loss",
            "h_win",
        ],
        inplace=True,
    )

    return df.to_dict(orient="records")  # type: ignore
