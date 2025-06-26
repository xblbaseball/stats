import pandas as pd


def clean_standings(standings_df: pd.DataFrame, league: str):
    """Update the DataFrame in place. Clean up standings data

    Args:
        standings_df DataFrame with data from a *__Standings.json spreadsheet
        league str
    """

    # ELOs over 1000 have commas that need to be removed... thanks Wishbone
    standings_df["elo"] = standings_df["elo"].apply(
        lambda elo: int(elo.replace(",", ""))
    )

    columns_to_rename = {
        "#": "rank",
        "1run": "one_run",
        "1run_w%": "win_pct_one_run",
        "inn/gm": "innings_per_game",
        "l": "losses",
        "l_sweeps": "sweeps_l",
        "team_name": "team",
        "w": "wins",
        "w_sweeps": "sweeps_w",
        "w%": "win_pct",
        "vs_500+": "win_pct_vs_500",
    }

    if league == "AA":
        columns_to_rename["current_ego"] = "ego_current"
        columns_to_rename["starting_ego"] = "ego_starting"

    standings_df.rename(
        columns=columns_to_rename,
        inplace=True,
        errors="raise",  # TOOD change to "ignore" for prod
    )

    # we get these from elsewhere
    # TODO would be cool to see if our calculated ra9, etc match these
    standings_df.drop(
        columns=[
            "inn_played",
            "rs/9",
            "ra/9",
            "diff/9",
            "runs_against",
            "run_diff",
            "runs_scored",
        ],
        inplace=True,
    )

    # create a column just to use as the index so we can get the team name in the record as well
    standings_df["team_index"] = standings_df["team"]
    standings_df.set_index("team_index", inplace=True)
