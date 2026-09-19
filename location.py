"""
ParcelRate – server-side location lookup.
Two strategies:
  1. Pure digits typed → zippopotam.us postcode lookup (fast, precise)
  2. City name typed  → Nominatim (OpenStreetMap) geocoding
Both run server-side in Streamlit so no CORS/CSP issues.
Results are cached for the session to minimise external calls.
"""

from __future__ import annotations
import re
import requests
import streamlit as st

ZIPPOPOTAM_URL = "https://api.zippopotam.us/de/{postcode}"
NOMINATIM_URL  = "https://nominatim.openstreetmap.org/search"
NOMINATIM_HEADERS = {"User-Agent": "ParcelRate/1.0 (shipping comparator, DE domestic)"}

TIMEOUT = 5  # seconds


@st.cache_data(ttl=3600, show_spinner=False)
def lookup_postcode(postcode: str) -> list[dict]:
    """Look up city/state from a (partial) German postcode."""
    try:
        r = requests.get(ZIPPOPOTAM_URL.format(postcode=postcode), timeout=TIMEOUT)
        if r.status_code != 200:
            return []
        data = r.json()
        pc = data.get("post code", postcode)
        return [
            {"postcode": pc, "city": p["place name"], "state": p.get("state", "")}
            for p in data.get("places", [])
        ]
    except Exception:
        return []


@st.cache_data(ttl=3600, show_spinner=False)
def lookup_city(query: str) -> list[dict]:
    """Geocode a city name to German postcodes via Nominatim."""
    try:
        params = {
            "q": f"{query}, Germany",
            "format": "json",
            "addressdetails": 1,
            "limit": 10,
            "countrycodes": "de",
        }
        r = requests.get(NOMINATIM_URL, params=params,
                         headers=NOMINATIM_HEADERS, timeout=TIMEOUT)
        if r.status_code != 200:
            return []

        results, seen = [], set()
        for item in r.json():
            addr = item.get("address", {})
            pc   = addr.get("postcode", "")
            city = (addr.get("city") or addr.get("town") or
                    addr.get("village") or addr.get("municipality") or
                    addr.get("county") or "")
            if not pc or not city or pc in seen:
                continue
            if not re.match(r"^\d{5}$", pc):
                continue
            seen.add(pc)
            results.append({
                "postcode": pc,
                "city": city,
                "state": addr.get("state", ""),
            })
            if len(results) >= 6:
                break
        return results
    except Exception:
        return []


def resolve(query: str) -> list[dict]:
    """Route to the right lookup based on whether query looks like a postcode."""
    q = query.strip()
    if not q:
        return []
    if re.match(r"^\d+$", q):
        return lookup_postcode(q)
    return lookup_city(q)


def format_option(loc: dict) -> str:
    """Human-readable dropdown label."""
    return f"{loc['city']} ({loc['state']}) — {loc['postcode']}"
