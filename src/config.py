from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.parent

CONFIG = {
    "input_dir": _PROJECT_ROOT / "data/raw",
    "output_dir": _PROJECT_ROOT / "data/processed",
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
    }
}
