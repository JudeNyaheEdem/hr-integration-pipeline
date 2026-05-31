import pandas as pd
from rapidfuzz import fuzz
from src.config import CONFIG


def add_source_priority(df: pd.DataFrame) -> pd.DataFrame:

    df["source_priority"] = df["source"].map(
        CONFIG["source_priority"]).fillna(99)
    return df


def dedup_exact_id(df: pd.DataFrame) -> pd.DataFrame:

    df = df.sort_values(
        by=["employee_id", "source_priority"]
    )

    df["dedup_method"] = "exact_id"

    df = df.drop_duplicates(
        subset=["employee_id"],
        keep="first"
    )

    return df


def fuzzy_match_candidates(df: pd.DataFrame, threshold=88):

    if not {"first_name", "last_name", "hire_date"}.issubset(df.columns):
        return pd.DataFrame()

    df = df.copy()

    df["full_name"] = (
        df["first_name"].astype(str) + " " + df["last_name"].astype(str)
    )

    df["hire_date"] = pd.to_datetime(df["hire_date"], errors="coerce")

    candidates = []

    for i, row_i in df.iterrows():
        for j, row_j in df.iterrows():

            if i >= j:
                continue

            name_score = fuzz.ratio(
                row_i["full_name"],
                row_j["full_name"]
            )

            if pd.notna(row_i["hire_date"]) and pd.notna(row_j["hire_date"]):
                date_diff = abs(
                    (row_i["hire_date"] - row_j["hire_date"]).days
                )
            else:
                date_diff = 999

            if name_score >= threshold and date_diff <= 30:

                candidates.append({
                    "record_1_id": row_i["employee_id"],
                    "record_2_id": row_j["employee_id"],
                    "similarity_score": name_score,
                    "hire_date_diff_days": date_diff,
                    "recommended_action": "manual_review"
                })

    return pd.DataFrame(candidates)


def dedup_email(df: pd.DataFrame) -> pd.DataFrame:

    if "email" not in df.columns:
        return df

    df = df.sort_values(
        by=["email", "source_priority"]
    )

    df["dedup_method"] = df["dedup_method"].fillna("single_source")

    df = df.drop_duplicates(
        subset=["email"],
        keep="first"
    )

    df["dedup_method"] = df["dedup_method"]+"_email_match"

    return df


def detect_ghost_employees(payroll_df, hris_df):

    ghost = payroll_df[
        ~payroll_df["employee_id"].isin(hris_df("employee_id"))
    ].copy()

    ghost["ghost_flag_reason"] = "No HRIS match"

    return ghost


def add_provenance(df: pd.DataFrame) -> pd.DataFrame:

    df["source_systems"] = df["source"]

    return df
