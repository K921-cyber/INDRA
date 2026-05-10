from fetch_utils import safe_fetch
from config import settings


LEGAL_NOTE = (
    "Source: data.gov.in — Ministry of Corporate Affairs (MCA21). "
    "License: Open Government Data License India 1.0 (OGDL-India 1.0). "
    "Free API key: https://data.gov.in/user/register. "
    "Attribution required in any downstream use. "
    "https://data.gov.in/catalog/master-data-ministry-corporate-affairs"
)

# MCA21 Master Data resource ID on data.gov.in
MCA_RESOURCE_ID = "64a1cc14-0e05-44f7-b077-d9f3c1cf39e3"


async def lookup_company(name: str) -> dict:

    if not name.strip():
        return {
            "error":     "Company name cannot be empty",
            "_source":   "validation",
            "_fallback": False,
            "_ms":       0,
            "_legal":    LEGAL_NOTE,
        }

    # ── No API key — return helpful guidance ─────────────────────
    if not settings.DATA_GOV_IN_API_KEY:
        return {
            "note": (
                "data.gov.in API key not configured. "
                "Register free at data.gov.in/user/register "
                "then add DATA_GOV_IN_API_KEY to your .env file."
            ),
            "query":        name,
            "dataset_url":  (
                "https://data.gov.in/catalog/"
                "master-data-ministry-corporate-affairs"
            ),
            "sebi_manual":  "https://www.sebi.gov.in",
            "roc_manual":   "https://www.mca.gov.in/mcafoportal/viewCompanyMasterData.do",
            "_source":      "no-key",
            "_fallback":    False,
            "_ms":          0,
            "_legal":       LEGAL_NOTE,
        }

    # ── Query data.gov.in MCA21 dataset ──────────────────────────
    data, source, is_fallback, ms = await safe_fetch(
        primary_url    = f"https://api.data.gov.in/resource/{MCA_RESOURCE_ID}",
        primary_label  = "data.gov.in (MCA21)",
        fallback_url   = None,
        params = {
            "api-key":               settings.DATA_GOV_IN_API_KEY,
            "format":                "json",
            "filters[COMPANY_NAME]": name.upper(),
            "limit":                 10,
        },
    )

    if data is None:
        return {
            "error":   "data.gov.in unreachable. Try again later.",
            "query":   name,
            "_source":   "none",
            "_fallback": False,
            "_ms":       ms,
            "_legal":    LEGAL_NOTE,
        }

    records = data.get("records", [])

    if not records:
        return {
            "note":    f"No companies found matching: {name}",
            "tip":     "Try searching with partial name or in CAPS",
            "query":   name,
            "_source":   source,
            "_fallback": is_fallback,
            "_ms":       ms,
            "_legal":    LEGAL_NOTE,
        }

    # Normalise MCA21 records
    companies = []
    for r in records:
        companies.append({
            "name":          r.get("COMPANY_NAME"),
            "cin":           r.get("CIN"),
            "category":      r.get("COMPANY_CATEGORY"),
            "class":         r.get("CLASS_OF_COMPANY"),
            "status":        r.get("COMPANY_STATUS"),
            "state":         r.get("STATE"),
            "roc":           r.get("REGISTRAR_OF_COMPANIES"),
            "date_of_reg":   r.get("DATE_OF_INCORPORATION"),
            "auth_capital":  r.get("AUTHORISED_CAP"),
            "paid_up_cap":   r.get("PAIDUP_CAPITAL"),
        })

    return {
        "query":     name,
        "total":     data.get("total", len(companies)),
        "results":   companies,
        "_source":   source,
        "_fallback": is_fallback,
        "_ms":       ms,
        "_legal":    LEGAL_NOTE,
    }
