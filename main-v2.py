import argparse
import numpy as np
from pathlib import Path
from typing import List

from stats import gsheets
from stats.games import agg_team_stats, annotate_game_results


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
    aa_box_scores_df = gsheets.as_df(
        args.g_sheets_dir / "AA__Box%20Scores.json", str_cols=["away", "home", "week"]
    )

    annotate_game_results(aa_box_scores_df, "AA", False)
    stats_by_team = agg_team_stats(aa_box_scores_df)
    print(stats_by_team)


if __name__ == "__main__":
    parser = arg_parser()
    args = parser.parse_args(namespace=StatsAggNamespace)
    err = main(args)
    if err is not None:
        parser.error(err)
