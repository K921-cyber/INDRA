import asyncio
import time as time_module
from fetch_utils import safe_fetch


LEGAL_NOTE = (
    "Source: Nominatim/OpenStreetMap — Free, no API key required. "
    "License: ODbL (Open Database License) — attribution required. "
    "Rate limit: 1 request/second enforced by INDRA. "
    "https://nominatim.org | https://osmfoundation.org/wiki/Licence"
)

# Track last call time to enforce Nominatim's 1 req/sec policy
_last_call: float = 0.0


async def lookup_geo(place: str) -> dict:
    global _last_call

    if not place.strip():
        return {
            "error":     "Search term cannot be empty",
            "_source":   "validation",
            "_fallback": False,
            "_ms":       0,
            "_legal":    LEGAL_NOTE,
        }

    # Enforce Nominatim rate limit — 1 request per second
    now  = time_module.monotonic()
    wait = 1.0 - (now - _last_call)
    if wait > 0:
        await asyncio.sleep(wait)
    _last_call = time_module.monotonic()

    # Nominatim requires a descriptive User-Agent
    # identifying your application — required by their ToS
    headers = {
        "User-Agent": (
            "INDRA-OSINT-Platform/2.1 "
            "(academic research tool; "
            "github.com/indra-osint)"
        )
    }

    data, source, is_fallback, ms = await safe_fetch(
        primary_url    = "https://nominatim.openstreetmap.org/search",
        primary_label  = "Nominatim/OSM",
        fallback_url   = None,    # No fallback for geo
        headers        = headers,
        params = {
            "q":             f"{place} India",
            "format":        "json",
            "limit":         5,
            "addressdetails": 1,
        },
    )

    if data is None:
        return {
            "error":        "Nominatim unreachable.",
            "fallback_tip": "Try ISRO Bhuvan manually: bhuvan.nrsc.gov.in",
            "place":        place,
            "_source":      "none",
            "_fallback":    False,
            "_ms":          ms,
            "_legal":       LEGAL_NOTE,
        }

    if not data:    # Empty list — no results found
        return {
            "error":    f"No locations found for: {place}",
            "tip":      "Try a major Indian city or district name",
            "place":    place,
            "_source":  source,
            "_fallback": is_fallback,
            "_ms":       ms,
            "_legal":    LEGAL_NOTE,
        }

    # Normalise each result
    results = []
    for r in data:
        addr = r.get("address", {})
        results.append({
            "display_name": r.get("display_name"),
            "lat":          float(r.get("lat", 0)),
            "lon":          float(r.get("lon", 0)),
            "type":         r.get("type"),
            "class":        r.get("class"),
            "address": {
                "state":    addr.get("state"),
                "district": addr.get("county") or addr.get("state_district"),
                "city":     (addr.get("city")
                             or addr.get("town")
                             or addr.get("village")),
                "postcode": addr.get("postcode"),
                "country":  addr.get("country"),
            },
        })

    return {
        "query":     place,
        "count":     len(results),
        "results":   results,
        "_source":   source,
        "_fallback": is_fallback,
        "_ms":       ms,
        "_legal":    LEGAL_NOTE,
    }