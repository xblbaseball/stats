from typing_extensions import TypedDict
from typing import List, TypeAlias


League: TypeAlias = str

class GameResults(TypedDict):
    """what happened in a single game"""

    season: int
    league: League
    home_team: str
    away_team: str
    home_player: str
    away_player: str
    home_score: int
    away_score: int
    run_rule: bool
    winner: str
    innings: int
    away_ab: int
    away_r: int
    away_hits: int
    away_hr: int
    away_rbi: int
    away_bb: int
    away_so: int
    away_e: int
    home_ab: int
    home_r: int
    home_hits: int
    home_hr: int
    home_rbi: int
    home_bb: int
    home_so: int
    home_e: int
    week: int | None
    round: int | None