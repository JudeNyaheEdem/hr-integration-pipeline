import pandas as pd
from src.config import VALIDATION_RULES
from src.utils import logger
from datetime import datetime


class DataQualityValidator:

    def __init__(self, df: pd.DataFrame, threshold: float = 0.95):
        self.df = df
        self.threshold = threshold
        self.results = []
        self.n = len(df)

    def _record(self, check: str, description: str, failed: int, total: int):
        pass_rate = 1 - (failed/total) if total > 0 else 1.0

        result = {
            "check": check,
            "description": description,
            "total": total,
            "passed": total - failed,
            "failed": failed,
            "pass_rate": round(pass_rate, 4),
            "status": "PASS" if pass_rate >= self.threshold else "FAIL"
        }

        self.results.append(result)

        return result

    # basic requirement checks

    def check_not_null(self, column, description):
        failed = int(self.df[column].isna().sum())
        return self._record(f"NOT NULL:{column}", description, failed, self.n)

    def check_unique(self, column, description):
        non_null = self.df[column].dropna()
        failed = int(non_null.duplicated().sum())
        return self._record(f"UNIQUE: {column}", description, failed, len(non_null))

    def check_regex(self, column, pattern, description):
        non_null = self.df[column].dropna()
        failed = int((~non_null.astype(str).str.match(pattern)).sum())
        return self._record(f"REGEX: {column}", description, failed, len(non_null))

    def check_values_in_set(self, column, valid_values, description):
        non_null = self.df[column].dropna()
        failed = int((~non_null.isin(valid_values)).sum())
        return self._record(f"VALUES IN SET: {column}", description, failed, len(non_null))

    def check_date_range(self, column, min_date, max_date, description):
        non_null = self.df[column].dropna()

        in_range = non_null.between(
            pd.Timestamp(min_date),
            pd.Timestamp(max_date)
        )

        failed = int((~in_range).sum())
        return self._record(f"DATE RANGE: {column}", description, failed, len(non_null))

    def check_numeric_range(self, column, min_val, max_val, description):
        non_null = self.df[column].dropna()

        failed = int(((non_null < min_val) | (non_null > max_val)).sum())

        return self._record(
            f"NUMERIC RANGE: {column}",
            description,
            failed,
            len(non_null)
        )

    def check_referential_integrity(self, child_col, parent_col, description):

        child = self.df[child_col].dropna()
        parent = self.df[parent_col].dropna()

        valid_ids = set(parent)

        failed = int((~child.isin(valid_ids)).sum())

        return self._record(
            f"REFERENTIAL: {child_col}->{parent_col}",
            description,
            failed,
            len(child)
        )

    def generate_report(self) -> pd.DataFrame:

        report = pd.DataFrame(self.results)

        logger.info("=" * 60)
        logger.info("DATA QUALITY REPORT")
        logger.info("=" * 60)

        for r in self.results:
            icon = "✓" if r["status"] == "PASS" else "✗"
            logger.info(
                f"[{icon}] {r['check']} | "
                f"{r['pass_rate']:.1%} "
                f"({r['failed']} failed)"
            )

        overall = (report["status"] == "PASS").all()

        logger.info("=" * 60)
        logger.info(
            f"OVERALL: {'PASS ✓' if overall else 'FAIL ✗'}"
        )
        logger.info("=" * 60)

        return report


def run_quality_checks(df: pd.DataFrame, rules=VALIDATION_RULES):

    v = DataQualityValidator(df)

    # NOT NULL
    for col in rules.get("not_null", []):
        if col in df.columns:
            v.check_not_null(col, f"{col} must not be null")

    # UNIQUE
    for col in rules.get("unique", []):
        if col in df.columns:
            v.check_unique(col, f"{col} must be unique")

    # REGEX
    for col, pattern in rules.get("regex", {}).items():
        if col in df.columns:
            v.check_regex(col, pattern, f"{col} format validation")

    # VALUES IN SET
    for col, allowed in rules.get("values_in_set", {}).items():
        if col in df.columns:
            v.check_values_in_set(col, allowed, f"{col} allowed values")

    # NUMERIC RANGE
    for col, (min_v, max_v) in rules.get("numeric_range", {}).items():
        if col in df.columns:
            v.check_numeric_range(col, min_v, max_v, f"{col} range check")

    # DATE RANGE
    for col, (min_d, max_d) in rules.get("date_range", {}).items():
        if col in df.columns:

            if max_d == "today":
                max_d = datetime.now().strftime("%Y-%m-%d")

            v.check_date_range(col, min_d, max_d, f"{col} date range")

    # REFERENTIAL INTEGRITY
    for child, parent in rules.get("referential", []):
        if child in df.columns and parent in df.columns:
            v.check_referential_integrity(
                child,
                parent,
                f"{child} must exist in {parent}"
            )

    return v.generate_report()
