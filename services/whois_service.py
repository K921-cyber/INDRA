import re
from fetch_utils import safe_fetch
from config import settings


LEGAL_NOTE = (
    "Source: rdap.org (IANA RDAP Protocol) — Free, public, no API key. "
    "WhoisXML API used when configured (free 500 req/month). "
    "https://rdap.org | https://www.iana.org/help/rdap"
)

# Basic domain format check
DOMAIN_RE = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+"
    r"[a-zA-Z]{2,}$"
)


def clean_domain(domain: str) -> str:
    """Strip protocol, path, trailing slash from user input."""
    domain = re.sub(r"^https?://", "", domain)
    domain = domain.split("/")[0].strip()
    return domain.lower()


def extract_entity_name(entity: dict) -> str:
    """Pull the fn (full name) from an RDAP entity's vCard."""
    try:
        vcard = entity.get("vcardArray", [[], []])[1]
        for item in vcard:
            if item[0] == "fn":
                return item[3]
    except Exception:
        pass
    return ""


async def lookup_whois(domain: str) -> dict:

    domain = clean_domain(domain)

    if not DOMAIN_RE.match(domain):
        return {
            "error":     f"Invalid domain format: {domain}",
            "_source":   "validation",
            "_fallback": False,
            "_ms":       0,
            "_legal":    LEGAL_NOTE,
        }

    # Use WhoisXML if key is configured (richer data)
    if settings.WHOISXML_API_KEY:
        data, source, is_fallback, ms = await safe_fetch(
            primary_url    = "https://www.whoisxmlapi.com/whoisserver/WhoisService",
            fallback_url   = f"https://rdap.org/domain/{domain}",
            primary_label  = "WhoisXML API",
            fallback_label = "rdap.org [fallback]",
            params = {
                "apiKey":       settings.WHOISXML_API_KEY,
                "domainName":   domain,
                "outputFormat": "JSON",
            },
        )
    else:
        # RDAP — always free, always works, no key needed
        data, source, is_fallback, ms = await safe_fetch(
            primary_url    = f"https://rdap.org/domain/{domain}",
            fallback_url   = f"https://rdap.iana.org/domain/{domain}",
            primary_label  = "rdap.org",
            fallback_label = "rdap.iana.org [fallback]",
        )

    if data is None:
        return {
            "error":     f"WHOIS lookup failed for {domain}.",
            "domain":    domain,
            "_source":   "none",
            "_fallback": is_fallback,
            "_ms":       ms,
            "_legal":    LEGAL_NOTE,
        }

    # ── Normalise RDAP response ───────────────────────────────────
    if "rdap" in source.lower() or is_fallback:
        events     = data.get("events", [])
        registered = next((
            e["eventDate"][:10]
            for e in events
            if e.get("eventAction") == "registration"
        ), None)
        expires    = next((
            e["eventDate"][:10]
            for e in events
            if e.get("eventAction") == "expiration"
        ), None)
        updated    = next((
            e["eventDate"][:10]
            for e in events
            if e.get("eventAction") == "last changed"
        ), None)

        entities   = data.get("entities", [])
        registrar  = next((
            extract_entity_name(e)
            for e in entities
            if "registrar" in e.get("roles", [])
        ), None)
        registrant = next((
            extract_entity_name(e)
            for e in entities
            if "registrant" in e.get("roles", [])
        ), None)

        nameservers = [
            n.get("ldhName", "")
            for n in data.get("nameservers", [])
        ]

        return {
            "domain":      data.get("ldhName", domain),
            "status":      data.get("status", []),
            "registrar":   registrar,
            "registrant":  registrant,
            "registered":  registered,
            "updated":     updated,
            "expires":     expires,
            "nameservers": nameservers,
            "_source":     source,
            "_fallback":   is_fallback,
            "_ms":         ms,
            "_legal":      LEGAL_NOTE,
        }

    # ── Normalise WhoisXML response ───────────────────────────────
    wr = data.get("WhoisRecord", {})
    return {
        "domain":      wr.get("domainName", domain),
        "status":      [wr.get("status", "")],
        "registrar":   wr.get("registrarName"),
        "registrant":  wr.get("registrant", {}).get("organization"),
        "registered":  (wr.get("createdDate", "")[:10]
                        if wr.get("createdDate") else None),
        "updated":     (wr.get("updatedDate", "")[:10]
                        if wr.get("updatedDate") else None),
        "expires":     (wr.get("expiresDate", "")[:10]
                        if wr.get("expiresDate") else None),
        "nameservers": wr.get("nameServers", {}).get("hostNames", []),
        "_source":     source,
        "_fallback":   is_fallback,
        "_ms":         ms,
        "_legal":      LEGAL_NOTE,
    }