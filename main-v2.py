import argparse
import json
import math
import numpy as np
import os
import pandas as pd
from pathlib import Path
from typing import List

from stats import gsheets
from stats.careers import career_cols_to_box_scores_cols
from stats.games import agg_team_stats, annotate_computed_stats, annotate_game_results
from stats.models import *
from stats.players import aggregate_players, get_active_players
from stats.teams import clean_standings

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


def prep_career_stats(args: type[StatsAggNamespace], league: str):
    h2h_df = gsheets.json_as_df(
        args.g_sheets_dir / f"CAREER_STATS__{league}%20Head%20to%20Head.json",
        str_cols=[
            "Week",
            "Away Player",
            "Away Result",
            "Home Player",
            "Home Result",
        ],
    )

    h2h_df["league"] = league

    # TODO try to multiindex on player, league, season?

    # make career data's columns match box scores so we can use the same methods
    career_cols_to_box_scores_cols(h2h_df)
    annotate_game_results(h2h_df, league, playoffs=False)

    return h2h_df


def build_career_stats(args: type[StatsAggNamespace]) -> CareerStats:
    """Get career stats for all players

    Args:
        args StatsAggNamespace
    Returns:
        CareerStats
    """

    print(f"Running career stats...")

    # what we'll eventually return
    data: CareerStats = {
        "all_players": {},
        "active_players": {},
        "regular_season": {},
        "regular_season_head_to_head": [],
        "playoffs": {},
        "playoffs_head_to_head": [],
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

    data["all_players"] = all_players
    data["active_players"] = active_players

    # get regular season stats for all players across all leagues and all seasons and all head to heads
    [xbl_h2h_df, aaa_h2h_df, aa_h2h_df] = [
        prep_career_stats(args, league) for league in LEAGUES
    ]

    all_games_ever_df = pd.concat([xbl_h2h_df, aaa_h2h_df, aa_h2h_df])

    # TODO filter on league, season, player, then agg stats

    # by_season_df = all_games_ever_df[
    #     (all_games_ever_df.season == 18) & (all_games_ever_df.away == "shameronium")
    # ]
    # print(by_season_df)

    by_season_df = all_games_ever_df.groupby("season")
    by_league_df = all_games_ever_df.groupby("league")

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

    return data


def main(args: type[StatsAggNamespace]):
    # regular season
    for league in LEAGUES:
        df = gsheets.json_as_df(
            args.g_sheets_dir / f"{league}__Box%20Scores.json",
            str_cols=["Away", "Home", "Week"],
        )

        df["season"] = args.season

        dcs_and_bad_data = gsheets.find_games_with_bad_data(df)
        if len(dcs_and_bad_data) > 0:
            print(f"These {league} games are missing data:")
            print(dcs_and_bad_data.to_dict(orient="records"))

        annotate_game_results(df, league, False)
        team_stats_df = agg_team_stats(df)
        league_era = (
            9 * np.sum(team_stats_df["r"]) / np.sum(team_stats_df["innings_pitching"])
        )
        annotate_computed_stats(team_stats_df, league_era=league_era)

        standings_df = gsheets.json_as_df(
            args.g_sheets_dir / f"{league}__Standings.json",
            str_cols=["ELO", "GB", "Team Name"],
        )
        clean_standings(standings_df, league)

        # TODO write these somewhere!

    career_data = build_career_stats(args)

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
