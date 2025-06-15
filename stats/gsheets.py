import json
from typing import Any, List
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
    df = pd.DataFrame(values[1:])
    columns = [
        str(col).lower().strip().replace(" ", "_").replace(".", "") for col in values[0]
    ]
    df.columns = columns

    # fix types
    numeric_cols = [col for col in columns if col not in str_cols]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    if str_cols:
        df[str_cols] = df[str_cols].astype("string")

    return df
