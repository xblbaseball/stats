import json
from typing import Any, List
import numpy as np
import pandas as pd
from pathlib import Path


def json_as_df(path_to_json: Path, str_cols: List[str] = []) -> pd.DataFrame:
    """Return a DataFrame with cleaned up column names. Cases are lowered, spaces are turned into `_`, and periods are removed. E.g. `A. AB` turns into `a_ab`

    Args:
        path_to_json Path
        str_cols these columns should be treated as strings and not coerced to numeric
    """
    with open(path_to_json, "r") as f:
        raw_data = json.loads(f.read())

    return values_to_df(raw_data["values"], str_cols)


def values_to_df(values: List[List[Any]], str_cols: List[str] = []) -> pd.DataFrame:
    """Make the actual DataFrame. For column names, cases are lowered, spaces are turned into `_`, and periods are removed. E.g. `A. AB` turns into `a_ab`

    Args:
        values list of lists where the first element is the column labels
        str_cols these columns should be treated as strings and not coerced to numeric
    Returns:
        pd.DataFrame
    """
    df = pd.DataFrame(values[1:], columns=values[0])

    # fix types
    numeric_cols = [col for col in values[0] if col not in str_cols]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    if str_cols:
        df[str_cols] = df[str_cols].astype("string")

    # clean up the column names
    clean_col = lambda col: str(col).lower().strip().replace(" ", "_").replace(".", "")
    df.rename(columns={col: clean_col(col) for col in values[0]}, inplace=True)

    # sometimes LO leaves columns blank. get rid of them
    df.replace({"": np.nan}, inplace=True)
    df.dropna(axis=1, how="all", inplace=True)

    return df


def find_games_with_bad_data(df: pd.DataFrame) -> pd.DataFrame:
    """Return any games where there are NaNs recorded. These would be due to either DCs or bad inputs

    Args:
        df DataFrame of games pre-processing
    Returns:
        DataFrame
    """
    all_nan_rows = df[df.isna().any(axis=1)]
    # increment the index by 2 to match the rows in the spreadsheet (row 1 is the header, games start on row 2)
    all_nan_rows.index += 2

    return all_nan_rows
