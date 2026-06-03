from pathlib import Path
import pandas as pd

from src.config import CONFIG
from src.utils import logger

from src.ingestion import ingest_all_sources
from src.cleaning import (
    clean_employee_data,
    clean_payroll_data,
    namespace_employee_ids
)
from src.deduplication import deduplicate, detect_ghost_employees
from src.validation import run_quality_checks
from src.visualization import generate_eda_report


def run_pipeline():
    logger.info("===== STARTING GLOBALTECH HR PIPELINE =====")

    logger.info("Ingesting raw data sources")

    datasets = ingest_all_sources(CONFIG["input_dir"])

    globaltech_df = datasets["globaltech_hris"]
    acquiredco_df = datasets["acquiredco_hris"]
    payroll_df = datasets["payroll"]
    benefits_df = datasets["benefits"]

    logger.info("Cleaning datasets")

    globaltech_df = clean_employee_data(globaltech_df)
    acquiredco_df = clean_employee_data(acquiredco_df)

    payroll_df = clean_payroll_data(payroll_df)

    globaltech_df = namespace_employee_ids(globaltech_df, "GT")
    acquiredco_df = namespace_employee_ids(acquiredco_df, "AC")
    payroll_df = namespace_employee_ids(payroll_df, "GT")
    benefits_df = namespace_employee_ids(benefits_df, "GT")

    logger.info("Merging HR datasets")

    globaltech_df["company_origin"] = "GlobalTech"
    acquiredco_df["company_origin"] = "AcquiredCo"

    employee_df = pd.concat(
        [globaltech_df, acquiredco_df],
        ignore_index=True
    )

    logger.info("Deduplicating employees")

    deduped_df, probable_matches = deduplicate(employee_df)

    logger.info("Detecting ghost employees")

    ghost_df = detect_ghost_employees(
        payroll_df,
        deduped_df
    )

    logger.info("Building golden employee dataset")

    payroll_enrichment = (
        payroll_df
        .sort_values("effective_date")
        .drop_duplicates(
            subset=["employee_id"],
            keep="last"
        )
        [
            [
                "employee_id",
                "salary_usd_annual"
            ]
        ]
    )

    benefits_enrichment = (
        benefits_df
        .groupby("employee_id")
        .size()
        .reset_index(name="benefit_count")
    )

    benefits_enrichment["benefits_enrolled"] = True

    golden_df = deduped_df.merge(
        payroll_enrichment,
        on="employee_id",
        how="left"
    )

    golden_df = golden_df.merge(
        benefits_enrichment[
            [
                "employee_id",
                "benefits_enrolled"
            ]
        ],
        on="employee_id",
        how="left"
    )

    golden_df["benefits_enrolled"] = (
        golden_df["benefits_enrolled"]
        .fillna(False)
    )

    print("<<<<<<<<<<<<", golden_df.columns)
    logger.info("Running data quality checks")

    quality_report = run_quality_checks(golden_df)

    failed_checks = (
        quality_report["status"] == "FAIL"
    ).sum()

    if failed_checks > 2:
        logger.error(
            "Pipeline halted: too many validation failures"
        )
        raise ValueError(
            "Data quality threshold breached"
        )

    logger.info("Generating EDA report")

    generate_eda_report(
        employee_df=golden_df,
        benefits_df=benefits_df,
        quality_report_df=quality_report,
        output_path=CONFIG["output_dir"]
    )

    logger.info("Saving outputs")

    output_dir = CONFIG["output_dir"]
    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    golden_df.to_parquet(
        output_dir / "golden_employee_dataset.parquet",

        index=False
    )

    ghost_df.to_csv(
        output_dir / "ghost_employee_report.csv",
        index=False
    )

    probable_matches.to_csv(
        output_dir / "probable_match_review.csv",
        index=False
    )

    quality_report.to_csv(
        output_dir / "validation_report.csv",
        index=False
    )

    quality_report.to_html(
        output_dir / "validation_report.html",
        index=False
    )

    logger.info(
        "===== PIPELINE COMPLETED SUCCESSFULLY ====="
    )

    return {
        "employees": golden_df,
        "ghost_employees": ghost_df,
        "probable_matches": probable_matches,
        "quality_report": quality_report
    }


if __name__ == "__main__":
    run_pipeline()
