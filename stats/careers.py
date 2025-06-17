import pandas as pd


def career_cols_to_box_scores_cols(df: pd.DataFrame):
    """Update the CAREER_STATS DataFrame in place to match the columns in Box Scores (likewise for playoffs). Assumes column names have been standardized (see gsheets.py)

    Args:
        df DataFrame from Head to Head data"""
    df.rename(
        columns={
            "away_player": "away",
            "away_score": "a_score",
            "home_player": "home",
            "home_score": "h_score",
        },
        inplace=True,
    )
