import unicodedata
import pandas as pd
import numpy as np
from src.config import CONFIG


# Name Standardization

def normalize_unicode(value):
    if pd.isna(value):
        return value

    return (
        unicodedata.normalize("NFKD", str(value))
        .encode("ascii", "ignore")
        .decode("utf-8")
    )


def clean_employee_names(df):

    df["first_name"] = (
        df["first_name"]
        .astype(str)
        .str.strip()
        .apply(normalize_unicode)
        .str.title()
    )

    df["last_name"] = (
        df["last_name"]
        .astype(str)
        .str.strip()
        .apply(normalize_unicode)
        .str.title()
    )

    return df


def namespace_employee_ids(df, company_code):

    def format_id(identifier):
        if pd.isna(identifier):
            return identifier

        identifier = str(identifier).strip()

        if identifier.upper().startswith("GHOST"):
            return identifier

        digits = "".join(
            ch for ch in identifier
            if ch.isdigit()
        )

        if not digits:
            return pd.NA

        return f"{company_code}-{digits.zfill(6)}"

    df["employee_id"] = df["employee_id"].apply(format_id)

    if "manager_id" in df.columns:
        df["manager_id"] = df["manager_id"].apply(format_id)

    return df


def clean_acquiredco_noise(df):

    if "employee_id" in df.columns:
        df = df[~df["employee_id"].astype(str).str.contains("DUP", na=False)]

    return df


def standardize_emails(df):
    df["email"] = (
        df["email"]
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"\s+", "", regex=True)
        .replace({
            "nan": np.nan,
            "none": np.nan,
            "": np.nan
        })
    )

    return df


def standardize_departments(df):

    df["department"] = (
        df["department"]
        .astype("string")
        .str.strip()
        .str.lower()
        .str.replace(r"\s+", " ", regex=True)
        .str.title()
    )

    return df


def standardize_dates(df):

    date_columns = [
        "hire_date",
        "effective_date",
        "enrollment_date"
    ]

    today = pd.Timestamp.today()

    for col in date_columns:

        if col not in df.columns:
            continue

        df[col] = pd.to_datetime(df[col], errors="coerce")

        df[f"{col}_is_invalid"] = (
            (df[col] < "1970-01-01") |
            (df[col] > today)
        )

    return df


def normalize_currency_and_salary(df):

    df["employee_id"] = (
        df["employee_id"]
        .astype("string")
        .str.replace(",", "", regex=False)
    )

    df["base_salary"] = (
        df["base_salary"]
        .astype("string")
        .str.replace(r"[$£€,]", "", regex=True)
    )

    df["base_salary"] = pd.to_numeric(
        df["base_salary"],
        errors="coerce"
    )

    df["currency"] = (
        df["currency"]
        .astype("string")
        .str.upper()
        .str.strip()
    )

    df["pay_frequency"] = (
        df["pay_frequency"]
        .astype(str)
        .str.lower()
        .str.strip()
        .replace({
            "monthly": "monthly",
            "bi weekly": "bi-weekly",
            "biweekly": "bi-weekly",
            "bi-weekly": "bi-weekly",
            "annual": "annual"
        })
    )

    df["salary_annual_local"] = (
        df["base_salary"]
        * df["pay_frequency"]
        .map(CONFIG["pay_multipliers"])
        .fillna(1)
    )

    df["salary_usd_annual"] = (
        df["salary_annual_local"]
        * df["currency"]
        .map(CONFIG["exchange_rates"])
        .fillna(1)
    )

    df["salary_usd_annual"] = pd.to_numeric(
        df["salary_usd_annual"],
        errors="coerce"
    )

    return df


def standardize_employment_type(df):

    mapping = {
        "FT": "Full-Time",
        "PT": "Part-Time",
        "FULL-TIME": "Full-Time",
        "PART-TIME": "Part-Time",
        "CONTRACTOR": "Contractor",
        "CONTRACT": "Contractor"
    }

    df["employment_type"] = (
        df["employment_type"]
        .astype("string")
        .str.strip()
        .str.upper()
        .replace(mapping)
    )

    return df


def clean_employee_data(df):

    df = clean_employee_names(df)
    df = standardize_emails(df)
    df = clean_acquiredco_noise(df)
    df = standardize_departments(df)
    df = standardize_employment_type(df)
    df = standardize_dates(df)

    return df


def clean_payroll_data(df):

    df = normalize_currency_and_salary(df)
    df = standardize_dates(df)

    return df


def clean_benefits_data(df):

    df = standardize_dates(df)

    return df
