import numpy as np
import pandas as pd
from typing import List

from .models import GameResults, League


def annotate_game_results(games_df: pd.DataFrame, league: str, playoffs: bool = False):
    """Add `league`, wins, losses, and run_rule columns to game results"""

    games_df["league"] = league
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
        wins=("h_win", "sum"),
        losses=("h_loss", "sum"),
        wins_by_run_rule=("h_run_rule_win", "sum"),
        losses_by_run_rule=("h_run_rule_loss", "sum"),
    )

    away_stats_df = all_games_df.groupby("away").agg(
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
        wins=("a_win", "sum"),
        losses=("a_loss", "sum"),
        wins_by_run_rule=("a_run_rule_win", "sum"),
        losses_by_run_rule=("a_run_rule_loss", "sum"),
    )

    team_stats_df = away_stats_df + home_stats_df
    team_stats_df.rename_axis("team", inplace=True)

    return team_stats_df
