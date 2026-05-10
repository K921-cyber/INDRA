import re
from fetch_utils import safe_fetch


LEGAL_NOTE = (
    "Source: ip-api.com — Free, no API key required. "
    "License: Non-commercial use only, CC Attribution required. "
    "Fallback: ipapi.co — Free tier 1000 req/day. "
    "https://ip-api.com/docs/legal"
)

# Regex patterns for basic IP validation
IPV4_RE = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")
IPV6_RE = re.compile(r"^[0-9a-fA-F:]+$")


def is_valid_ip(ip: str) -> bool:
    return bool(IPV4_RE.match(ip) or IPV6_RE.match(ip))


async def lookup_ip(ip: str) -> dict:

    # Validate format before hitting API
    if not is_valid_ip(ip):
        return {
            "error":   f"Invalid IP format: {ip}",
            "valid":   False,
            "_source": "validation",
            "_fallback": False,
            "_ms":     0,
            "_legal":  LEGAL_NOTE,
        }

    # Fields we want from ip-api.com
    fields = (
        "status,message,country,countryCode,regionName,"
        "city,zip,lat,lon,timezone,isp,org,as,query,proxy,hosting"
    )

    data, source, is_fallback, ms = await safe_fetch(
        primary_url    = f"http://ip-api.com/json/{ip}",
        fallback_url   = f"https://ipapi.co/{ip}/json/",
        primary_label  = "ip-api.com",
        fallback_label = "ipapi.co [fallback]",
        params         = {"fields": fields},
    )

    if data is None:
        return {
            "error":     "All geolocation sources unreachable.",
            "ip":        ip,
            "_source":   "none",
            "_fallback": False,
            "_ms":       ms,
            "_legal":    LEGAL_NOTE,
        }

    # ip-api returns {"status": "fail"} for private/invalid IPs
    if data.get("status") == "fail":
        return {
            "error":     data.get("message", "IP lookup failed"),
            "ip":        ip,
            "_source":   source,
            "_fallback": is_fallback,
            "_ms":       ms,
            "_legal":    LEGAL_NOTE,
        }

    # Normalise — ip-api.com and ipapi.co use different field names
    return {
        "ip":           data.get("query")        or data.get("ip")           or ip,
        "country":      data.get("country")      or data.get("country_name"),
        "country_code": data.get("countryCode")  or data.get("country_code"),
        "region":       data.get("regionName")   or data.get("region"),
        "city":         data.get("city"),
        "postal":       data.get("zip")          or data.get("postal"),
        "lat":          data.get("lat")          or data.get("latitude"),
        "lon":          data.get("lon")          or data.get("longitude"),
        "timezone":     data.get("timezone"),
        "isp":          data.get("isp")          or data.get("org"),
        "org":          data.get("org"),
        "asn":          data.get("as")           or data.get("asn"),
        "is_proxy":     data.get("proxy",  False),
        "is_hosting":   data.get("hosting", False),
        "_source":      source,
        "_fallback":    is_fallback,
        "_ms":          ms,
        "_legal":       LEGAL_NOTE,
    }