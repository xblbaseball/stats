"""
Aggregate all the XBL stats that we can find into a clear, accessible set of high-level statistics. These statistics are at the level that you would want to put in the ticker for a sports broadcast. The script expects that you've already run scripts/get-sheets.py (or you've downloaded the same data with the same filenames some other way).

Usage:
    python stats.py --help
    python stats.py --season 18 # the season number is the current season
"""

import argparse
from collections import defaultdict
import copy
import json
import logging
import math
import os
from pathlib import Path
import shutil
import traceback
from typing import List

from models import *
from utils import *

# TODO keep an old json around per season. lets us show last season's stats at the beginning of next season
# TODO consistency between "so" and "k"

LEAGUES = ["XBL", "AAA", "AA"]

logger = logging.getLogger("stats/main")
logging.basicConfig(filename="main.log", level=logging.INFO)


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


def two_digits(x: int | float | None) -> int | float:
    if x is None:
        return None
    return round(x, 2)


def three_digits(x: int | float | None) -> int | float:
    if x is None:
        return None
    return round(x, 3)


def maybe(row: List[str], col: int, type: callable):
    """Do our best to get the stat. But it might be missing, in which case return None"""
    ret = None
    try:
        ret = type(row[col])
    except IndexError as e:
        # print(f"Failed to get col {col} from {row}")
        pass
    return ret


def sum_dict_tallies(*dicts: List[dict]):
    """given 2+ dicts with int or set keys, return a dict with the ints summed or sets combined"""

    # prune any Nones
    dicts = [d for d in dicts if d is not None]

    if len(dicts) == 0:
        return None

    if len(dicts) == 1:
        return dicts[0]

    result = {}
    for key in dicts[0].keys():
        if all([key in d for d in dicts]):
            if all([isinstance(d[key], int) for d in dicts]):
                result[key] = sum([d[key] for d in dicts])
            if all([isinstance(d[key], set) for d in dicts]):
                result[key] = set.union(*[d[key] for d in dicts])

    return result


def collect_team_records(
    league: str,
    standings_data: List[List[str]],
):
    """cleaned up team wins and losses for the regular season"""
    team_records: dict[str, SeasonTeamRecord] = {}

    # return a different row for AA
    get_row: int = lambda r: r + 2 if league == "AA" else r

    for row in standings_data[1:]:
        team = row[1]
        team_records[team] = {
            "team": team,
            "rank": int(row[0]),
            "ego_starting": int(row[2]) if league == "AA" else None,
            "ego_current": int(row[3]) if league == "AA" else None,
            "wins": int(row[get_row(2)]),
            "losses": int(row[get_row(3)]),
            "gb": 0.0 if row[get_row(4)] == "-" else float(row[get_row(4)]),
            "win_pct": float(row[get_row(5)]),
            "win_pct_vs_500": 0.0 if row[get_row(6)] == "-" else float(row[get_row(6)]),
            "sweeps_w": int(row[get_row(7)]),
            "splits": int(row[get_row(8)]),
            "sweeps_l": int(row[get_row(9)]),
            "sos": int(row[get_row(10)]),
            "elo": int(row[get_row(19)].replace(",", "")),
        }

    team_count = len(team_records)
    games_per_team = 2 * (team_count - 1)

    for team in team_records.keys():
        # I think Ws and Ls in the spreadsheet don't account for teams who drop?
        team_records[team]["remaining"] = max(
            games_per_team
            - (team_records[team]["wins"] + team_records[team]["losses"]),
            0,
        )

    return team_records


