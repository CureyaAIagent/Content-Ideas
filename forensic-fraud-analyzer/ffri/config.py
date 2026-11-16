"""All research assumptions live here. Change them here and document the change in the thesis."""

WEIGHTS = {
    "beneish": 0.25,
    "accruals": 0.20,
    "leverage": 0.15,
    "price": 0.15,
    "volume": 0.10,
    "governance": 0.15,
}

BANDS = [(20, "Low risk"), (40, "Moderate risk"), (60, "Elevated risk"), (80, "High risk"), (100, "Critical risk")]

# Linear scaling bounds: (value mapped to 0, value mapped to 100)
BENEISH_BOUNDS = (-2.5, -1.0)        # M = -1.78 lands near 48
TATA_BOUNDS = (-0.05, 0.15)
CFO_NI_BOUNDS = (1.0, 0.0)           # CFO/NI of 1.0 or more scores 0, 0 or less scores 100
ALTMAN_Z2_BOUNDS = (2.6, 1.1)        # safe zone edge to distress zone edge
DEBT_ASSETS_BOUNDS = (0.3, 0.8)
INTEREST_COVER_BOUNDS = (4.0, 1.5)
CURRENT_RATIO_BOUNDS = (1.5, 0.8)

# Market model
ESTIMATION_DAYS = 250                # trading days before the fiscal year start
EXTREME_AR_Z = 3.0
EXTREME_DAY_SHARE_MAX = 0.04         # 4% extreme days scores 100
VOL_RATIO_BOUNDS = (1.0, 2.0)
VOLUME_WINDOW = 60
VOLUME_SPIKE_Z = 3.0
VOLUME_SPIKE_SHARE_MAX = 0.05

# Governance points (capped at 100)
GOVERNANCE_POINTS = {
    "audit_qualification": 30,
    "auditor_resignation": 20,
    "sebi_order": 25,
    "agency_probe": 25,
    "related_party_flag": 10,
}
PLEDGE_THRESHOLD_PCT = 50
PLEDGE_POINTS = 10

# Indian fiscal year: FY2024 runs 1 Apr 2023 to 31 Mar 2024
FY_START_MONTH = 4

MIN_COVERAGE = 0.5                   # share of weight that must be scoreable to report an FFRI
