import numpy as np
import pandas as pd
from typing import List

from .models import GameResults, League


def annotate_game_results(games_df: pd.DataFrame, league: str, playoffs: bool = False):
    """Add `league`, wins, losses, run_rule, etc columns to game results. Used as preparation for aggregating stats accross games"""

    games_df["league"] = league
    games_df["game"] = 1

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

    games_df["league"] = games_df["league"].astype("string")

    if playoffs:
        games_df.week = pd.NA
    else:
        games_df["round"] = pd.NA


def agg_team_stats(all_games_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate stats by team across all games in the input dataframe. Assumes games have been annotated with `annotate_game_results`"""

    home_stats_df = all_games_df.groupby("home").agg(
        wins=("h_win", "sum"),
        losses=("h_loss", "sum"),
        wins_by_run_rule=("h_run_rule_win", "sum"),
        losses_by_run_rule=("h_run_rule_loss", "sum"),
        games_played=("game", "sum"),
        ab=("h_ab", "sum"),
        r=("h_score", "sum"),
        h=("h_h", "sum"),
        hr=("h_hr", "sum"),
        rbi=("h_rbi", "sum"),
        bb=("h_bb", "sum"),
        so=("h_so", "sum"),
        oppab=("a_ab", "sum"),
        oppr=("a_score", "sum"),
        opph=("a_h", "sum"),
        opphr=("a_hr", "sum"),
        opprbi=("a_rbi", "sum"),
        oppbb=("a_bb", "sum"),
        oppso=("a_so", "sum"),
        innings_hitting=("ip", lambda ips: sum(np.floor(ip) for ip in ips)),
        innings_pitching=("ip", lambda ips: sum(np.ceil(ip) for ip in ips)),
    )

    away_stats_df = all_games_df.groupby("away").agg(
        wins=("a_win", "sum"),
        losses=("a_loss", "sum"),
        wins_by_run_rule=("a_run_rule_win", "sum"),
        losses_by_run_rule=("a_run_rule_loss", "sum"),
        games_played=("game", "sum"),
        ab=("a_ab", "sum"),
        r=("a_score", "sum"),
        h=("a_h", "sum"),
        hr=("a_hr", "sum"),
        rbi=("a_rbi", "sum"),
        bb=("a_bb", "sum"),
        so=("a_so", "sum"),
        oppab=("h_ab", "sum"),
        oppr=("h_score", "sum"),
        opph=("h_h", "sum"),
        opphr=("h_hr", "sum"),
        opprbi=("h_rbi", "sum"),
        oppbb=("h_bb", "sum"),
        oppso=("h_so", "sum"),
        innings_hitting=("ip", lambda ips: sum(np.ceil(ip) for ip in ips)),
        innings_pitching=("ip", lambda ips: sum(np.floor(ip) for ip in ips)),
    )

    team_stats_df = away_stats_df + home_stats_df
    team_stats_df.rename_axis("team", inplace=True)

    return team_stats_df


def annotate_computed_stats(team_stats_df: pd.DataFrame, league_era: float):
    """Use raw aggregated stats to compute all the stats that depend on more than one column"""

    # hitting
    team_stats_df["rs"] = team_stats_df.r
    team_stats_df["rs9"] = (team_stats_df.r / team_stats_df.innings_hitting) * 9
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
    team_stats_df["rc"] = team_stats_df.h / team_stats_df.r
    team_stats_df["babip"] = (team_stats_df.h - team_stats_df.hr) / (
        team_stats_df.ab - team_stats_df.so - team_stats_df.hr
    )
    team_stats_df["k"] = team_stats_df["so"]

    # pitching
    team_stats_df["ra"] = team_stats_df.oppr
    team_stats_df["ra9"] = (team_stats_df.oppr / team_stats_df.innings_pitching) * 9
    team_stats_df["oppba"] = team_stats_df.opph / team_stats_df.oppab
    team_stats_df["oppab9"] = (team_stats_df.oppab / team_stats_df.innings_pitching) * 9
    team_stats_df["opph9"] = (team_stats_df.opph / team_stats_df.innings_pitching) * 9
    team_stats_df["opphr9"] = (team_stats_df.opphr / team_stats_df.innings_pitching) * 9
    team_stats_df["oppabhr"] = team_stats_df.oppab / team_stats_df.opphr
    team_stats_df["oppk"] = team_stats_df.oppso
    team_stats_df["oppk9"] = (team_stats_df.oppk / team_stats_df.innings_pitching) * 9
    team_stats_df["oppbb9"] = (team_stats_df.oppbb / team_stats_df.innings_pitching) * 9
    team_stats_df["whip"] = (
        team_stats_df.opph + team_stats_df.oppbb / team_stats_df.innings_pitching
    )
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

    # these were renamed
    team_stats_df.drop(
        columns=[
            "r",
            "oppr",
        ],
        inplace=True,
    )