def collect_game_results(playoffs: bool, box_score_data: List[List[str]], league: str):
    """convert the Box%20Score and Playoffs spreadsheet tabs into structured data"""
    if playoffs:
        game_results: List[PlayoffsGameResults] = []
    else:
        game_results: List[SeasonGameResults] = []

    # regular season has errors but playoffs do not
    get_col = lambda c: c if playoffs else c + 2

    for game in box_score_data[1:]:
        try:
            away_team = game[1]
            home_team = game[4]
            away_score = int(game[2])
            home_score = int(game[3])
            innings = float(game[get_col(5)])
            results = {
                "away_team": away_team,
                "home_team": home_team,
                "away_score": away_score,
                "home_score": home_score,
                "innings": innings,
                "winner": away_team if away_score > home_score else home_team,
                "run_rule": innings <= 8.0,
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


def calc_stats_from_all_games(
    raw_stats: RawStats, league_era: float, team="", player=""
) -> TeamStats:
    """given everything a player/team did across all games, calculate stat lines"""
    per_9_hitting = lambda key, digits=3: (
        three_digits((raw_stats[key] / raw_stats["innings_hitting"]) * 9)
        if digits == 3
        else two_digits((raw_stats[key] / raw_stats["innings_hitting"]) * 9)
    )
    per_9_pitching = lambda key, digits=3: (
        three_digits((raw_stats[key] / raw_stats["innings_pitching"]) * 9)
        if digits == 3
        else two_digits((raw_stats[key] / raw_stats["innings_pitching"]) * 9)
    )

    # use Nones as blackholes. if any stat turns to None, it stays None without raising any errors
    for key in raw_stats.keys():
        if raw_stats[key] is None or isinstance(raw_stats[key], int):
            raw_stats[key] = SafeNum(raw_stats[key])

    stats: TeamStats = {
        "team": team,
        "player": player,
        # hitting
        "rs": raw_stats["r"],
        "rs9": per_9_hitting("r", 2),
        "ba": (three_digits(raw_stats["h"] / raw_stats["ab"])),
        "ab": raw_stats["ab"],
        "ab9": per_9_hitting("ab", 2),
        "h": raw_stats["h"],
        "h9": per_9_hitting("h"),
        "hr": raw_stats["hr"],
        "hr9": per_9_hitting("hr", 2),
        "abhr": (three_digits(raw_stats["ab"] / raw_stats["hr"])),
        "so": raw_stats["so"],
        "so9": per_9_hitting("so", 2),
        "bb": raw_stats["bb"],
        "bb9": per_9_hitting("bb", 2),
        "obp": three_digits(
            (raw_stats["h"] + raw_stats["bb"]) / (raw_stats["ab"] + raw_stats["bb"])
        ),
        "rc": (three_digits(raw_stats["h"] / raw_stats["r"])),
        "babip": three_digits(
            (raw_stats["h"] - raw_stats["hr"])
            / (raw_stats["ab"] - raw_stats["so"] - raw_stats["hr"])
        ),
        # pitching
        "ra": raw_stats["oppr"],
        "ra9": per_9_pitching("oppr", 2),
        "oppba": (three_digits(raw_stats["opph"] / raw_stats["oppab"])),
        "oppab9": per_9_pitching("oppab", 2),
        "opph": raw_stats["opph"],
        "opph9": per_9_pitching("opph", 2),
        "opphr": raw_stats["opphr"],
        "opphr9": per_9_pitching("opphr", 2),
        "oppabhr": (two_digits(raw_stats["ab"] / raw_stats["hr"])),
        "oppk": raw_stats["oppso"],
        "oppk9": per_9_pitching("oppso", 2),
        "oppbb": raw_stats["oppbb"],
        "oppbb9": per_9_pitching("oppbb", 2),
        "whip": two_digits(
            (raw_stats["opph"] + raw_stats["oppbb"]) / raw_stats["innings_pitching"]
        ),
        "lob": three_digits(
            (raw_stats["opph"] + raw_stats["oppbb"] - raw_stats["oppr"])
            / (raw_stats["opph"] + raw_stats["oppbb"] - 1.4 * raw_stats["opphr"])
        ),
        "e": None,
        # TODO is this right?
        "fip": two_digits(
            SafeNum(league_era)
            - (
                (
                    raw_stats["opphr"] * 13
                    + 3 * raw_stats["oppbb"]
                    - 2 * raw_stats["oppso"]
                )
                / raw_stats["innings_pitching"]
            )
        ),
        # mixed
        "rd": raw_stats["r"] - raw_stats["oppr"],
        # TODO is this right?
        "rd9": (two_digits(per_9_hitting("r") - per_9_pitching("oppr"))),
        "innings_played": (raw_stats["innings_hitting"] + raw_stats["innings_pitching"])
        / 2,
        "innings_game": two_digits(
            ((raw_stats["innings_hitting"] + raw_stats["innings_pitching"]) / 2)
            / raw_stats["games_played"]
        ),
        "wins": raw_stats["wins"],
        "losses": raw_stats["losses"],
        "wins_by_run_rule": raw_stats["wins_by_run_rule"],
        "losses_by_run_rule": raw_stats["losses_by_run_rule"],
    }

    if "seasons" in raw_stats:
        stats["seasons"] = sorted(list(raw_stats["seasons"]))

    return stats


def calc_team_stats(game_results: List[GameResults]):
    """do math to get stats about team performances over the games passed in to this function. we get a few stats that aren't in the spreadsheets"""

    stats_by_team: dict[str, TeamStats] = {}

    blank_team_stats_by_game: RawStats = {
        "innings_pitching": 0,
        "innings_hitting": 0,
        "wins": 0,
        "losses": 0,
        "wins_by_run_rule": 0,
        "losses_by_run_rule": 0,
        "ab": 0,
        "r": 0,
        "h": 0,
        "hr": 0,
        "rbi": 0,
        "bb": 0,
        "so": 0,
        "oppab": 0,
        "oppr": 0,
        "opph": 0,
        "opphr": 0,
        "opprbi": 0,
        "oppbb": 0,
        "oppso": 0,
        "games_played": 0,
    }

    raw_stats_by_team: dict[str, dict[str, int | float]] = {}

    league_runs = 0
    league_innings_hitting = 0

    # collect stats by team by looking at each game
    for game in game_results:
        away = game["away_team"]
        home = game["home_team"]
        if away not in raw_stats_by_team:
            raw_stats_by_team[away] = copy.deepcopy(blank_team_stats_by_game)
        if home not in raw_stats_by_team:
            raw_stats_by_team[home] = copy.deepcopy(blank_team_stats_by_game)

        if game["winner"] == away:
            raw_stats_by_team[away]["wins"] += 1
            raw_stats_by_team[home]["losses"] += 1
        else:
            raw_stats_by_team[away]["losses"] += 1
            raw_stats_by_team[home]["wins"] += 1

        if game["winner"] == away and game["run_rule"]:
            raw_stats_by_team[away]["wins_by_run_rule"] += 1
            raw_stats_by_team[home]["losses_by_run_rule"] += 1
        if game["winner"] == home and game["run_rule"]:
            raw_stats_by_team[home]["wins_by_run_rule"] += 1
            raw_stats_by_team[away]["losses_by_run_rule"] += 1

        if "away_ab" not in game or game["away_ab"] is None:
            # we're missing stats. don't count this game
            continue

        away_stats = copy.deepcopy(raw_stats_by_team[away])
        home_stats = copy.deepcopy(raw_stats_by_team[home])

        away_stats["innings_hitting"] += math.ceil(game["innings"])
        away_stats["innings_pitching"] += math.floor(game["innings"])
        home_stats["innings_hitting"] += math.floor(game["innings"])
        home_stats["innings_pitching"] += math.ceil(game["innings"])

        league_runs += game["away_r"]
        league_runs += game["home_r"]
        league_innings_hitting += away_stats["innings_hitting"]
        league_innings_hitting += home_stats["innings_hitting"]

        # capture away team stats
        away_stats["games_played"] += 1
        away_stats["ab"] += game["away_ab"]
        away_stats["r"] += game["away_r"]
        away_stats["h"] += game["away_hits"]
        away_stats["hr"] += game["away_hr"]
        away_stats["rbi"] += game["away_rbi"]
        away_stats["bb"] += game["away_bb"]
        away_stats["so"] += game["away_so"]
        away_stats["oppab"] += game["home_ab"]
        away_stats["oppr"] += game["home_r"]
        away_stats["opph"] += game["home_hits"]
        away_stats["opphr"] += game["home_hr"]
        away_stats["opprbi"] += game["home_rbi"]
        away_stats["oppbb"] += game["home_bb"]
        away_stats["oppso"] += game["home_so"]

        # capture home team stats
        home_stats["games_played"] += 1
        home_stats["ab"] += game["home_ab"]
        home_stats["r"] += game["home_r"]
        home_stats["h"] += game["home_hits"]
        home_stats["hr"] += game["home_hr"]
        home_stats["rbi"] += game["home_rbi"]
        home_stats["bb"] += game["home_bb"]
        home_stats["so"] += game["home_so"]
        home_stats["oppab"] += game["away_ab"]
        home_stats["oppr"] += game["away_r"]
        home_stats["opph"] += game["away_hits"]
        home_stats["opphr"] += game["away_hr"]
        home_stats["opprbi"] += game["away_rbi"]
        home_stats["oppbb"] += game["away_bb"]
        home_stats["oppso"] += game["away_so"]

        raw_stats_by_team[away] = away_stats
        raw_stats_by_team[home] = home_stats

    league_era = (
        three_digits(9 * league_runs / league_innings_hitting)
        # before the season starts, we have no innings hitting
        if league_innings_hitting > 0
        else 0.0
    )

    # do math to get aggregate stats
    for team in raw_stats_by_team.keys():
        raw_stats = raw_stats_by_team[team]
        stats_by_team[team] = calc_stats_from_all_games(
            raw_stats, league_era, team=team
        )

    return stats_by_team


def collect_playoffs_team_records(results: List[PlayoffsGameResults]):
    """figure out how each round of the playoffs is going for each team"""
    records_by_team: dict[str, PlayoffsTeamRecord] = {}

    default_round = {"wins": 0, "losses": 0, "remaining": 0}

    for game in results:
        away_team = game["away_team"]
        home_team = game["home_team"]
        this_round = game["round"]

        if home_team not in records_by_team:
            records_by_team[home_team] = {"team": home_team, "rounds": {}}

        if away_team not in records_by_team:
            records_by_team[away_team] = {"team": away_team, "rounds": {}}

        if this_round not in records_by_team[home_team]["rounds"]:
            records_by_team[home_team]["rounds"][this_round] = default_round | {
                "round": this_round,
                "team": home_team,
                "opponent": away_team,
            }

        if this_round not in records_by_team[away_team]["rounds"]:
            records_by_team[away_team]["rounds"][this_round] = default_round | {
                "round": this_round,
                "team": away_team,
                "opponent": home_team,
            }

        home_round_record = copy.deepcopy(
            records_by_team[home_team]["rounds"][this_round]
        )
        away_round_record = copy.deepcopy(
            records_by_team[away_team]["rounds"][this_round]
        )

        winner = away_team if game["away_score"] > game["home_score"] else home_team

        if winner == away_team:
            away_round_record["wins"] += 1
            home_round_record["losses"] += 1
        else:
            home_round_record["wins"] += 1
            away_round_record["losses"] += 1

        # TODO it'd be nice to have access to something that tells us how many games are in the series

        records_by_team[away_team]["rounds"][this_round] = away_round_record
        records_by_team[home_team]["rounds"][this_round] = home_round_record

    return records_by_team


def build_season_stats(league: str, g_sheets_dir: Path, season: int) -> SeasonStats:
    """parse JSONs from g sheets and collect season stats"""

    print(f"Running season {season} {league}...")
    data: SeasonStats = {
        "current_season": season,
        "season_team_records": {},
        "season_team_stats": {},
        "season_game_results": [],
        "playoffs_team_records": {},
        "playoffs_team_stats": {},
        "playoffs_game_results": [],
    }

    standings_data: List[List[str]] = None
    with open(g_sheets_dir.joinpath(f"{league}__Standings.json")) as f:
        raw_data = json.loads(f.read())
        standings_data = raw_data["values"]

    season_team_records = collect_team_records(league, standings_data)
    data["season_team_records"] = season_team_records

    season_scores_data = None
    with open(g_sheets_dir.joinpath(f"{league}__Box%20Scores.json")) as f:
        raw_data = json.loads(f.read())
        season_scores_data = raw_data["values"]

    season_game_results = collect_game_results(False, season_scores_data, league)
    data["season_game_results"] = season_game_results
    data["season_team_stats"] = calc_team_stats(season_game_results)

    playoffs_scores_data = None
    with open(g_sheets_dir.joinpath(f"{league}__Playoffs.json")) as f:
        raw_data = json.loads(f.read())
        playoffs_scores_data = raw_data["values"]

    playoffs_game_results = collect_game_results(True, playoffs_scores_data, league)
    data["playoffs_game_results"] = playoffs_game_results
    data["playoffs_team_records"] = collect_playoffs_team_records(playoffs_game_results)

    # no spreadsheet has these. we have to run the numbers ourselves
    data["playoffs_team_stats"] = calc_team_stats(playoffs_game_results)

    return data


def collect_players(
    xbl_abbrev_data: List[List[str]],
    aaa_abbrev_data: List[List[str]],
    aa_abbrev_data: List[List[str]],
) -> dict[str, Player]:
    """Find everyone who ever played in any league and when they played"""
    players: dict[str, Player] = {}

    for row in xbl_abbrev_data[1:]:
        season = int(row[0])
        team_name = row[1]
        team_abbrev = row[2]
        player = row[3]

        if player not in players:
            players[player] = {"player": player, "teams": []}

        players[player]["teams"].append(
            {
                "player": player,
                "team_name": team_name,
                "team_abbrev": team_abbrev,
                "league": "XBL",
                "season": season,
            }
        )

    for row in aaa_abbrev_data[1:]:
        season = int(row[0])
        team_name = row[1]
        team_abbrev = row[2]
        player = row[3]

        if player not in players:
            players[player] = {"player": player, "teams": []}

        players[player]["teams"].append(
            {
                "player": player,
                "team_name": team_name,
                "team_abbrev": team_abbrev,
                "league": "AAA",
                "season": season,
            }
        )

    for row in aa_abbrev_data[1:]:
        season = int(row[0])
        team_name = row[1]
        team_abbrev = row[2]
        player = row[3]

        if player not in players:
            players[player] = {"player": player, "teams": []}

        players[player]["teams"].append(
            {
                "player": player,
                "team_name": team_name,
                "team_abbrev": team_abbrev,
                "league": "AA",
                "season": season,
            }
        )

    # sort teams in order of ascending season
    for player in players.keys():
        sorted_teams = sorted(players[player]["teams"], key=lambda team: team["season"])
        players[player]["teams"] = sorted_teams

    return players


def get_active_players(
    players: dict[str, Player], season: int
) -> dict[str, List[TeamSeason]]:
    """get the players (usernames) who are playing this season. assumes a player is only in 1 league per season"""

    active_players: dict[str, List[TeamSeason]] = {"XBL": [], "AAA": [], "AA": []}

    for player_name in players:
        for team in players[player_name]["teams"]:
            if team["season"] == season:
                active_players[team["league"]].append(team)
                break

    return active_players


def get_career_games_results(
    game: List[str], playoffs: bool, league: str
) -> GameResults:
    away_player = game[2]
    home_player = game[7]

    try:
        season = game[0]
        week_or_round = game[1]
        away_score = int(game[4])
        home_score = int(game[5])
        innings = maybe(game, 10, float)
        results: GameResults = {
            "season": season,
            "league": league,
            "away_player": away_player,
            "home_player": home_player,
            "away_score": away_score,
            "home_score": home_score,
            "innings": innings,
            "winner": away_player if away_score > home_score else home_player,
            "run_rule": True if innings is not None and innings <= 8.0 else False,
        }
        if playoffs:
            results["round"] = week_or_round
        else:
            results["week"] = int(week_or_round)
    except ValueError as e:
        # something went horribly wrong. don't count this game
        logger.warning(
            f"Missing critical information from the following game. It could not be recorded. {', '.join(game)}"
        )
        return None

    try:
        extra_stats = {
            "away_e": None if playoffs else maybe(game, 8, int),
            "home_e": None if playoffs else maybe(game, 9, int),
            # not all of these are always recorded. missing records are probably from disconnects
            "away_ab": maybe(game, 11, int),
            "away_r": maybe(game, 12, int),
            "away_hits": maybe(game, 13, int),
            "away_hr": maybe(game, 14, int),
            "away_rbi": maybe(game, 15, int),
            "away_bb": maybe(game, 16, int),
            "away_so": maybe(game, 17, int),
            "home_ab": maybe(game, 18, int),
            "home_r": maybe(game, 19, int),
            "home_hits": maybe(game, 20, int),
            "home_hr": maybe(game, 21, int),
            "home_rbi": maybe(game, 22, int),
            "home_bb": maybe(game, 23, int),
            "home_so": maybe(game, 24, int),
        }

        results |= extra_stats

    except ValueError as e:
        # some column is wrong in the extra stats. don't collect them
        pass

    return results


def collect_career_performances_and_head_to_head(
    playoffs: bool,
    xbl_head_to_head_data: List[List[str]],
    aaa_head_to_head_data: List[List[str]],
    aa_head_to_head_data: List[List[str]],
) -> List[HeadToHead]:
    """get career stats and head to head stats"""
    regular_season: dict[str, CareerSeasonPerformance] = {}
    regular_season_head_to_head: dict[str, dict[str, HeadToHead]] = {}

    # get nicely formatted results
    all_xbl_games = [
        results
        for game in xbl_head_to_head_data[1:]
        if (results := get_career_games_results(game, playoffs, "XBL")) is not None
    ]
    all_aaa_games = [
        results
        for game in aaa_head_to_head_data[1:]
        if (results := get_career_games_results(game, playoffs, "AAA")) is not None
    ]
    all_aa_games = [
        results
        for game in aa_head_to_head_data[1:]
        if (results := get_career_games_results(game, playoffs, "AA")) is not None
    ]

    all_game_results = [*all_xbl_games, *all_aaa_games, *all_aa_games]

    blank_team_stats_by_game: TeamStats = {
        "innings_pitching": 0,
        "innings_hitting": 0,
        "wins": 0,
        "losses": 0,
        "wins_by_run_rule": 0,
        "losses_by_run_rule": 0,
        "ab": 0,
        "r": 0,
        "h": 0,
        "hr": 0,
        "rbi": 0,
        "bb": 0,
        "so": 0,
        "oppab": 0,
        "oppr": 0,
        "opph": 0,
        "opphr": 0,
        "opprbi": 0,
        "oppbb": 0,
        "oppso": 0,
        "games_played": 0,
        # not in TeamStats. only used temporarily
        "seasons": set(),
    }

    xbl_league_runs = 0
    aaa_league_runs = 0
    aa_league_runs = 0
    xbl_league_innings_hitting = 0
    aaa_league_innings_hitting = 0
    aa_league_innings_hitting = 0
    runs_by_league_by_season = {
        "XBL": defaultdict(int),
        "AAA": defaultdict(int),
        "AA": defaultdict(int),
    }
    innings_hitting_by_league_by_season = {
        "XBL": defaultdict(int),
        "AAA": defaultdict(int),
        "AA": defaultdict(int),
    }

    # {player: {season_X: league, season_Y: league}}
    league_for_season_by_player: dict[str, dict[str, str]] = {}

    # {player: {season_X: stats, season_y: stats}}
    raw_stats_for_season_by_player: dict[str, dict[str, RawStats]] = {}

    # keyed on player names
    xbl_raw_stats_by_player: dict[str, RawStats] = {}
    aaa_raw_stats_by_player: dict[str, RawStats] = {}
    aa_raw_stats_by_player: dict[str, RawStats] = {}

    # keyed on player names in alphabetical order
    head_to_head_by_players = {}

    # sum per games stats to get all-time stats per player and head-to-head stats per matchup in the same loop. we have to:
    #   * translate game home/away to each player
    #   * sort stats by league
    #   * sort stats by matchups
    #   * collect league ERAs to calculate FIP
    #
    # we also skip any games for players who are inactive, or matchups when 1 or both players are inactive
    for game in all_game_results:
        away_player = game["away_player"]
        home_player = game["home_player"]
        season = game["season"]
        # this will eventually be turned into JSON, and TS/lodash is weird about dict keys that are numbers
        season_key = f"season_{season}"
        league = game["league"]

        is_xbl_game = league == "XBL"
        is_aaa_game = league == "AAA"
        is_aa_game = league == "AA"

        # track who played which season when
        if away_player not in league_for_season_by_player:
            league_for_season_by_player[away_player] = {}
        if home_player not in league_for_season_by_player:
            league_for_season_by_player[home_player] = {}

        league_for_season_by_player[away_player][season_key] = league
        league_for_season_by_player[home_player][season_key] = league

        # prep to track stats by season for each player
        if away_player not in raw_stats_for_season_by_player:
            raw_stats_for_season_by_player[away_player] = {}
        if home_player not in raw_stats_for_season_by_player:
            raw_stats_for_season_by_player[home_player] = {}

        if season_key not in raw_stats_for_season_by_player[away_player]:
            raw_stats_for_season_by_player[away_player][season_key] = copy.deepcopy(
                blank_team_stats_by_game
            )
        if season_key not in raw_stats_for_season_by_player[home_player]:
            raw_stats_for_season_by_player[home_player][season_key] = copy.deepcopy(
                blank_team_stats_by_game
            )

        # prep for tracking stats by league for each player
        if is_xbl_game and away_player not in xbl_raw_stats_by_player:
            xbl_raw_stats_by_player[away_player] = copy.deepcopy(
                blank_team_stats_by_game
            )
        elif is_aaa_game and away_player not in aaa_raw_stats_by_player:
            aaa_raw_stats_by_player[away_player] = copy.deepcopy(
                blank_team_stats_by_game
            )
        elif is_aa_game and away_player not in aa_raw_stats_by_player:
            aa_raw_stats_by_player[away_player] = copy.deepcopy(
                blank_team_stats_by_game
            )

        if is_xbl_game and home_player not in xbl_raw_stats_by_player:
            xbl_raw_stats_by_player[home_player] = copy.deepcopy(
                blank_team_stats_by_game
            )
        elif is_aaa_game and home_player not in aaa_raw_stats_by_player:
            aaa_raw_stats_by_player[home_player] = copy.deepcopy(
                blank_team_stats_by_game
            )
        elif is_aa_game and home_player not in aa_raw_stats_by_player:
            aa_raw_stats_by_player[home_player] = copy.deepcopy(
                blank_team_stats_by_game
            )

        # alphabetical tuple of player names
        h2h_key = tuple(sorted((home_player, away_player)))
        (player_a, player_z) = h2h_key

        # use this to figure out how players in raw_stats and h2h_stats translate
        player_a_is_away = player_a == away_player

        # where we'll store h2h stats
        if player_a not in head_to_head_by_players:
            head_to_head_by_players[player_a] = {}
        if player_z not in head_to_head_by_players[player_a]:
            head_to_head_by_players[player_a][player_z] = {
                "player_a": player_a,
                "player_z": player_z,
                "player_a_raw_stats": copy.deepcopy(blank_team_stats_by_game),
                "player_z_raw_stats": copy.deepcopy(blank_team_stats_by_game),
            }

        def add_to_player_season(player: str, key: str, value: int):
            raw_stats_for_season_by_player[player][season_key][key] += value

        def add_to_player_h2h(away: bool, key: str, value: int):
            """if we need h2h for this matchup, translate home and away into player_a and player_z and record the stat"""
            if (away and player_a_is_away) or (not away and not player_a_is_away):
                head_to_head_by_players[player_a][player_z]["player_a_raw_stats"][
                    key
                ] += value
            else:
                head_to_head_by_players[player_a][player_z]["player_z_raw_stats"][
                    key
                ] += value

        def add_to_away(key: str, value: int):
            """record an away team stat if the away player is currently playing"""
            if is_xbl_game:
                xbl_raw_stats_by_player[away_player][key] += value
            elif is_aaa_game:
                aaa_raw_stats_by_player[away_player][key] += value
            elif is_aa_game:
                aa_raw_stats_by_player[away_player][key] += value
            add_to_player_h2h(True, key, value)
            add_to_player_season(away_player, key, value)

        def add_to_home(key: str, value: int):
            """record a home team stat if the home player is currently playing"""
            if is_xbl_game:
                xbl_raw_stats_by_player[home_player][key] += value
            elif is_aaa_game:
                aaa_raw_stats_by_player[home_player][key] += value
            elif is_aa_game:
                aa_raw_stats_by_player[home_player][key] += value
            add_to_player_h2h(False, key, value)
            add_to_player_season(home_player, key, value)

        if game["winner"] == away_player:
            add_to_away("wins", 1)
            add_to_home("losses", 1)
        else:
            add_to_home("wins", 1)
            add_to_away("losses", 1)

        if game["run_rule"]:
            if game["winner"] == away_player:
                add_to_away("wins_by_run_rule", 1)
                add_to_home("losses_by_run_rule", 1)
            if game["winner"] == home_player:
                add_to_home("wins_by_run_rule", 1)
                add_to_away("losses_by_run_rule", 1)

        # record which seasons were played
        if is_xbl_game:
            xbl_raw_stats_by_player[home_player]["seasons"].add(season)
            xbl_raw_stats_by_player[away_player]["seasons"].add(season)
        if is_aaa_game:
            aaa_raw_stats_by_player[home_player]["seasons"].add(season)
            aaa_raw_stats_by_player[away_player]["seasons"].add(season)
        if is_aa_game:
            aa_raw_stats_by_player[home_player]["seasons"].add(season)
            aa_raw_stats_by_player[away_player]["seasons"].add(season)
        head_to_head_by_players[player_a][player_z]["player_a_raw_stats"][
            "seasons"
        ].add(season)
        head_to_head_by_players[player_a][player_z]["player_z_raw_stats"][
            "seasons"
        ].add(season)
        raw_stats_for_season_by_player[away_player][season_key]["seasons"].add(season)
        raw_stats_for_season_by_player[home_player][season_key]["seasons"].add(season)

        if "away_ab" not in game or game["away_ab"] is None:
            # we're missing stats. don't count this game
            continue

        if game["innings"] is not None:
            add_to_away("innings_hitting", math.ceil(game["innings"]))
            add_to_away("innings_pitching", math.floor(game["innings"]))
            add_to_home("innings_hitting", math.floor(game["innings"]))
            add_to_home("innings_pitching", math.ceil(game["innings"]))

            runs_by_league_by_season[league][season_key] += game["away_r"]
            runs_by_league_by_season[league][season_key] += game["home_r"]
            innings_hitting_by_league_by_season[league][season_key] += math.ceil(
                game["innings"]
            )
            innings_hitting_by_league_by_season[league][season_key] += math.floor(
                game["innings"]
            )

            # use these to calculate the league ERA
            if is_xbl_game:
                xbl_league_runs += game["away_r"]
                xbl_league_runs += game["home_r"]
                xbl_league_innings_hitting += math.ceil(game["innings"])
                xbl_league_innings_hitting += math.floor(game["innings"])
            if is_aaa_game:
                aaa_league_runs += game["away_r"]
                aaa_league_runs += game["home_r"]
                aaa_league_innings_hitting += math.ceil(game["innings"])
                aaa_league_innings_hitting += math.floor(game["innings"])
            if is_aa_game:
                aa_league_runs += game["away_r"]
                aa_league_runs += game["home_r"]
                aa_league_innings_hitting += math.ceil(game["innings"])
                aa_league_innings_hitting += math.floor(game["innings"])

        # capture away team stats
        add_to_away("games_played", 1)
        add_to_away("ab", game["away_ab"])
        add_to_away("r", game["away_r"])
        add_to_away("h", game["away_hits"])
        add_to_away("hr", game["away_hr"])
        add_to_away("rbi", game["away_rbi"])
        add_to_away("bb", game["away_bb"])
        add_to_away("so", game["away_so"])
        add_to_away("oppab", game["home_ab"])
        add_to_away("oppr", game["home_r"])
        add_to_away("opph", game["home_hits"])
        add_to_away("opphr", game["home_hr"])
        add_to_away("opprbi", game["home_rbi"])
        add_to_away("oppbb", game["home_bb"])
        add_to_away("oppso", game["home_so"])

        # capture home team stats
        add_to_home("games_played", 1)
        add_to_home("ab", game["home_ab"])
        add_to_home("r", game["home_r"])
        add_to_home("h", game["home_hits"])
        add_to_home("hr", game["home_hr"])
        add_to_home("rbi", game["home_rbi"])
        add_to_home("bb", game["home_bb"])
        add_to_home("so", game["home_so"])
        add_to_home("oppab", game["away_ab"])
        add_to_home("oppr", game["away_r"])
        add_to_home("opph", game["away_hits"])
        add_to_home("opphr", game["away_hr"])
        add_to_home("opprbi", game["away_rbi"])
        add_to_home("oppbb", game["away_bb"])
        add_to_home("oppso", game["away_so"])

    xbl_league_era = three_digits(9 * xbl_league_runs / xbl_league_innings_hitting)
    aaa_league_era = three_digits(9 * aaa_league_runs / aaa_league_innings_hitting)
    aa_league_era = three_digits(9 * aa_league_runs / aa_league_innings_hitting)
    all_time_league_era = three_digits(
        9
        * sum([xbl_league_runs, aaa_league_runs, aa_league_runs])
        / sum(
            [
                xbl_league_innings_hitting,
                aaa_league_innings_hitting,
                aaa_league_innings_hitting,
            ],
        )
    )
    era_by_league_by_season = {
        "XBL": dict(
            [
                (
                    season_key,
                    three_digits(
                        9
                        * runs_by_league_by_season["XBL"][season_key]
                        / innings_hitting_by_league_by_season["XBL"][season_key]
                    ),
                )
                for season_key in runs_by_league_by_season["XBL"].keys()
            ]
        ),
        "AAA": dict(
            [
                (
                    season_key,
                    three_digits(
                        9
                        * runs_by_league_by_season["AAA"][season_key]
                        / innings_hitting_by_league_by_season["AAA"][season_key]
                    ),
                )
                for season_key in runs_by_league_by_season["AAA"].keys()
            ]
        ),
        "AA": dict(
            [
                (
                    season_key,
                    three_digits(
                        9
                        * runs_by_league_by_season["AA"][season_key]
                        / innings_hitting_by_league_by_season["AA"][season_key]
                    ),
                )
                for season_key in runs_by_league_by_season["AA"].keys()
            ]
        ),
    }

    all_time_raw_stats_by_player = {
        player: sum_dict_tallies(
            xbl_raw_stats_by_player.get(player, None),
            aaa_raw_stats_by_player.get(player, None),
            aa_raw_stats_by_player.get(player, None),
        )
        for player in list(
            set(
                [
                    *xbl_raw_stats_by_player.keys(),
                    *aaa_raw_stats_by_player.keys(),
                    *aa_raw_stats_by_player.keys(),
                ]
            )
        )
    }

    # do math to get career performance stats
    for player in all_time_raw_stats_by_player.keys():
        regular_season[player] = {
            "player": player,
            "all_time": calc_stats_from_all_games(
                all_time_raw_stats_by_player[player], all_time_league_era, player=player
            ),
            "by_league": {
                "XBL": (
                    calc_stats_from_all_games(
                        xbl_raw_stats_by_player[player], xbl_league_era, player=player
                    )
                    if player in xbl_raw_stats_by_player
                    else None
                ),
                "AAA": (
                    calc_stats_from_all_games(
                        aaa_raw_stats_by_player[player], aaa_league_era, player=player
                    )
                    if player in aaa_raw_stats_by_player
                    else None
                ),
                "AA": (
                    calc_stats_from_all_games(
                        aa_raw_stats_by_player[player], aa_league_era, player=player
                    )
                    if player in aa_raw_stats_by_player
                    else None
                ),
            },
            # dict of {season_1: [list of games in that season]}
            # but only if the player played in that season
            "by_season": dict(
                [
                    (
                        # use keys that don't start with numbers because javascript (and lodash) gets weird about keying a dict with numbers
                        sk,
                        calc_stats_from_all_games(
                            raw_stats_for_season_by_player[player][sk],
                            era_by_league_by_season[
                                league_for_season_by_player[player][sk]
                            ][sk],
                            player=player,
                        ),
                    )
                    # use XBL as a key because XBL has been played every season
                    for sk in era_by_league_by_season["XBL"].keys()
                    # don't include seasons where someone didn't play
                    if sk in raw_stats_for_season_by_player[player]
                ]
            ),
        }

    # do math to get head to head stats
    for player_a in head_to_head_by_players.keys():
        for player_z in head_to_head_by_players[player_a]:
            if player_a not in regular_season_head_to_head:
                regular_season_head_to_head[player_a] = {}

            raw_stats_a = head_to_head_by_players[player_a][player_z][
                "player_a_raw_stats"
            ]
            raw_stats_z = head_to_head_by_players[player_a][player_z][
                "player_z_raw_stats"
            ]

            try:
                regular_season_head_to_head[player_a][player_z] = {
                    "player_a": player_a,
                    "player_z": player_z,
                    "player_a_stats": calc_stats_from_all_games(
                        raw_stats_a,
                        all_time_league_era,
                        player=player_a,
                    ),
                    "player_z_stats": calc_stats_from_all_games(
                        raw_stats_z,
                        all_time_league_era,
                        player=player_z,
                    ),
                }
            except Exception as e:
                print(player_a, player_z)
                print(e)
                traceback.print_exc()

    # TODO still need to get playoffs player series wins, losses, championships, etc

    return regular_season, regular_season_head_to_head


def build_career_stats(g_sheets_dir: Path, season: int):
    print(f"Running career stats...")
    data: CareerStats = {
        "all_players": {},
        "active_players": {},
        "regular_season": {},
        "regular_season_head_to_head": [],
        "playoffs": {},
        "playoffs_head_to_head": [],
    }

    xbl_abbrev_data = None
    with open(
        g_sheets_dir.joinpath("CAREER_STATS__XBL%20Team%20Abbreviations.json")
    ) as f:
        raw_data = json.loads(f.read())
        xbl_abbrev_data = raw_data["values"]

    aaa_abbrev_data = None
    with open(
        g_sheets_dir.joinpath("CAREER_STATS__AAA%20Team%20Abbreviations.json")
    ) as f:
        raw_data = json.loads(f.read())
        aaa_abbrev_data = raw_data["values"]

    aa_abbrev_data = None
    with open(
        g_sheets_dir.joinpath(f"CAREER_STATS__AA%20Team%20Abbreviations.json")
    ) as f:
        raw_data = json.loads(f.read())
        aa_abbrev_data = raw_data["values"]

    print("Finding who played which season...")
    all_players = collect_players(xbl_abbrev_data, aaa_abbrev_data, aa_abbrev_data)
    data["all_players"] = all_players

    active_players = get_active_players(all_players, season)
    data["active_players"] = active_players

    xbl_head_to_head_data = None
    with open(g_sheets_dir.joinpath("CAREER_STATS__XBL%20Head%20to%20Head.json")) as f:
        raw_data = json.loads(f.read())
        xbl_head_to_head_data = raw_data["values"]

    aaa_head_to_head_data = None
    with open(g_sheets_dir.joinpath("CAREER_STATS__AAA%20Head%20to%20Head.json")) as f:
        raw_data = json.loads(f.read())
        aaa_head_to_head_data = raw_data["values"]

    aa_head_to_head_data = None
    with open(g_sheets_dir.joinpath("CAREER_STATS__AA%20Head%20to%20Head.json")) as f:
        raw_data = json.loads(f.read())
        aa_head_to_head_data = raw_data["values"]

    print(
        "Tabulating career regular season stats, stats by season, stats by league, and head to head performances..."
    )
    regular_season, regular_season_head_to_head = (
        collect_career_performances_and_head_to_head(
            False,
            xbl_head_to_head_data,
            aaa_head_to_head_data,
            aa_head_to_head_data,
        )
    )

    data["regular_season"] = regular_season
    data["regular_season_head_to_head"] = regular_season_head_to_head

    xbl_playoffs_head_to_head_data = None
    with open(g_sheets_dir.joinpath("PLAYOFF_STATS__XBL%20Head%20to%20Head.json")) as f:
        raw_data = json.loads(f.read())
        xbl_playoffs_head_to_head_data = raw_data["values"]

    aaa_playoffs_head_to_head_data = None
    with open(g_sheets_dir.joinpath("PLAYOFF_STATS__AAA%20Head%20to%20Head.json")) as f:
        raw_data = json.loads(f.read())
        aaa_playoffs_head_to_head_data = raw_data["values"]

    aa_playoffs_head_to_head_data = None
    with open(g_sheets_dir.joinpath("PLAYOFF_STATS__AA%20Head%20to%20Head.json")) as f:
        raw_data = json.loads(f.read())
        aa_playoffs_head_to_head_data = raw_data["values"]

    print("Tabulating career playoffs stats and head to head performances...")
    playoffs, playoffs_head_to_head = collect_career_performances_and_head_to_head(
        True,
        xbl_playoffs_head_to_head_data,
        aaa_playoffs_head_to_head_data,
        aa_playoffs_head_to_head_data,
    )

    data["playoffs"] = playoffs
    data["playoffs_head_to_head"] = playoffs_head_to_head

    return data


def main(args: StatsAggNamespace):
    if not args.g_sheets_dir.exists():
        raise Exception(
            f"Missing data from Google Sheets. Cannot find {args.g_sheets_dir}. Plesae double check `--g-sheets-dir' or run `get-sheets.py' first"
        )

    season_data = {
        league: build_season_stats(league, args.g_sheets_dir, args.season)
        for league in LEAGUES
    }

    for league in LEAGUES:
        season_json = args.save_dir.joinpath(f"{league}__s{args.season}.json")
        print(f"Writing {season_json}...")
        with open(season_json, "w") as f:
            f.write(json.dumps(season_data[league], cls=SafeEncoder))

        shutil.copy(season_json, args.save_dir.joinpath(f"{league}.json"))

    career_data = build_career_stats(args.g_sheets_dir, args.season)

    career_json = args.save_dir.joinpath("careers.json")
    print(f"Writing {career_json}...")
    with open(career_json, "w") as f:
        f.write(json.dumps(career_data, cls=SafeEncoder))

    career_file_size = os.path.getsize(career_json)
    print(f"careers.json filesize: {math.floor(career_file_size / 1000000)}MB")

    if len(args.query) > 0:
        try:
            current = None
            if args.query[0] == "season":
                current = season_data
            elif args.query[0] == "career":
                current = career_data
            else:
                return f"`--query' must begin with either 'season' or 'career'"

            for part in args.query[1:]:
                current = current.get(part, {})
            return current
        except (KeyError, TypeError, IndexError) as e:
            return f"--query `{', '.join(args.query)}' cannot be found."

    return None


if __name__ == "__main__":
    parser = arg_parser()
    args: StatsAggNamespace = parser.parse_args()
    err = main(args)
    if err is not None:
        parser.error(err)
