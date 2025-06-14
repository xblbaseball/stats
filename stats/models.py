from typing_extensions import TypedDict
from typing import List, TypeAlias


League: TypeAlias = str


class TeamSeason(TypedDict):
    """pairing between a person and a season in XBL"""

    player: str
    team_name: str
    team_abbrev: str
    league: League
    season: int


class Player(TypedDict):
    """someone who played in XBL"""

    player: str
    teams: List[TeamSeason]
