"""
ParcelRate – carrier matching and dimensional logic.
All dimension checks are carrier-specific:

  LWH  – DHL / DPD: all three sides sorted largest→smallest must each fit
           within the corresponding sorted tier dimension.

  GLS  – GLS DE published rules (source: gls-pakete.de):
           1. Each absolute side must not exceed the tier's absolute max
              (sorted: largest≤tier_largest, mid≤tier_mid, smallest≤tier_smallest)
           2. Belt/girth = L + 2×W + 2×H ≤ 300 cm (hard constant for all GLS tiers)

  NONE – UPS: weight-only, no published dimensional limit in Phase 1 rate card.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional

GLS_MAX_GIRTH = 300  # cm — L + 2W + 2H ≤ 300 (GLS DE published rule)


def load_rates(path: str = "data/rates.json") -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sorted_desc(a, b, c) -> list[float]:
    return sorted([x for x in (a, b, c) if x is not None], reverse=True)


def _gls_girth(L: float, W: float, H: float) -> float:
    """GLS belt size = longest side + 2x middle + 2x shortest."""
    sides = sorted([L, W, H], reverse=True)
    return sides[0] + 2 * sides[1] + 2 * sides[2]


def dim_fits(rule: str,
             iL: float, iW: float, iH: float,
             tL: Optional[float], tW: Optional[float], tH: Optional[float]) -> bool:
    if rule == "NONE" or any(v is None for v in (tL, tW, tH)):
        return True

    inp  = _sorted_desc(iL, iW, iH)
    tier = _sorted_desc(tL, tW, tH)

    if rule == "LWH":
        return all(inp[i] <= tier[i] for i in range(3))

    if rule == "GLS":
        sides_ok = all(inp[i] <= tier[i] for i in range(3))
        girth_ok = _gls_girth(iL, iW, iH) <= GLS_MAX_GIRTH
        return sides_ok and girth_ok

    return False


def ineligible_reason(carrier: str, rates: list[dict],
                      weight: float, L: float, W: float, H: float) -> str:
    carrier_rates = [r for r in rates if r["carrier"] == carrier]
    weight_ok = any(weight <= r["maxKg"] for r in carrier_rates)
    if not weight_ok:
        return f"Exceeds max weight for {carrier}"
    if carrier == "GLS":
        girth = _gls_girth(L, W, H)
        if girth > GLS_MAX_GIRTH:
            return f"GLS girth {girth:.0f} cm exceeds 300 cm limit"
    return f"Dimensions exceed {carrier} limits"


def get_results(rates: list[dict],
                weight: float, L: float, W: float, H: float) -> dict[str, list[dict]]:
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
