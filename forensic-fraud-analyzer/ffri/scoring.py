"""Standalone forensic models and the 0-100 dimension scalers."""
from __future__ import annotations

import math

import numpy as np

from . import config as C


def scale(x, bounds):
    """Linear map to 0-100 (bounds = value for 0, value for 100). NaN stays NaN."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return float("nan")
    lo, hi = bounds
    return float(np.clip((x - lo) / (hi - lo) * 100.0, 0, 100))


def _div(a, b):
    try:
        if b == 0 or any(v is None or (isinstance(v, float) and math.isnan(v)) for v in (a, b)):
            return float("nan")
        return a / b
    except TypeError:
        return float("nan")


def beneish(cur: dict, prev: dict) -> dict:
    """Original eight-variable Beneish M-Score. Returns each index and M."""
    g = lambda d, k: d.get(k, float("nan"))
    gm = lambda d: _div(g(d, "sales") - g(d, "cogs"), g(d, "sales"))
    dsri = _div(_div(g(cur, "receivables"), g(cur, "sales")), _div(g(prev, "receivables"), g(prev, "sales")))
    gmi = _div(gm(prev), gm(cur))
    aq = lambda d: 1 - _div(g(d, "current_assets") + g(d, "ppe"), g(d, "total_assets"))
    aqi = _div(aq(cur), aq(prev))
    sgi = _div(g(cur, "sales"), g(prev, "sales"))
    dr = lambda d: _div(g(d, "depreciation"), g(d, "depreciation") + g(d, "ppe"))
    depi = _div(dr(prev), dr(cur))
    sga = lambda d: _div(g(d, "sga"), g(d, "sales"))
    sgai = _div(sga(cur), sga(prev))
    lv = lambda d: _div(g(d, "total_debt"), g(d, "total_assets"))
    lvgi = _div(lv(cur), lv(prev))
    tata = _div(g(cur, "net_income") - g(cur, "cfo"), g(cur, "total_assets"))
    parts = dict(DSRI=dsri, GMI=gmi, AQI=aqi, SGI=sgi, DEPI=depi, SGAI=sgai, LVGI=lvgi, TATA=tata)
    if any(math.isnan(v) for v in parts.values()):
        m = float("nan")
    else:
        m = (-4.84 + 0.92 * dsri + 0.528 * gmi + 0.404 * aqi + 0.892 * sgi + 0.115 * depi
             - 0.172 * sgai - 0.327 * lvgi + 4.679 * tata)
    return {**parts, "M": m}


def altman_z2(d: dict) -> dict:
    """Z'' variant (no sales term), used for emerging markets and non-manufacturers."""
    g = lambda k: d.get(k, float("nan"))
    ta = g("total_assets")
    x1 = _div(g("current_assets") - g("current_liabilities"), ta)
    x2 = _div(g("retained_earnings"), ta)
    x3 = _div(g("ebit"), ta)
    x4 = _div(g("market_cap"), g("total_liabilities"))
    parts = [x1, x2, x3, x4]
    z = float("nan") if any(math.isnan(v) for v in parts) else 6.56 * x1 + 3.26 * x2 + 6.72 * x3 + 1.05 * x4
    return {"X1": x1, "X2": x2, "X3": x3, "X4": x4, "Z2": z}


def accrual_dimension(cur: dict, tata: float) -> tuple[float, list[str]]:
    flags, comps = [], []
    s = scale(tata, C.TATA_BOUNDS)
    if not math.isnan(s):
        comps.append(s)
        if tata > 0.10:
            flags.append(f"High total accruals (TATA {tata:.3f})")
    ni, cfo = cur.get("net_income", float("nan")), cur.get("cfo", float("nan"))
    if not (math.isnan(ni) or math.isnan(cfo)) and ni > 0:
        ratio = cfo / ni
        comps.append(scale(ratio, C.CFO_NI_BOUNDS))
        if ratio < 0.5:
            flags.append(f"Cash flow covers {ratio:.0%} of profit")
    return (float(np.mean(comps)) if comps else float("nan")), flags


def leverage_dimension(cur: dict, z2: float) -> tuple[float, list[str]]:
    flags, comps = [], []
    if not math.isnan(z2):
        comps.append(scale(z2, C.ALTMAN_Z2_BOUNDS))
        if z2 < 1.1:
            flags.append(f"Altman Z'' in distress zone ({z2:.2f})")
    da = _div(cur.get("total_debt", float("nan")), cur.get("total_assets", float("nan")))
    if not math.isnan(da):
        comps.append(scale(da, C.DEBT_ASSETS_BOUNDS))
    ic = _div(cur.get("ebit", float("nan")), cur.get("interest_expense", float("nan")))
    if not math.isnan(ic):
        comps.append(scale(ic, C.INTEREST_COVER_BOUNDS))
        if ic < 1.5:
            flags.append(f"Interest cover {ic:.2f}x")
    cr = _div(cur.get("current_assets", float("nan")), cur.get("current_liabilities", float("nan")))
    if not math.isnan(cr):
        comps.append(scale(cr, C.CURRENT_RATIO_BOUNDS))
    return (float(np.mean(comps)) if comps else float("nan")), flags


def governance_dimension(row: dict | None) -> tuple[float, list[str]]:
    if row is None:
        return float("nan"), []
    pts, flags = 0, []
    for key, p in C.GOVERNANCE_POINTS.items():
        if int(row.get(key, 0) or 0):
            pts += p
            flags.append(key.replace("_", " ").capitalize())
    pledge = row.get("promoter_pledge_pct", float("nan"))
    if pledge == pledge and pledge >= C.PLEDGE_THRESHOLD_PCT:
        pts += C.PLEDGE_POINTS
        flags.append(f"Promoter pledge {pledge:.0f}%")
    return float(min(pts, 100)), flags


def band(score: float) -> str:
    if score != score:
        return "Not scored"
    for upper, name in C.BANDS:
        if score <= upper:
            return name
    return C.BANDS[-1][1]
