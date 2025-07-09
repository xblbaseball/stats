import argparse
import json
import math
import numpy as np
import os
import pandas as pd
from pathlib import Path
from typing import List

from stats import gsheets
from stats.games import (
    annotate_computed_stats,
    annotate_game_results,
    make_game_results,
    normalize_games,
)
from stats.models import *
from stats.players import aggregate_players, get_active_players
from stats.playoffs import collect_playoffs_team_records
from stats.standings import clean_standings

LEAGUES = ["XBL", "AAA", "AA"]


class StatsAggNamespace(argparse.Namespace):
    season: int
    g_sheets_dir: Path
    save_dir: Path
    query: List[str]


def arg_parser():
    parser = argparse.ArgumentParser(
        description="Aggregate high-level XBL stats per-season and for careers"
    )
    parser.add_argument(
        "-s", "--season", type=int, required=True, help="Current season"
    )
    parser.add_argument(
        "--g-sheets-dir",
        "-g",
        type=Path,
        default=Path("public/raw"),
        help="Path to where JSON from Google Sheets is stored",
    )
    parser.add_argument(
        "--save-dir",
        "-S",
        type=Path,
        default=Path("public"),
        help="Path to where parsed JSON should be stored",
    )
    parser.add_argument(
        "--query",
        "-Q",
        nargs="+",
        type=List[str],
        default=[],
        help="Perform a query on the resulting data. Enter a list of keys to look up. The first key must be either 'career' or 'season'",
    )

    return parser


# kwargs to use when calling .groupby( ... ).agg(**kwargs) to aggregate stats
AGG_NORMALIZED_STATS_KWARGS = {
    "league": ("league", "first"),
    "games_played": ("team", "count"),  # FYI column doesn't matter
    "wins": ("win", "sum"),
    "losses": ("loss", "sum"),
    "wins_by_run_rule": ("run_rule_win", "sum"),
    "losses_by_run_rule": ("run_rule_loss", "sum"),
    "ab": ("ab", "sum"),
    "r": ("rs", "sum"),
    "h": ("h", "sum"),
    "hr": ("hr", "sum"),
    "rbi": ("rbi", "sum"),
    "bb": ("bb", "sum"),
    "so": ("so", "sum"),
    "oppab": ("oppab", "sum"),
    "oppr": ("ra", "sum"),
    "opph": ("opph", "sum"),
    "opphr": ("opphr", "sum"),
    "opprbi": ("opprbi", "sum"),
    "oppbb": ("oppbb", "sum"),
    "oppso": ("oppso", "sum"),
    "innings_hitting": ("innings_hitting", "sum"),
    "innings_pitching": ("innings_pitching", "sum"),
}


def prep_career_stats(
    args: type[StatsAggNamespace], all_players: dict[str, Player], league: str
):
    df = gsheets.json_as_df(
        args.g_sheets_dir / f"CAREER_STATS__{league}%20Head%20to%20Head.json",
        str_cols=[
            "Week",
            "Away Player",
            "Away Result",
            "Home Player",
            "Home Result",
        ],
    )

    df["league"] = league

    normalized_df = gsheets.normalize_head_to_head_spreadsheet(
        df, all_players, league, playoffs=False
    )

    return normalized_df


