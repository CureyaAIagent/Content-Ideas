"""Tests use SYNTHETIC data only. No result here describes a real company."""
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ffri import scoring as S
from ffri.pipeline import FIN_COLS, combine, run, write_report


def fin_row(scale=1.0, **kw):
    d = dict(sales=1000, cogs=600, sga=100, depreciation=50, net_income=100, cfo=110, total_assets=2000,
             current_assets=800, ppe=900, receivables=150, inventory=100, current_liabilities=500,
             total_debt=600, total_liabilities=1200, retained_earnings=500, ebit=200, interest_expense=50,
             market_cap=3000)
    d.update(kw)
    return d


def test_beneish_stable_firm_below_cutoff():
    r = S.beneish(fin_row(), fin_row())
    assert math.isclose(r["GMI"], 1.0) and math.isclose(r["DEPI"], 1.0)
    assert r["M"] < -1.78


def test_beneish_known_value():
    r = S.beneish(fin_row(), fin_row())
    expected = -4.84 + .92 + .528 + .404 + .892 + .115 - .172 - .327 + 4.679 * (-10 / 2000)
    assert math.isclose(r["M"], expected)


def test_altman_z2_known_value():
    z = S.altman_z2(fin_row())
    exp = 6.56 * (300 / 2000) + 3.26 * (500 / 2000) + 6.72 * (200 / 2000) + 1.05 * (3000 / 1200)
    assert math.isclose(z["Z2"], exp)


def test_altman_partial_is_nan_without_market_cap():
    assert math.isnan(S.altman_z2(fin_row(market_cap=float("nan")))["Z2"])


def test_combine_renormalises_and_requires_coverage():
    full = dict(beneish=50, accruals=50, leverage=50, price=50, volume=50, governance=50)
    assert combine(full) == (50, 1.0)
    part = dict(full, price=float("nan"), volume=float("nan"))
    v, cov = combine(part)
    assert math.isclose(v, 50) and math.isclose(cov, 0.75)
    sparse = dict(beneish=50, accruals=float("nan"), leverage=float("nan"), price=float("nan"),
                  volume=float("nan"), governance=float("nan"))
    assert math.isnan(combine(sparse)[0])


def test_bands():
    assert S.band(20) == "Low risk" and S.band(58) == "Elevated risk" and S.band(85) == "Critical risk"


def test_end_to_end(tmp_path):
    rng = np.random.default_rng(1)
    idx = pd.bdate_range("2020-01-01", "2024-03-31")
    bench = pd.DataFrame({"DATE": idx, "CLOSE": 10000 * np.cumprod(1 + rng.normal(0, .008, len(idx)))})
    pdir = tmp_path / "prices"
    pdir.mkdir()
    bench.to_csv(pdir / "NIFTY.csv", index=False)
    cos, fin, gov = [], [], []
    for i, sym in enumerate(["AAA", "BBB", "CCC"]):
        noise = 0.01 * (i + 1) * (3 if sym == "CCC" else 1)
        r = rng.normal(0, noise, len(idx)) + 0.5 * bench["CLOSE"].pct_change().fillna(0).values
        if sym == "CCC":
            r[-200:-190] += 0.2
        pd.DataFrame({"DATE": idx, "CLOSE": 100 * np.cumprod(1 + r),
                      "VOLUME": rng.integers(1e5, 2e5, len(idx))}).to_csv(pdir / f"{sym}.csv", index=False)
        cos.append(dict(company=f"Synthetic {sym}", symbol=sym, sector="Test", event_year=2023,
                        event_status="none"))
        for y in (2022, 2023, 2024):
            extra = dict(receivables=150 * (1 + (y - 2022) * (1 if sym == "CCC" else 0)),
                         cfo=110 if sym != "CCC" else 20)
            fin.append(dict(symbol=sym, year=y, **fin_row(**extra)))
        gov.append(dict(symbol=sym, year=2024, sebi_order=int(sym == "CCC"), audit_qualification=int(sym == "CCC")))
    xlsx = tmp_path / "in.xlsx"
    with pd.ExcelWriter(xlsx) as xw:
        pd.DataFrame(cos).to_excel(xw, sheet_name="Companies", index=False)
        pd.DataFrame(fin).to_excel(xw, sheet_name="Financials", index=False)
        pd.DataFrame(gov).to_excel(xw, sheet_name="Governance", index=False)
    res = run(xlsx, pdir)
    latest = res["latest"].set_index("symbol")
    assert latest.loc["CCC", "FFRI"] > latest.loc["AAA", "FFRI"]
    assert latest.loc["CCC", "rank_latest"] == 1
    assert (latest["coverage"] == 1.0).all()
    write_report(res, tmp_path / "out.xlsx")
    assert (tmp_path / "out.xlsx").exists()
