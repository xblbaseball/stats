import argparse
import numpy as np
from pathlib import Path
from typing import List

from stats import gsheets
from stats.games import agg_team_stats, annotate_computed_stats, annotate_game_results
from stats.players import aggregate_players, get_active_players
from stats.teams import clean_standings


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


def main(args: type[StatsAggNamespace]):
    aa_box_scores_df = gsheets.json_as_df(
        args.g_sheets_dir / "AA__Box%20Scores.json", str_cols=["away", "home", "week"]
    )

    annotate_game_results(aa_box_scores_df, False)
    team_stats_df = agg_team_stats(aa_box_scores_df)
    league_era = (
        9 * np.sum(team_stats_df["r"]) / np.sum(team_stats_df["innings_pitching"])
    )
    annotate_computed_stats(team_stats_df, league="AA", league_era=league_era)

    aa_standings_df = gsheets.json_as_df(
        args.g_sheets_dir / "AA__Standings.json", str_cols=["elo", "gb", "team_name"]
    )
    clean_standings(aa_standings_df)

    xbl_abbrev_df = gsheets.json_as_df(
        args.g_sheets_dir / "CAREER_STATS__XBL%20Team%20Abbreviations.json",
        str_cols=[
            "xbl_teams",
            "xbl_abbreviations",
            "player",
            "concatenate",
            "seasons_played",
        ],
    )
    aaa_abbrev_df = gsheets.json_as_df(
        args.g_sheets_dir / "CAREER_STATS__AAA%20Team%20Abbreviations.json",
        str_cols=[
            "aaa_teams",
            "aaa_abbreviations",
            "player",
            "concatenate",
            "seasons_played",
        ],
    )
    aa_abbrev_df = gsheets.json_as_df(
        args.g_sheets_dir / "CAREER_STATS__AA%20Team%20Abbreviations.json",
        str_cols=[
            "aa_teams",
            "aa_abbreviations",
            "player",
            "concatenate",
            "seasons_played",
        ],
    )

    all_players = aggregate_players(xbl_abbrev_df, aaa_abbrev_df, aa_abbrev_df)
    active_players = get_active_players(all_players, args.season)


if __name__ == "__main__":
    parser = arg_parser()
    args = parser.parse_args(namespace=StatsAggNamespace)
    err = main(args)
    if err is not None:
        parser.error(err)
