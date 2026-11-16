"""Market-model abnormal returns, volatility and volume anomalies per fiscal year."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as C
from .scoring import scale


def fy_of(ts: pd.Timestamp) -> int:
    return ts.year + 1 if ts.month >= C.FY_START_MONTH else ts.year


def load_prices(path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip().upper() for c in df.columns]
    df["DATE"] = pd.to_datetime(df["DATE"])
    df = df.sort_values("DATE").drop_duplicates("DATE").set_index("DATE")
    return df


def market_features(stock: pd.DataFrame, bench: pd.DataFrame, fy: int) -> dict:
    """Features for one fiscal year. Estimation window: ESTIMATION_DAYS sessions before FY start."""
    out = dict(price_score=np.nan, volume_score=np.nan, flags=[], n_days=0)
    if "ADJ_CLOSE" in stock.columns:
        px = stock["ADJ_CLOSE"]
        out["price_basis"] = "adjusted"
    else:
        px = stock["CLOSE"]
        out["price_basis"] = "unadjusted (check splits and bonus issues)"
    ret = px.pct_change() * 100
    bret = bench["CLOSE"].pct_change() * 100
    df = pd.concat([ret.rename("r"), bret.rename("m")], axis=1).dropna()
    fy_start = pd.Timestamp(year=fy - 1, month=C.FY_START_MONTH, day=1)
    fy_end = pd.Timestamp(year=fy, month=C.FY_START_MONTH, day=1)
    est = df[df.index < fy_start].tail(C.ESTIMATION_DAYS)
    win = df[(df.index >= fy_start) & (df.index < fy_end)]
    if len(est) < 120 or len(win) < 100:
        return out
    beta, alpha = np.polyfit(est["m"], est["r"], 1)
    resid = est["r"] - (alpha + beta * est["m"])
    sigma = resid.std(ddof=2)
    if sigma == 0 or np.isnan(sigma):
        return out
    ar = win["r"] - (alpha + beta * win["m"])
    z = ar / sigma
    extreme = float((z.abs() > C.EXTREME_AR_Z).mean())
    vol_ratio = float(win["r"].std() / est["r"].std())
    a = scale(extreme, (0, C.EXTREME_DAY_SHARE_MAX))
    b = scale(vol_ratio, C.VOL_RATIO_BOUNDS)
    out.update(price_score=float(np.mean([a, b])), n_days=len(win), beta=float(beta), alpha=float(alpha),
               extreme_share=extreme, vol_ratio=vol_ratio, car_pct=float(ar.sum()), max_abs_z=float(z.abs().max()))
    if extreme > 0.02:
        out["flags"].append(f"{extreme:.1%} of sessions had abnormal returns beyond {C.EXTREME_AR_Z:.0f} sigma")
    if vol_ratio > 1.5:
        out["flags"].append(f"Volatility {vol_ratio:.1f}x the estimation window")
    if "VOLUME" in stock.columns:
        v = stock["VOLUME"].astype(float)
        roll_m = v.rolling(C.VOLUME_WINDOW).mean().shift(1)
        roll_s = v.rolling(C.VOLUME_WINDOW).std().shift(1)
        vz = ((v - roll_m) / roll_s).loc[fy_start:fy_end - pd.Timedelta(days=1)].dropna()
        if len(vz) >= 100:
            share = float((vz > C.VOLUME_SPIKE_Z).mean())
            out["volume_score"] = scale(share, (0, C.VOLUME_SPIKE_SHARE_MAX))
            out["volume_spike_share"] = share
            if share > 0.03:
                out["flags"].append(f"Volume spikes on {share:.1%} of sessions")
    return out
