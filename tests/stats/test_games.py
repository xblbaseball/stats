import pandas as pd
import unittest

from stats.games import agg_team_stats, annotate_game_results, annotate_computed_stats


class TestGames(unittest.TestCase):
    def test_mix_of_good_and_dc(self):
        columns = [
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
        box_scores_df = pd.DataFrame(
            [
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
                [
                    1,
                    "hippos",
                    1,
                    2,
                    "alligators",
                    0,
                    0,
                    9,
                    30,
                    1,
                    1,
                    1,
                    0,
                    1,
                    10,
                    30,
                    2,
                    2,
                    2,
                    0,
                    4,
                    12,
                ],
            ],
            columns=columns,
        )

        annotate_game_results(box_scores_df, False)
        team_stats_df = agg_team_stats(box_scores_df)
        annotate_computed_stats(team_stats_df, league="TEST", league_era=1.0)

        self.assertAlmostEqual(
            team_stats_df.loc["hippos"].ba,
            1 / 30,
            msg="Hippos batted 1/30 in the game that wasn't a DC",
        )
