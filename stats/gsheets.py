import json
from typing import Any, List
import numpy as np
import pandas as pd
from pathlib import Path

from stats.games import annotate_game_results, normalize_games
from stats.models import Player, TeamSeason


def json_as_df(path_to_json: Path, str_cols: List[str] = []) -> pd.DataFrame:
    """Return a DataFrame with cleaned up column names. Cases are lowered, spaces are turned into `_`, and periods are removed. E.g. `A. AB` turns into `a_ab`

    Args:
        path_to_json Path
        str_cols these columns should be treated as strings and not coerced to numeric
    """
    with open(path_to_json, "r") as f:
        raw_data = json.loads(f.read())

    return values_to_df(raw_data["values"], str_cols)


def values_to_df(values: List[List[Any]], str_cols: List[str] = []) -> pd.DataFrame:
    """Make the actual DataFrame. For column names, cases are lowered, spaces are turned into `_`, and periods are removed. E.g. `A. AB` turns into `a_ab`.

    We automatically cut off any columns missing headers.

    Args:
        values list of lists where the first element is the column labels
        str_cols these columns should be treated as strings and not coerced to numeric
    Returns:
        pd.DataFrame
    """

    columns = values[0]

    # if any row has data that extends beyond the last column in the header, remove it
    rows = [row[: len(columns)] for row in values[1:]]

    df = pd.DataFrame(rows, columns=columns)

    # fix types
    numeric_cols = [col for col in values[0] if col not in str_cols]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    if str_cols:
        df[str_cols] = df[str_cols].astype("string")

    # clean up the column names
    clean_col = lambda col: str(col).lower().strip().replace(" ", "_").replace(".", "")
    df.rename(columns={col: clean_col(col) for col in values[0]}, inplace=True)

    # sometimes LO leaves columns blank. get rid of them
    df.replace({"": np.nan}, inplace=True)
    df.dropna(axis=1, how="all", inplace=True)

    return df


def find_games_with_bad_data(df: pd.DataFrame) -> pd.DataFrame:
    """Return any games where there are NaNs recorded. These would be due to either DCs or bad inputs

    Args:
        df DataFrame of games pre-processing
    Returns:
        DataFrame
    """
    all_nan_rows = df[df.isna().any(axis=1)]
    # increment the index by 2 to match the rows in the spreadsheet (row 1 is the header, games start on row 2)
    all_nan_rows.index += 2

    return all_nan_rows


def normalize_season_games_spreadsheet(
    df: pd.DataFrame,
    active_players: dict[str, List[TeamSeason]],
    league: str,
    playoffs=False,
):
    """Both annotates the input DataFrame of current season box scores (reg season and playoffs) in place to match GameResults as well as return a new normalized DataFrame that matches the standard in docs/data-structures.md

    Args:
        df DataFrame from a {league}__Box%20Scores.json or {league}_Playoffs.json spreadsheet
        active_players dict[player] = [TeamSeason]
        league str
    Returns:
        DataFrame normalized to the standard in docs/data-structures.md
        DataFrame annotated with extra info like player names
    """
    annotated_df = df.copy()

    annotate_game_results(annotated_df, league, playoffs=playoffs)

    teams_to_players = {ts["team_name"]: ts["player"] for ts in active_players[league]}
    annotated_df["away_player"] = annotated_df["away"].apply(
        lambda away: teams_to_players[away]
    )
    annotated_df["home_player"] = annotated_df["home"].apply(
        lambda home: teams_to_players[home]
    )

    return normalize_games(annotated_df, playoffs=playoffs), annotated_df


def normalize_head_to_head_spreadsheet(
    df: pd.DataFrame,
    all_players: dict[str, Player],
    league: str,
    playoffs=False,
):
    # match the columns that `annotate_game_results()` expects. we'll actually flip these column names back later
    df.rename(
        columns={
            "away_player": "away",
            "away_score": "a_score",
            "home_player": "home",
            "home_score": "h_score",
        },
        inplace=True,
    )

    # unnecessary
    df.drop(columns=["away_result", "home_result"], inplace=True)

    annotate_game_results(df, league, playoffs=playoffs)

    def team_name_from_player_season(player: str, season: int):
        teams = all_players[player]["teams"]
        for team in teams:
            if team["season"] == season:
                return team["team_name"]

        raise Exception(f"Couldn't find a team for '{player}' in season '{season}'")

    # flip flop away and home back to the way they were
    # away and home are actually the players
    df.rename(columns={"away": "away_player", "home": "home_player"}, inplace=True)

    # now make home and away the team names
    df["away"] = df.apply(
        lambda row: team_name_from_player_season(row["away_player"], row["season"]),
        axis=1,
    )
    df["home"] = df.apply(
        lambda row: team_name_from_player_season(row["home_player"], row["season"]),
        axis=1,
    )

    return normalize_games(df, playoffs=playoffs)
