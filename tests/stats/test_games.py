import pandas as pd
import numpy as np
import unittest

from stats import gsheets
from stats.games import agg_team_stats, annotate_game_results, annotate_computed_stats

box_score_columns = [
    "week",
    "away",
    "a_score",
    "h_score",
    "home",
    "a_e",
    "h_e",
    "ip",
    "a_ab",
    "a_r",
    "a_h",
    "a_hr",
    "a_rbi",
    "a_bb",
    "a_so",
    "h_ab",
    "h_r",
    "h_h",
    "h_hr",
    "h_rbi",
    "h_bb",
    "h_so",
]


class TestGames(unittest.TestCase):
    def test_mix_of_good_and_dc(self):
        box_scores_df = pd.DataFrame(
            [
                # typical DC box score
                [
                    1,
                    "alligators",
                    1,
                    2,
                    "hippos",
                    0,
                    0,
                    9,
                ],
                # good
                [
                    1,  # week
                    "hippos",  # away
                    1,  # a_score
                    2,  # h_score
                    "alligators",  # home
                    0,  # a_e
                    0,  # h_e
                    9,  # ip
                    30,  # a_ab
                    1,  # a_r
                    1,  # a_h
                    1,  # a_hr
                    0,  # a_rbi
                    1,  # a_bb
                    10,  # a_so
                    30,  # h_ab
                    2,  # h_r
                    2,  # h_h
                    2,  # h_hr
                    0,  # h_rbi
                    4,  # h_bb
                    12,  # h_so
                ],
            ],
            columns=box_score_columns,
        )

        annotate_game_results(box_scores_df, False)
        team_stats_df = agg_team_stats(box_scores_df)
        annotate_computed_stats(team_stats_df, league="TEST", league_era=1.0)

        ba: float = team_stats_df.at["hippos", "ba"]

        self.assertAlmostEqual(
            ba,
            1 / 30,
            msg="hippos batted 1/30 in the game that wasn't a DC",
        )

    def test_garbage_in(self):
        box_scores_df = gsheets.values_to_df(
            [
                box_score_columns,
                # garbage
                [
                    1,  # week
                    "alligators",  # away
                    1,  # a_score
                    2,  # h_score
                    "hippos",  # home
                    0,  # a_e
                    0,  # h_e
                    9,  # ip
                    "bad entry",  # a_ab
                    1,  # a_r
                    1,  # a_h
                    1,  # a_hr
                    0,  # a_rbi
                    1,  # a_bb
                    10,  # a_so
                    30,  # h_ab
                    2,  # h_r
                    2,  # h_h
                    2,  # h_hr
                    0,  # h_rbi
                    4,  # h_bb
                    12,  # h_so
                ],
                # good
                [
                    1,  # week
                    "hippos",  # away
                    1,  # a_score
                    2,  # h_score
                    "alligators",  # home
                    0,  # a_e
                    0,  # h_e
                    9,  # ip
                    30,  # a_ab
                    1,  # a_r
                    1,  # a_h
                    1,  # a_hr
                    0,  # a_rbi
                    1,  # a_bb
                    10,  # a_so
                    30,  # h_ab
                    2,  # h_r
                    2,  # h_h
                    2,  # h_hr
                    0,  # h_rbi
                    4,  # h_bb
                    12,  # h_so
                ],
            ],
            str_cols=["away", "home"],
        )

        annotate_game_results(box_scores_df, False)
        team_stats_df = agg_team_stats(box_scores_df)
        annotate_computed_stats(team_stats_df, league="TEST", league_era=1.0)

        ba: float = team_stats_df.at["alligators", "ba"]

        self.assertAlmostEqual(
            ba,
            3 / 30,
            msg="alligators had 3 hits and 30 known ABs (one game is missing ABs)",
        )
