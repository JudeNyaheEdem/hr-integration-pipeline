# HR Integration Pipeline

Merges GlobalTech and AcquiredCo HRIS data, deduplicates employees, flags payroll-only ghosts, and writes outputs to `data/processed/`.

## Run

```bash
python pipeline.py
```

## Inputs (`data/raw/`)

- `globaltech_hris.csv`
- `acquiredco_api.json`
- `payroll_data.xlsx`
- `benefits_enrollment.xml`

## Outputs (`data/processed/`)

- `golden_employee_dataset/` (parquet, partitioned by `company_origin`)
- `ghost_employee_report.csv`
- `probable_match_review.csv`
- `validation_report.csv` / `.html`
- `eda_report.png`

Code lives in `src/` (`ingestion`, `cleaning`, `deduplication`, `validation`, `visualization`).
