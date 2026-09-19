"""
ParcelRate – carrier matching and dimensional logic.
All dimension checks are carrier-specific:
  LWH  – DHL / DPD: all three sides sorted largest→smallest must each fit
  SL   – GLS: MAX(input) + MIN(input) ≤ MAX(tier) + MIN(tier)  (girth-style)
  NONE – UPS: weight-only, no published dimensional limit
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional


def load_rates(path: str = "data/rates.json") -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sorted_desc(a, b, c) -> list[float]:
    return sorted([x for x in (a, b, c) if x is not None], reverse=True)


def dim_fits(rule: str,
             iL: float, iW: float, iH: float,
             tL: Optional[float], tW: Optional[float], tH: Optional[float]) -> bool:
    if rule == "NONE" or any(v is None for v in (tL, tW, tH)):
        return True

    inp  = _sorted_desc(iL, iW, iH)   # [largest, mid, smallest]
    tier = _sorted_desc(tL, tW, tH)

    if rule == "LWH":
        return all(inp[i] <= tier[i] for i in range(3))

    if rule == "SL":
        # Only longest + shortest checked; middle dimension is not constrained
        return (max(iL, iW, iH) + min(iL, iW, iH)) <= (max(tL, tW, tH) + min(tL, tW, tH))

    return False


def ineligible_reason(carrier: str, rates: list[dict],
                      weight: float, L: float, W: float, H: float) -> str:
    carrier_rates = [r for r in rates if r["carrier"] == carrier]
    weight_ok = any(weight <= r["maxKg"] for r in carrier_rates)
    if not weight_ok:
        return f"Exceeds max weight for {carrier}"
    return f"Dimensions exceed {carrier} limits"


def get_results(rates: list[dict],
                weight: float, L: float, W: float, H: float) -> dict[str, list[dict]]:
    """
    Returns a dict keyed by carrier with a list of eligible tiers,
    sorted cheapest first. Ineligible carriers have an empty list.
    """
    carriers = ["DHL", "DPD", "UPS", "GLS"]
    out = {}
    for carrier in carriers:
        eligible = [
            r for r in rates
            if r["carrier"] == carrier
            and weight <= r["maxKg"]
            and dim_fits(r["dimRule"], L, W, H, r["L"], r["W"], r["H"])
        ]
        out[carrier] = sorted(eligible, key=lambda r: r["price"])
    return out
