# Forensic Financial Risk Index (FFRI) Analyzer

Scores Indian listed companies from 0 to 100 on six dimensions. Higher means higher risk.
A high score flags a company for review. It does not establish fraud.

## Inputs
1. `python make_template.py` writes `inputs_template.xlsx`. Fill three sheets:
   - `Companies`: company, symbol, isin, sector, event_year, event_status (confirmed, alleged, none)
   - `Financials`: one row per symbol and fiscal year (FY2024 = year to 31 Mar 2024)
   - `Governance`: audit qualification, auditor resignation, SEBI order, agency probe, related party, promoter pledge
2. Price files in one folder: `SYMBOL.csv` with `DATE, CLOSE, VOLUME` (add `ADJ_CLOSE` for split-adjusted prices) and `NIFTY.csv` with `DATE, CLOSE`.

## Run
```bash
pip install pandas numpy openpyxl
python run.py inputs.xlsx prices/ report.xlsx
python -m pytest tests
```

## Dimensions and weights (ffri/config.py)
| Dimension | Weight | Basis |
|---|---|---|
| beneish | 25% | Beneish M-Score, eight indices |
| accruals | 20% | TATA and CFO to net income |
| leverage | 15% | Altman Z'', debt to assets, interest cover, current ratio |
| price | 15% | Market-model abnormal returns, volatility ratio |
| volume | 10% | Volume spikes against trailing 60 sessions |
| governance | 15% | Audit, SEBI, agency and pledge flags |

Missing dimensions drop out and weights renormalise. No FFRI is reported below 50% coverage.
The report includes a weight-sensitivity sheet with rank stability over 1,000 random weight vectors.

## Limits
- Weights and scaling bounds are research assumptions, not validated.
- Tests use synthetic data only.
- Not run against live NSE or BSE data. Validate prices against exchange Bhavcopy files.
