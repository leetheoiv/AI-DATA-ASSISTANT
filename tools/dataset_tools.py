import requests
import os
import json
from io import StringIO
import pandas as pd
import numpy as np
import requests
from langchain.tools import tool

def _load_dataframe(path_or_url: str) -> pd.DataFrame:
    """Helper: load CSV or JSON from local path or URL."""
    if path_or_url.lower().endswith((".csv", ".tsv")) or path_or_url.startswith("http"):
        try:
            return pd.read_csv(path_or_url)
        except Exception:
            # fallback: fetch via requests then read
            r = requests.get(path_or_url)
            r.raise_for_status()
            return pd.read_csv(StringIO(r.text))
    if path_or_url.lower().endswith(".json"):
        try:
            return pd.read_json(path_or_url)
        except Exception:
            r = requests.get(path_or_url)
            r.raise_for_status()
            return pd.read_json(StringIO(r.text))
    # final attempt: let pandas try to infer
    return pd.read_csv(path_or_url)

@tool("get_dataset_structure", description="Return dataset structure: name, rows, columns, dtypes, and shape for a CSV/JSON path or URL.")
def get_dataset_structure(path: str) -> dict:
    """
    path: local path or http(s) URL to a CSV or JSON dataset.
    Returns a dict with dataset_name, rows, columns_count, columns (list of {name,dtype}), and shape.
    """
    if not path:
        return {"error": "path is required"}
    try:
        df = _load_dataframe(path)
    except Exception as e:
        return {"error": f"failed to load dataset: {e}"}

    dataset_name = os.path.basename(path) or path
    rows, cols = df.shape
    columns = []
    for col, dtype in df.dtypes.items():
        columns.append({"name": str(col), "dtype": str(dtype)})
    return {
        "dataset_name": dataset_name,
        "rows": int(rows),
        "columns_count": int(cols),
        "columns": columns,
        "shape": [int(rows), int(cols)],
    }

@tool("get_dataset_statistics", description="Return statistics for numerical and categorical columns for a CSV/JSON path or URL.")
def get_dataset_statistics(path: str, max_unique_values: int = 50) -> dict:
    """
    path: local path or http(s) URL to a CSV or JSON dataset.
    max_unique_values: limit number of unique value entries returned for categorical columns.
    Returns per-column statistics:
      - numerical: mean, median, std, min, max, count, missing
      - categorical: unique_count, top_values (value -> count), missing
    """
    if not path:
        return {"error": "path is required"}
    try:
        df = _load_dataframe(path)
    except Exception as e:
        return {"error": f"failed to load dataset: {e}"}

    stats = {"numerical": {}, "categorical": {}}
    # numerical columns
    num_cols = df.select_dtypes(include=[np.number]).columns
    for col in num_cols:
        series = df[col]
        count = int(series.count())
        missing = int(series.isna().sum())
        # use .astype(float) to ensure json-serializable floats
        try:
            mean = float(series.mean())
        except Exception:
            mean = None
        try:
            median = float(series.median())
        except Exception:
            median = None
        try:
            std = float(series.std())
        except Exception:
            std = None
        try:
            amin = float(series.min()) if count > 0 else None
            amax = float(series.max()) if count > 0 else None
        except Exception:
            amin = amax = None
        stats["numerical"][str(col)] = {
            "count": count,
            "missing": missing,
            "mean": mean,
            "median": median,
            "std": std,
            "min": amin,
            "max": amax,
        }

    # categorical / object columns
    cat_cols = df.select_dtypes(include=["object", "category", "bool"]).columns
    for col in cat_cols:
        series = df[col].astype(object)
        missing = int(series.isna().sum())
        unique_count = int(series.nunique(dropna=True))
        value_counts = series.value_counts(dropna=True)
        top = value_counts.head(max_unique_values).to_dict()
        # convert numpy ints to int for JSON
        top_clean = {str(k): int(v) for k, v in top.items()}
        stats["categorical"][str(col)] = {
            "unique_count": unique_count,
            "top_values": top_clean,
            "missing": missing,
        }

    return {
        "dataset": os.path.basename(path) or path,
        "shape": [int(df.shape[0]), int(df.shape[1])],
        "statistics":stats
    }