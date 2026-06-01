import unicodedata
import pandas as pd
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


# Employee ID Standardization

def namespace_employee_ids(df, company_code):

    def format_id(identifier):
        if pd.isna(identifier):
            return identifier

        identifier = str(identifier).replace(",", "").strip()

        return f"{company_code}-{identifier}"

    df["employee_id"] = df["employee_id"].apply(format_id)
    df["manager_id"] = df["manager_id"].apply(format_id)

    return df


# Department Standardization

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


# Date Standardization

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

        df[col] = pd.to_datetime(
            df[col],
            errors="coerce"
        )

        df[f"{col}_is_invalid"] = (
            (df[col] < "1970-01-01") |
            (df[col] > today)
        )

    return df


# Payroll Standardization

def normalize_currency_and_salary(df):

    df["employee_id"] = (
        df["employee_id"]
        .astype(str)
        .str.replace(",", "", regex=False)
    )

    df["base_salary"] = (
        df["base_salary"]
        .astype(str)
        .str.replace(r"[^\d.]", "", regex=True)
    )

    df["base_salary"] = pd.to_numeric(
        df["base_salary"],
        errors="coerce"
    )

    df["currency"] = (
        df["currency"]
        .str.upper()
        .str.strip()
    )

    df["pay_frequency"] = (
        df["pay_frequency"]
        .str.lower()
        .str.strip()
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

    return df


# Pipeline Helpers

def clean_employee_data(df):

    df = clean_employee_names(df)
    df = standardize_departments(df)
    df = standardize_dates(df)

    return df


def clean_payroll_data(df):

    df = normalize_currency_and_salary(df)
    df = standardize_dates(df)

    return df
