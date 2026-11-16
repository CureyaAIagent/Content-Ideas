"""Investor Caution Score (0 to 8): rule INFERRED from the CG Power chapter. Not a validated scale.

Points: Pustylnick flags (0-5) + Altman Z'' zone (grey 0.5, distress 1.0) + negative ROA 0.5
+ ROA below -30% extra 1.0 + Beneish above -1.78 (1.5) + Montier 2 or more flags 0.5. Capped at 8.
The weights reproduce all six CG Power values exactly. Six points fit many rules, so treat as indicative.
"""
import math


def num(s):
    try:
        return float(str(s).replace("−", "-").replace("%", "").strip())
    except ValueError:
        return float("nan")


def caution(m, z, roa, p, c):
    s = p
    if not math.isnan(z):
        s += 0 if z > 2.6 else (0.5 if z > 1.1 else 1.0)
    if not math.isnan(roa):
        s += 0.5 if roa < 0 else 0
        s += 1.0 if roa < -30 else 0
    if not math.isnan(m) and m > -1.78:
        s += 1.5
    if c >= 2:
        s += 0.5
    return min(s, 8.0)


if __name__ == "__main__":
    cg = [(-6.11, 4.43, -16.6, 4, 3, 5.0), (-2.63, 5.62, 1.7, 1, 2, 1.5), (-2.74, 2.41, 0.2, 3, 2, 4.0),
          (-4.37, -0.41, -19.5, 3, 0, 4.5), (-6.42, -6.92, -44.2, 3, 1, 5.5), (-1.03, 2.12, 17.8, 1, 4, 3.5)]
    for *a, t in cg:
        assert caution(*a) == t, (a, t, caution(*a))
    print("Rule reproduces all six CG Power values")
