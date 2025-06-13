import pandas as pd
from typing import List

from .models import GameResults, League

def collect_game_results(playoffs: bool, box_score_data: pd.DataFrame, league: str):
    """convert the Box%20Score and Playoffs spreadsheet tabs into structured data"""
    game_results: List[GameResults] = []

    for game in box_score_data.itertuples():
        try:
            results = {
                "away_team": game.away,
                "home_team": game.home,
                "away_score": game.a_score,
                "home_score": game.h_score,
                "innings": game.innings,
                "winner": game.away if game.a_score > game.h_score else game.home,
                "run_rule": game.innings <= 8.0,
                "league": league,
            }
            if playoffs:
                results["round"] = game[0]
            else:
                results["week"] = int(game[0])
        except ValueError as e:
            print("Something is horribly wrong with this game:")
            print(game)
            continue

        try:
            extra_stats = {
                "away_e": None if playoffs else int(game[5]),
                "home_e": None if playoffs else int(game[6]),
                # not all of these are always recorded. missing records are probably from disconnects
                "away_ab": maybe(game, get_col(6), int),
                "away_r": maybe(game, get_col(7), int),
                "away_hits": maybe(game, get_col(8), int),
                "away_hr": maybe(game, get_col(9), int),
                "away_rbi": maybe(game, get_col(10), int),
                "away_bb": maybe(game, get_col(11), int),
                "away_so": maybe(game, get_col(12), int),
                "home_ab": maybe(game, get_col(13), int),
                "home_r": maybe(game, get_col(14), int),
                "home_hits": maybe(game, get_col(15), int),
                "home_hr": maybe(game, get_col(16), int),
                "home_rbi": maybe(game, get_col(17), int),
                "home_bb": maybe(game, get_col(18), int),
                "home_so": maybe(game, get_col(19), int),
            }

            results |= extra_stats

        except ValueError as e:
            # some column is wrong in the extra stats. don't collect them
            pass

        game_results.append(results)

    return game_results