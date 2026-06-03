from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd

from src.config import CONFIG
from src.utils import logger

COLORBLIND_PALETTE = CONFIG["colorblind_palette"]


def generate_eda_report(
    employee_df: pd.DataFrame,
    benefits_df: pd.DataFrame,
    quality_report_df: pd.DataFrame,
    output_path
):
    logger.info("Generating EDA report")

    plt.rcParams.update({
        "font.size": 12,
        "axes.titlesize": 14,
        "axes.labelsize": 12,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10
    })

    fig, axes = plt.subplots(
        3,
        2,
        figsize=(24, 18)
    )

    fig.suptitle(
        "GlobalTech HR Integration Report",
        fontsize=24,
        fontweight="bold"
    )

    # Headcount by Department

    dept_counts = (
        employee_df["department"]
        .dropna()
        .value_counts()
        .sort_values()
    )

    dept_counts.plot.barh(
        ax=axes[0, 0],
        color=COLORBLIND_PALETTE[0]
    )

    axes[0, 0].set_title(
        "Headcount by Department"
    )
    axes[0, 0].set_xlabel(
        "Employees"
    )
    axes[0, 0].set_ylabel(
        "Department"
    )
    axes[0, 0].text(
        0.01,
        -0.28,
        "Source: Unified Employee Dataset",
        transform=axes[0, 0].transAxes
    )

    # Headcount by Country

    country_counts = (
        employee_df["country"]
        .dropna()
        .value_counts()
        .head(15)
    )

    country_counts.plot.bar(
        ax=axes[0, 1],
        color=COLORBLIND_PALETTE[1]
    )

    axes[0, 1].set_title(
        "Headcount by Country"
    )
    axes[0, 1].set_xlabel(
        "Country"
    )
    axes[0, 1].set_ylabel(
        "Employees"
    )
    axes[0, 1].tick_params(
        axis="x",
        rotation=90
    )
    axes[0, 1].text(
        0.01,
        -0.28,
        "Source: Unified Employee Dataset",
        transform=axes[0, 1].transAxes
    )

    # Salary Distribution by Employment Type

    salary_df = employee_df.dropna(
        subset=["salary_usd_annual"]
    )

    salary_df.boxplot(
        column="salary_usd_annual",
        by="employment_type",
        ax=axes[1, 0]
    )

    axes[1, 0].set_title(
        "Salary Distribution by Employment Type"
    )
    axes[1, 0].set_xlabel(
        "Employment Type"
    )
    axes[1, 0].set_ylabel(
        "Annual Salary (USD)"
    )

    axes[1, 0].text(
        0.01,
        -0.28,
        "Source: Payroll Dataset",
        transform=axes[1, 0].transAxes
    )

    fig.suptitle(
        "GlobalTech HR Integration Report",
        fontsize=24,
        fontweight="bold"
    )

    # Tenure Distribution

    today = pd.Timestamp.today()

    tenure_years = (
        today - pd.to_datetime(
            employee_df["hire_date"],
            errors="coerce"
        )
    ).dt.days / 365.25

    tenure_years.dropna().plot.hist(
        bins=20,
        ax=axes[1, 1],
        color=COLORBLIND_PALETTE[2]
    )

    axes[1, 1].set_title(
        "Tenure Distribution"
    )
    axes[1, 1].set_xlabel(
        "Years"
    )
    axes[1, 1].set_ylabel(
        "Employees"
    )

    axes[1, 1].text(
        0.01,
        -0.28,
        "Source: Unified Employee Dataset",
        transform=axes[1, 1].transAxes
    )

    # Benefits Enrollment Rate by Department

    benefits_joined = employee_df.merge(
        benefits_df[["employee_id"]],
        on="employee_id",
        how="left",
        indicator=True
    )

    benefits_joined["enrolled"] = (
        benefits_joined["_merge"] == "both"
    )

    enrollment_rate = (
        benefits_joined
        .groupby("department")["enrolled"]
        .mean()
        .sort_values()
        * 100
    )

    enrollment_rate.plot.barh(
        ax=axes[2, 0],
        color=COLORBLIND_PALETTE[3]
    )

    axes[2, 0].set_title(
        "Benefits Enrollment Rate by Department"
    )
    axes[2, 0].set_xlabel(
        "Enrollment Rate (%)"
    )
    axes[2, 0].set_ylabel(
        "Department"
    )

    axes[2, 0].text(
        0.01,
        -0.28,
        "Source: Benefits Enrollment Dataset",
        transform=axes[2, 0].transAxes
    )

    # Data Quality Summary

    quality_report_df.plot(
        x="check",
        y=["passed", "failed"],
        kind="barh",
        ax=axes[2, 1],
        color=[
            COLORBLIND_PALETTE[4],
            COLORBLIND_PALETTE[5]
        ]
    )

    axes[2, 1].set_title(
        "Data Quality Summary"
    )
    axes[2, 1].set_xlabel(
        "Record Count"
    )
    axes[2, 1].set_ylabel(
        "Validation Check"
    )

    axes[2, 1].text(
        0.01,
        -0.28,
        "Source: Validation Report",
        transform=axes[2, 1].transAxes
    )

    # Footer

    fig.text(
        0.99,
        0.01,
        (
            f"Generated: "
            f"{datetime.now():%Y-%m-%d %H:%M:%S}"
        ),
        ha="right"
    )

    plt.tight_layout(
        rect=[0, 0.03, 1, 0.96]
    )

    output_file = output_path / "eda_report.png"

    plt.savefig(
        output_file,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    logger.info(
        f"EDA report saved to {output_file}"
    )
