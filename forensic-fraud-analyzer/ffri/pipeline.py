"""Read inputs, compute six dimensions, combine into FFRI, rank, test weight sensitivity."""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from . import config as C
from . import scoring as S
from .market import load_prices, market_features

DIMS = list(C.WEIGHTS)
FIN_COLS = ["sales", "cogs", "sga", "depreciation", "net_income", "cfo", "total_assets", "current_assets", "ppe",
            "receivables", "inventory", "current_liabilities", "total_debt", "total_liabilities",
            "retained_earnings", "ebit", "interest_expense", "market_cap"]


def read_inputs(xlsx: str | Path):
    cos = pd.read_excel(xlsx, sheet_name="Companies")
    fin = pd.read_excel(xlsx, sheet_name="Financials")
    try:
        gov = pd.read_excel(xlsx, sheet_name="Governance")
    except ValueError:
        gov = pd.DataFrame(columns=["symbol", "year"])
    for df in (cos, fin, gov):
        df.columns = [str(c).strip().lower() for c in df.columns]
    return cos, fin, gov


def combine(scores: dict, weights: dict | None = None) -> tuple[float, float]:
    """Weighted mean over scoreable dimensions. Returns (ffri, coverage)."""
    w = weights or C.WEIGHTS
    ok = {k: w[k] for k in DIMS if not _nan(scores.get(k))}
    cov = sum(ok.values()) / sum(w.values())
    if cov < C.MIN_COVERAGE:
        return float("nan"), cov
    return sum(w_ * scores[k] for k, w_ in ok.items()) / sum(ok.values()), cov


def _nan(x):
    return x is None or (isinstance(x, float) and math.isnan(x))


def run(xlsx, prices_dir, benchmark="NIFTY") -> dict[str, pd.DataFrame]:
    cos, fin, gov = read_inputs(xlsx)
    prices_dir = Path(prices_dir)
    bench = load_prices(prices_dir / f"{benchmark}.csv") if (prices_dir / f"{benchmark}.csv").exists() else None
    rows = []
    for _, co in cos.iterrows():
        sym = co["symbol"]
        f = fin[fin["symbol"] == sym].sort_values("year").set_index("year")
        g = gov[gov["symbol"] == sym].set_index("year") if len(gov) else pd.DataFrame()
        spath = prices_dir / f"{sym}.csv"
        stock = load_prices(spath) if spath.exists() else None
        for year in f.index:
            if year - 1 not in f.index:
                continue
            cur = f.loc[year].to_dict()
            prev = f.loc[year - 1].to_dict()
            ben = S.beneish(cur, prev)
            z = S.altman_z2(cur)
            acc, acc_flags = S.accrual_dimension(cur, ben["TATA"])
            lev, lev_flags = S.leverage_dimension(cur, z["Z2"])
            gov_row = g.loc[year].to_dict() if year in g.index else None
            gv, gv_flags = S.governance_dimension(gov_row)
            mk = dict(price_score=np.nan, volume_score=np.nan, flags=[], price_basis="no price file")
            if stock is not None and bench is not None:
                mk = market_features(stock, bench, int(year))
            flags = list(acc_flags) + list(lev_flags) + list(gv_flags) + list(mk["flags"])
            m = ben["M"]
            if not math.isnan(m) and m > -1.78:
                flags.append(f"Beneish M {m:.2f} above -1.78")
            dims = dict(beneish=S.scale(m, C.BENEISH_BOUNDS), accruals=acc, leverage=lev,
                        price=mk["price_score"], volume=mk["volume_score"], governance=gv)
            ffri, cov = combine(dims)
            rows.append(dict(
                company=co["company"], symbol=sym, sector=co.get("sector"), year=int(year),
                event_year=co.get("event_year"), event_status=co.get("event_status", "not classified"),
                **{f"S_{k}": v for k, v in dims.items()}, FFRI=ffri, coverage=cov, band=S.band(ffri),
                beneish_M=m, altman_Z2=z["Z2"], price_basis=mk.get("price_basis"),
                evidence_flags="; ".join(flags)))
    long = pd.DataFrame(rows)
    if long.empty:
        raise SystemExit("No company-year had a prior year of financials. Check the Financials sheet.")
    long["rank_in_year"] = long.groupby("year")["FFRI"].rank(ascending=False, method="min")
    latest = long.sort_values("year").groupby("symbol").tail(1).sort_values("FFRI", ascending=False)
    latest["rank_latest"] = range(1, len(latest) + 1)
    return dict(long=long, latest=latest, pivot=long.pivot(index="company", columns="year", values="FFRI"),
                sensitivity=sensitivity(long))


def sensitivity(long: pd.DataFrame, draws: int = 1000, seed: int = 7) -> pd.DataFrame:
    """Rank stability under random weight vectors (Dirichlet around the base weights)."""
    rng = np.random.default_rng(seed)
    latest = long.sort_values("year").groupby("symbol").tail(1).reset_index(drop=True)
    base = np.array([C.WEIGHTS[k] for k in DIMS])
    ranks = np.zeros((draws, len(latest)))
    for i in range(draws):
        w = rng.dirichlet(base * 50)
        vals = [combine({k: r[f"S_{k}"] for k in DIMS}, dict(zip(DIMS, w)))[0] for _, r in latest.iterrows()]
        ranks[i] = pd.Series(vals).rank(ascending=False, method="min").values
    return pd.DataFrame(dict(company=latest["company"], base_FFRI=latest["FFRI"], mean_rank=ranks.mean(0),
                             rank_sd=ranks.std(0), best_rank=ranks.min(0), worst_rank=ranks.max(0))
                        ).sort_values("mean_rank")


METHOD_NOTES = [
    "FFRI is a screening index. A high score flags a company for review. It does not establish fraud.",
    "Weights are proposed research weights, not validated. See the sensitivity sheet for rank stability.",
    "Dimensions are scaled 0-100 with fixed bounds in ffri/config.py. Higher means higher risk.",
    "Missing dimensions are dropped and remaining weights renormalised. Coverage shows the weight scored.",
    "Event status (confirmed, alleged, none) comes from the Companies sheet and never from the score.",
    "Altman Z'' and the leverage dimension measure distress, not manipulation.",
    "Abnormal returns use a market model on NIFTY over the 250 sessions before each fiscal year.",
    "Unadjusted prices distort returns around splits and bonus issues. Supply ADJ_CLOSE where possible.",
]


def write_report(res: dict, out) -> None:
    with pd.ExcelWriter(out, engine="openpyxl") as xw:
        res["latest"].to_excel(xw, sheet_name="Latest_Ranking", index=False)
        res["long"].to_excel(xw, sheet_name="Company_Year", index=False)
        res["pivot"].to_excel(xw, sheet_name="FFRI_by_Year")
        res["sensitivity"].to_excel(xw, sheet_name="Weight_Sensitivity", index=False)
        pd.DataFrame({"Method and limits": METHOD_NOTES}).to_excel(xw, sheet_name="Method", index=False)