def build_career_stats(
    args: type[StatsAggNamespace], all_players: dict[str, Player]
) -> CareerStats:
    """Get career stats for all players

    Args:
        args StatsAggNamespace
    Returns:
        CareerStats
    """

    print(f"Running career stats...")

    # TODO filter on league, season, player, then agg stats

    # by_season_df = all_games_ever_df[
    #     (all_games_ever_df.season == 18) & (all_games_ever_df.away == "shameronium")
    # ]
    # print(by_season_df)1

    # TODO:
    # - all-time
    # - per regular season
    # - per league RS
    # - per opponent
    # - per playoffs
    # - per league playoffs

    # groupby_season = all_games_ever_df.groupby(["season", "league", "team"])
    # ba_per_season_league_team = groupby_season.agg(ab=("ab", "sum"), hits=("h", "sum"))

    # ba_per_season_league = ba_per_season_league_team.groupby(["season", "league"]).agg(
    #     ab=("ab", "sum"), hits=("hits", "sum")
    # )
    # print(ba_per_season_league["hits"] / ba_per_season_league["ab"])

    # all_games_by_player_df = agg_team_stats(all_games_ever_df, index="player")
    # print(all_games_by_player_df)

    # eras_df = all_games_by_player_df.groupby(["league", "season"]).agg(
    #     runs=("rs", "sum"), innings_pitching=("innings_pitching", "sum")
    # )

    # print(eras_df)

    # TODO need league ERAs here

    # all_time_stats_by_player_df = annotate_computed_stats(all_games_by_player_df)

    # print(
    #     "Tabulating career regular season stats, stats by season, stats by league, and head to head performances..."
    # )
    # regular_season, regular_season_head_to_head = (
    #     collect_career_performances_and_head_to_head(
    #         False,
    #         xbl_head_to_head_data,
    #         aaa_head_to_head_data,
    #         aa_head_to_head_data,
    #     )
    # )

    # data["regular_season"] = regular_season
    # data["regular_season_head_to_head"] = regular_season_head_to_head

    # xbl_playoffs_head_to_head_data = None
    # with open(g_sheets_dir.joinpath("PLAYOFF_STATS__XBL%20Head%20to%20Head.json")) as f:
    #     raw_data = json.loads(f.read())
    #     xbl_playoffs_head_to_head_data = raw_data["values"]

    # aaa_playoffs_head_to_head_data = None
    # with open(g_sheets_dir.joinpath("PLAYOFF_STATS__AAA%20Head%20to%20Head.json")) as f:
    #     raw_data = json.loads(f.read())
    #     aaa_playoffs_head_to_head_data = raw_data["values"]

    # aa_playoffs_head_to_head_data = None
    # with open(g_sheets_dir.joinpath("PLAYOFF_STATS__AA%20Head%20to%20Head.json")) as f:
    #     raw_data = json.loads(f.read())
    #     aa_playoffs_head_to_head_data = raw_data["values"]

    # print("Tabulating career playoffs stats and head to head performances...")
    # playoffs, playoffs_head_to_head = collect_career_performances_and_head_to_head(
    #     True,
    #     xbl_playoffs_head_to_head_data,
    #     aaa_playoffs_head_to_head_data,
    #     aa_playoffs_head_to_head_data,
    # )

    # data["playoffs"] = playoffs
    # data["playoffs_head_to_head"] = playoffs_head_to_head

    # return data
    return None


def clean_box_scores(games_df: pd.DataFrame, players_df: pd.DataFrame):
    pass


