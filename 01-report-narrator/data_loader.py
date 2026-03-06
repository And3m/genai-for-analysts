"""
Data loading and statistics computation module.
"""

import pandas as pd
import numpy as np


def load_file(uploaded_file) -> pd.DataFrame:
    """Load CSV or Excel file from a Streamlit UploadedFile object."""
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    elif name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)
    else:
        raise ValueError(f"Unsupported file type: {name}")


def _detect_date_column(df: pd.DataFrame) -> str | None:
    """
    Return the name of a date/time column if one can be identified.
    Checks column names first, then tries to parse object columns as dates.
    """
    date_keywords = ("date", "month", "year", "period", "week", "quarter", "time")
    for col in df.columns:
        if any(kw in col.lower() for kw in date_keywords):
            return col
    # Try to parse object columns as dates
    for col in df.select_dtypes(include=["object"]).columns:
        try:
            parsed = pd.to_datetime(df[col], errors="coerce")
            if parsed.notna().sum() / len(df) > 0.8:
                return col
        except Exception:
            continue
    return None


def compute_stats(df: pd.DataFrame) -> dict:
    """
    Compute summary statistics from a DataFrame.

    Returns a dictionary with:
    - Shape, columns, missing values
    - Numeric column summaries (mean, min, max, trend using date-sorted order)
    - Top categorical values
    - Grouped summaries: numeric totals/means broken down by each categorical column
    """
    # Sort by date column if one exists, so trend direction is meaningful
    date_col = _detect_date_column(df)
    if date_col:
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.sort_values(date_col)

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = [
        c for c in df.select_dtypes(include=["object", "category"]).columns
        if c != date_col
    ]

    stats: dict = {
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": list(df.columns),
        "date_column": date_col,
        "missing_values": {k: int(v) for k, v in df.isnull().sum().items() if v > 0},
        "numeric_summary": {},
        "categorical_summary": {},
        "grouped_summary": {},
    }

    # --- Numeric summaries ---
    for col in numeric_cols:
        first_val = df[col].dropna().iloc[0] if len(df[col].dropna()) > 0 else None
        last_val = df[col].dropna().iloc[-1] if len(df[col].dropna()) > 0 else None

        def _f(v) -> float:
            return round(float(v), 2)

        col_stats: dict = {
            "total": _f(df[col].sum()),
            "mean": _f(df[col].mean()),
            "min": _f(df[col].min()),
            "max": _f(df[col].max()),
            "std": _f(df[col].std()),
        }

        if first_val is not None and last_val is not None and first_val != 0 and not np.isnan(float(first_val)):
            col_stats["first_value"] = _f(first_val)
            col_stats["last_value"] = _f(last_val)
            col_stats["pct_change_total"] = _f(
                ((last_val - first_val) / abs(first_val)) * 100
            )

        stats["numeric_summary"][col] = col_stats

    # --- Categorical summaries ---
    for col in categorical_cols[:5]:
        top_values = df[col].value_counts().head(5).to_dict()
        stats["categorical_summary"][col] = {
            "unique_count": int(df[col].nunique()),
            "top_values": {str(k): int(v) for k, v in top_values.items()},
        }

    # --- Grouped summaries: numeric aggregates broken down by categorical col ---
    # Only use the first categorical column to avoid bloating the prompt
    if categorical_cols and numeric_cols:
        group_col = categorical_cols[0]
        try:
            grouped = df.groupby(group_col)[numeric_cols].sum().round(2)
            raw = grouped.to_dict(orient="index")
            # Convert all numpy types to native Python floats for JSON serialisation
            clean = {
                str(grp): {col: round(float(val), 2) for col, val in metrics.items()}
                for grp, metrics in raw.items()
            }
            stats["grouped_summary"] = {
                "group_by": group_col,
                "metric": "total",
                "data": clean,
            }
        except Exception:
            pass

    return stats
