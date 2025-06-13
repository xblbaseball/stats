import json
import pandas as pd
from pathlib import Path

def as_df(path_to_json: Path, str_cols=[]) -> pd.DataFrame:
    """Return a DataFrame with cleaned up column names. Cases are lowered, spaces are turned into `_`, and periods are removed. E.g. `A. AB` turns into `a_ab`

    Args:
        path_to_json Path
        str_cols these columns should be treated as strings and not coerced to numeric
    """
    # read data
    with open(path_to_json, 'r') as f:
        raw_data = json.loads(f.read())

    # make the dataframe
    df = pd.DataFrame(raw_data["values"][1:])
    columns = [col.lower().replace(" ", "_").replace(".", "") for col in raw_data["values"][0]]
    df.columns = columns

    # fix types
    numeric_cols = [col for col in columns if col not in str_cols]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='raise')
    if str_cols:
        df[str_cols] = df[str_cols].astype("string")

    return df