def main(args: type[StatsAggNamespace]) -> str | None:
    """Collect season and all-time stats, write to JSON

    Args:
        args StatsAggNamespace
    Returns:
        str | None
    """

    # will be filled out and written to JSON
    season_stats_to_write: SeasonStats = {
        "current_season": args.season,
        "season_team_records": {},
        "season_team_stats": {},
        "season_game_results": [],
        "playoffs_team_records": {},
        "playoffs_team_stats": {},
        "playoffs_game_results": [],
    }

    # will be filled out and written to JSON
    career_stats_to_write: CareerStats = {
        "all_players": {},
        "active_players": {},
        "regular_season": {},
        "regular_season_head_to_head": [],
        "playoffs": {},
        "playoffs_head_to_head": [],
    }

    # will be filled out and written to HTML
    missing_games_to_write = {
        "XBL": {"regular_season": [], "playoffs": []},
        "AAA": {"regular_season": [], "playoffs": []},
        "AA": {"regular_season": [], "playoffs": []},
    }

    # a DF that maps (human) players with teams they've played as
    team_abbrev_df = [
        gsheets.json_as_df(
            args.g_sheets_dir / f"CAREER_STATS__{league}%20Team%20Abbreviations.json",
            str_cols=[
                f"{league} Teams",
                f"{league} Abbreviations",
                "Player",
                "Concatenate",
                "Seasons Played",
            ],
        )
        for league in LEAGUES
    ]

    # get who has played as what team, and who is currently playing this season
    all_players = aggregate_players(*team_abbrev_df)
    active_players = get_active_players(all_players, args.season)

    career_stats_to_write["all_players"] = all_players
    career_stats_to_write["active_players"] = active_players

    # season stats collection
    for league in LEAGUES:
        print(
            f"Running season {args.season} stats for regular season {league} games..."
        )
        # used for both season_team_stats and season_game_results
        df = gsheets.json_as_df(
            args.g_sheets_dir / f"{league}__Box%20Scores.json",
            str_cols=["Away", "Home", "Week"],
        )

        df["season"] = args.season

        dcs_and_bad_data = gsheets.find_games_with_bad_data(df)
        if len(dcs_and_bad_data) > 0:
            missing_games_to_write[league][
                "regular_season"
            ] += dcs_and_bad_data.to_dict(orient="records")

        # note this returns a normalized DataFrame AND mutates the input
        normalized_df, annotated_df = gsheets.normalize_season_games_spreadsheet(
            df, active_players, league, playoffs=False
        )

        #
        # build season_stats.season_game_results
        #

        season_stats_to_write["season_game_results"] += make_game_results(annotated_df)  # type: ignore

        #
        # build season_stats.season_team_stats
        #

        # remove DCs and games with missing data first. we don't want to include games with missing stats when we collect computed stats
        # we know either 'week' or 'round' will be na, so ignore those columns when determining which games are DCs
        all_columns_but_week_or_round = [
            col for col in normalized_df.columns if col not in ["week", "round"]
        ]
        normalized_games_no_dcs_df = normalized_df.dropna(
            subset=all_columns_but_week_or_round
        )

        # a query that sums raw numbers for each team for the season
        # TODO do we need to include season here?
        team_stats_df: pd.DataFrame = normalized_games_no_dcs_df.groupby("team").agg(
            team=("team", "first"),
            player=("player", "first"),
            **AGG_NORMALIZED_STATS_KWARGS,  # type: ignore
        )

        # needed for the FIP calculation
        league_era = (
            9 * np.sum(team_stats_df["r"]) / np.sum(team_stats_df["innings_pitching"])
        )

        # actually compute any stats with multiple inputs
        annotate_computed_stats(team_stats_df, league_era=league_era)

        season_stats_to_write["season_team_stats"] |= team_stats_df.to_dict(  # type: ignore
            orient="index"
        )

        #
        # build season_stats.season_team_records
        #

        standings_df = gsheets.json_as_df(
            args.g_sheets_dir / f"{league}__Standings.json",
            str_cols=["ELO", "GB", "Team Name"],
        )
        clean_standings(standings_df, league)

        season_stats_to_write["season_team_records"] |= standings_df.to_dict(orient="index")  # type: ignore

    # playoffs stats collection
    for league in LEAGUES:
        print(f"Running season {args.season} stats for {league} playoff games...")
        df = gsheets.json_as_df(
            args.g_sheets_dir / f"{league}__Playoffs.json",
            str_cols=["Away", "Home", "Round"],
        )

        df["season"] = args.season

        dcs_and_bad_data = gsheets.find_games_with_bad_data(df)
        if len(dcs_and_bad_data) > 0:
            missing_games_to_write[league]["playoffs"] += dcs_and_bad_data.to_dict(
                orient="records"
            )

        # note this returns a normalized DataFrame AND mutates the input
        normalized_df, annotated_df = gsheets.normalize_season_games_spreadsheet(
            df, active_players, league, playoffs=True
        )

        #
        # build season_stats_playoffs_game_results
        #

        season_stats_to_write["playoffs_game_results"] += make_game_results(annotated_df)  # type: ignore

        #
        # build season_stats.playoffs_team_stats
        #

        # remove DCs and games with missing data first. we don't want to include games with missing stats when we collect computed stats
        # we know either 'week' or 'round' will be na, so ignore those columns when determining which games are DCs
        all_columns_but_week_or_round = [
            col for col in normalized_df.columns if col not in ["week", "round"]
        ]
        normalized_games_no_dcs_df = normalized_df.dropna(
            subset=all_columns_but_week_or_round
        )

        # a query that sums raw numbers for each team for the season
        # TODO do we need to include season here?
        team_stats_df: pd.DataFrame = normalized_games_no_dcs_df.groupby("team").agg(
            team=("team", "first"),
            player=("player", "first"),
            **AGG_NORMALIZED_STATS_KWARGS,  # type: ignore
        )

        # needed for the FIP calculation
        league_era = (
            9 * np.sum(team_stats_df["r"]) / np.sum(team_stats_df["innings_pitching"])
        )

        # actually compute any stats with multiple inputs
        annotate_computed_stats(team_stats_df, league_era=league_era)

        season_stats_to_write["playoffs_team_stats"] |= team_stats_df.to_dict(  # type: ignore
            orient="index"
        )

        #
        # build season_stats.playoffs_team_records
        #

        season_stats_to_write["playoffs_team_records"] = collect_playoffs_team_records(
            normalized_df
        )

    with open("deleteme.json", "w") as f:
        f.write(json.dumps(season_stats_to_write))

    # career stats are generated across all leagues

    # get regular season stats for all players across all leagues and all seasons and all head to heads
    [xbl_h2h_df, aaa_h2h_df, aa_h2h_df] = [
        prep_career_stats(args, all_players, league) for league in LEAGUES
    ]

    all_games_ever_df = pd.concat([xbl_h2h_df, aaa_h2h_df, aa_h2h_df])
    all_time_stats_df = all_games_ever_df.groupby("player").agg(**AGG_NORMALIZED_STATS_KWARGS)  # type: ignore

    annotate_computed_stats(all_time_stats_df, league_era=1.0)

    # career_data = build_career_stats(args, all_players)

    # career_json = args.save_dir / "careers.json"
    # print(f"Writing {career_json}...")
    # with open(career_json, "w") as f:
    #     f.write(json.dumps(career_data))

    # career_file_size = os.path.getsize(career_json)
    # print(f"careers.json filesize: {math.floor(career_file_size / 1000000)}MB")

    # TODO write these somewhere


if __name__ == "__main__":
    parser = arg_parser()
    args = parser.parse_args(namespace=StatsAggNamespace)
    err = main(args)
    if err is not None:
        parser.error(err)
