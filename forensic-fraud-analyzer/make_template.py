"""Write an empty input workbook with the expected sheets and headers."""
import pandas as pd

from ffri.pipeline import FIN_COLS

with pd.ExcelWriter("inputs_template.xlsx") as xw:
    pd.DataFrame(columns=["company", "symbol", "isin", "bse_code", "sector", "event_year",
                          "event_status"]).to_excel(xw, sheet_name="Companies", index=False)
    pd.DataFrame(columns=["symbol", "year"] + FIN_COLS).to_excel(xw, sheet_name="Financials", index=False)
    pd.DataFrame(columns=["symbol", "year", "audit_qualification", "auditor_resignation", "sebi_order",
                          "agency_probe", "related_party_flag", "promoter_pledge_pct",
                          "source"]).to_excel(xw, sheet_name="Governance", index=False)
print("Wrote inputs_template.xlsx")
