import json
from pathlib import Path
import pandas as pd
import xml.etree.ElementTree as ET

from src.utils import logger

STANDARD_SCHEMA = [
    "employee_id",
    "first_name",
    "last_name",
    "email",
    "department",
    "job_title",
    "hire_date",
    "country",
    "employment_type",
    "manager_id",
    "source"
]

ACQUIREDCO_SCHEMA_MAP = {"employee_identifier": "employee_id", "name_first": "first_name", "name_last": "last_name", "contact_email": "email", "assignment_department": "department",
                         "assignment_role": "job_title", "assignment_hire_timestamp": "hire_date", "assignment_location": "country", "employment_type": "employment_type", "manager_employee_id": "manager_id"}


def write_dead_letter(dead_records: list, output_name: str) -> None:

    if not dead_records:
        return

    dead_df = pd.DataFrame(dead_records)

    output_path = Path("dead_letter_logs")
    output_path.mkdir(exist_ok=True)

    filepath = output_path / f"{output_name}.csv"

    logger.warning(
        f"Saved {len(dead_df)} dead-letter records to {filepath}"
    )


def file_exists(filepath: Path) -> bool:
    if not filepath.exists():
        logger.error(f"Missing source file: {filepath}")
    return True


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(r"[^\w]", "_", regex=True)
        .str.replace(r"_+", "_", regex=True)
        .str.strip("_")
    )
    return df


def enforce_schema(df: pd.DataFrame) -> pd.DataFrame:
    return df.reindex(columns=STANDARD_SCHEMA)


def ingest_globaltech_hris_csv(filepath: Path) -> pd.DataFrame:

    logger.info(f"Ingesting globaltech hris csv: {filepath}")
    if not file_exists(filepath):
        return pd.DataFrame(columns=STANDARD_SCHEMA)

    try:

        df = pd.read_csv(
            filepath,
            dtype={
                "employee_id": str,
                "manager_id": str
            },
            parse_dates=["hire_date"],
            na_values=["", "N/A", "null", "NULL", "none", "NaN"],
        )
        df = clean_columns(df)

        df["source"] = "globaltech_hris"

        df = enforce_schema(df)
        logger.info(f"Ingested {len(df)} records from globaltech hris CSV")
        return df

    except Exception as e:
        logger.exception(
            f"Failed ingesting GlobalTech HRIS: {e}"
        )

    return pd.DataFrame(columns=STANDARD_SCHEMA)


def ingest_acquiredco_api(
    filepath: Path,
    page_size: int = 500
) -> pd.DataFrame:

    logger.info(f"Ingesting AcquiredCo API JSON: {filepath}")

    if not file_exists(filepath):
        return pd.DataFrame(columns=STANDARD_SCHEMA)

    dead_records = []

    try:

        raw = json.loads(filepath.read_text())

        employees = raw.get("employees", [])

        pages = []

        for start_idx in range(0, len(employees), page_size):

            page = employees[start_idx:start_idx + page_size]

            try:

                page_df = pd.json_normalize(
                    page,
                    sep="_"
                )

                page_df = clean_columns(page_df)

                page_df = page_df.rename(
                    columns=ACQUIREDCO_SCHEMA_MAP
                )

                page_df["hire_date"] = pd.to_datetime(
                    page_df["hire_date"],
                    errors="coerce"
                )

                page_df["source"] = "acquiredco"

                page_df = enforce_schema(page_df)

                pages.append(page_df)

                logger.info(
                    f"Processed AcquiredCo page "
                    f"{start_idx // page_size + 1}"
                )

            except Exception as page_error:

                dead_records.append({
                    "page_start": start_idx,
                    "error": str(page_error)
                })

        write_dead_letter(
            dead_records,
            "acquiredco_dead_letters"
        )

        if pages:
            final_df = pd.concat(
                pages,
                ignore_index=True
            )
        else:
            final_df = pd.DataFrame(
                columns=STANDARD_SCHEMA
            )

        logger.info(
            f"Ingested {len(final_df)} AcquiredCo records"
        )

        return final_df

    except Exception as e:

        logger.exception(
            f"Failed ingesting AcquiredCo API: {e}"
        )

        return pd.DataFrame(columns=STANDARD_SCHEMA)


def ingest_payroll(filepath: Path) -> pd.DataFrame:
    if not file_exists(filepath):
        return pd.DataFrame()

    logger.info(f"Ingesting payroll data: {filepath}")

    dead_records = []

    try:
        df = pd.read_excel(filepath)
        df = clean_columns(df)
        df["employee_id"] = (
            df["employee_id"]
            .astype(str)
            .str.replace(",", "", regex=False)
        )
        df["effective_date"] = pd.to_datetime(
            df["effective_date"],
            errors="coerce"
        )

        df["source"] = "payroll"
        before_count = len(df)
        df = df.drop_duplicates()

        removed = before_count - len(df)

        logger.info(
            f"Removed {removed} duplicate payroll rows"
        )

        logger.info(f"Loaded {len(df)} payroll records")

        return df
    except Exception as e:
        dead_records.append({
            "file": str(filepath),
            "error": str(e)
        })

        write_dead_letter(
            dead_records,
            "payroll_dead_letters"
        )

        logger.exception(
            f"Failed ingesting payroll data: {e}"
        )

        return pd.DataFrame()


def ingest_benefits_xml(filepath: Path) -> pd.DataFrame:
    logger.info(f"Ingesting benefits XML: {filepath}")

    if not file_exists(filepath):
        return pd.DataFrame()

    records = []
    dead_records = []

    try:
        tree = ET.parse(filepath)
        root = tree.getroot()

        records = []

        for enrollment in root.findall("enrollment"):
            try:

                records.append({
                    "employee_id": enrollment.findtext("employee_id"),
                    "plan_type": enrollment.findtext("plan_type"),
                    "coverage_level": enrollment.findtext("coverage_level"),
                    "enrollment_date": enrollment.findtext("enrollment_date"),
                    "premium_employee": enrollment.findtext("premium_employee"),
                    "premium_employer": enrollment.findtext("premium_employer")
                })

            except Exception as record_error:

                dead_records.append({
                    "record": ET.tostring(
                        enrollment,
                        encoding="unicode"
                    ),
                    "error": str(record_error)
                })

        write_dead_letter(
            dead_records,
            "benefits_dead_letters"
        )

        df = pd.DataFrame(records)

        df = clean_columns(df)

        df["employee_id"] = df["employee_id"].astype(str)

        df["enrollment_date"] = pd.to_datetime(
            df["enrollment_date"],
            errors="coerce"
        )

        numeric_cols = [
            "premium_employee",
            "premium_employer"
        ]

        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col],
                    errors="coerce"
                )

        df["source"] = "benefits"

        logger.info(f"Loaded {len(df)} benefits enrollment records")

        return df

    except Exception as e:

        logger.exception(
            f"Failed ingesting benefits XML: {e}"
        )

        return pd.DataFrame()


def ingest_all_sources(input_dir: Path) -> dict:
    logger.info("Starting ingestion of all source systems")

    datasets = {
        "globaltech_hris": ingest_globaltech_hris_csv(
            input_dir / "globaltech_hris.csv"
        ),

        "acquiredco_hris": ingest_acquiredco_api(
            input_dir / "acquiredco_api.json"
        ),

        "payroll": ingest_payroll(
            input_dir / "payroll_data.xlsx"
        ),

        "benefits": ingest_benefits_xml(
            input_dir / "benefits_enrollment.xml"
        )
    }

    logger.info("Completed ingestion for all datasets")

    return datasets
