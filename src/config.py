from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.parent

CONFIG = {
    "input_dir": _PROJECT_ROOT / "data/raw",
    "output_dir": _PROJECT_ROOT / "data/processed",
    "log_dir": _PROJECT_ROOT / "logs",
    "exchange_rates": {
        "USD": 1.0,
        "EUR": 1.10,
        "GBP": 1.28
    },
    "pay_multipliers": {
        "monthly": 12,
        "bi-weekly": 26,
        "weekly": 52,
        "annual": 1
    },
    "source_priority": {
        "globaltech_hris": 1,
        "acquiredco": 2,
        "payroll": 3,
        "benefits": 4
    },
    "colorblind_palette": [
        "#0072B2",
        "#E69F00",
        "#009E73",
        "#CC79A7",
        "#56B4E9",
        "#D55E00"
    ]
}

VALIDATION_RULES = {
    "not_null": [
        "employee_id",
        "first_name",
        "last_name",
        "email",
        "department",
        "country"
    ],
    "unique": [
        "employee_id",
        "email"
    ],
    "regex": {
        "email": CONFIG["email_regex"],
        "employee_id": r"^(GT|AC)-.*$"
    },
    "values_in_set": {
        "employment_type": ["Full-Time", "Part-Time", "Contractor"],
        "currency": ["USD", "EUR", "GBP"]
    },
    "numeric_range": {
        "salary_usd_annual": (15000, 2_000_000)
    },
    "date_range": {
        "hire_date": ("1970-01-01", "today")
    },
    "referential": [
        ("manager_id", "employee_id")
    ]
}
