from fetch_utils import safe_fetch
from config import settings
from services.ip_service import lookup_ip, is_valid_ip


LEGAL_NOTE = (
    "Source: AbuseIPDB — Free 1000 checks/day, API key required. "
    "Register: abuseipdb.com/register. "
    "Fallback: ip-api.com network context (non-commercial CC). "
    "Do NOT use for mass automated scanning — violates AbuseIPDB ToS. "
    "https://docs.abuseipdb.com"
)


async def lookup_threat(ip: str) -> dict:

    if not is_valid_ip(ip):
        return {
            "error":     f"Invalid IP format: {ip}",
            "_source":   "validation",
            "_fallback": False,
            "_ms":       0,
            "_legal":    LEGAL_NOTE,
        }

    # ── AbuseIPDB (if key configured) ────────────────────────────
    if settings.ABUSEIPDB_API_KEY:
        data, source, is_fallback, ms = await safe_fetch(
            primary_url    = "https://api.abuseipdb.com/api/v2/check",
            primary_label  = "AbuseIPDB",
            fallback_url   = None,
            headers = {
                "Key":    settings.ABUSEIPDB_API_KEY,
                "Accept": "application/json",
            },
            params = {
                "ipAddress":    ip,
                "maxAgeInDays": 90,
            },
        )

        if data and "data" in data:
            d = data["data"]
            return {
                "ip":             ip,
                "abuse_score":    d.get("abuseConfidenceScore"),
                "total_reports":  d.get("totalReports"),
                "last_reported":  d.get("lastReportedAt"),
                "is_whitelisted": d.get("isWhitelisted"),
                "isp":            d.get("isp"),
                "domain":         d.get("domain"),
                "country":        d.get("countryCode"),
                "usage_type":     d.get("usageType"),
                "is_tor":         d.get("isTor"),
                "distinct_users": d.get("numDistinctUsers"),
                "_source":        source,
                "_fallback":      False,
                "_ms":            ms,
                "_legal":         LEGAL_NOTE,
            }

    # ── Fallback: ip-api.com network context ─────────────────────
    # No AbuseIPDB key configured — use free IP geolocation
    # to at least show proxy/hosting/ASN information
    geo = await lookup_ip(ip)

    return {
        "ip":             ip,
        "abuse_score":    None,
        "total_reports":  None,
        "is_tor":         None,
        "is_proxy":       geo.get("is_proxy"),
        "is_hosting":     geo.get("is_hosting"),
        "country":        geo.get("country"),
        "isp":            geo.get("isp"),
        "asn":            geo.get("asn"),
        "note": (
            "AbuseIPDB key not configured — "
            "showing network context only. "
            "Register free at abuseipdb.com/register "
            "and add ABUSEIPDB_API_KEY to .env"
        ),
        "_source":        geo.get("_source", "ip-api.com [no key]"),
        "_fallback":      True,
        "_ms":            geo.get("_ms", 0),
        "_legal":         LEGAL_NOTE,
    }
