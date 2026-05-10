from fetch_utils import safe_fetch
from config import settings


LEGAL_NOTE = (
    "Sources: GNews API (gnews.io — free 100/day, key required) | "
    "GDELT Project (open data, no key required). "
    "News content copyright belongs to original publishers. "
    "INDRA surfaces headlines and links only — not full article text. "
    "https://gnews.io/docs | https://blog.gdeltproject.org"
)


async def lookup_news(keyword: str) -> dict:

    if not keyword.strip():
        return {
            "error":     "Search keyword cannot be empty",
            "_source":   "validation",
            "_fallback": False,
            "_ms":       0,
            "_legal":    LEGAL_NOTE,
        }

    # ── GNews API (if key configured) ────────────────────────────
    if settings.GNEWS_API_KEY:
        data, source, is_fallback, ms = await safe_fetch(
            primary_url    = "https://gnews.io/api/v4/search",
            fallback_url   = "https://api.gdeltproject.org/api/v2/doc/doc",
            primary_label  = "GNews API",
            fallback_label = "GDELT [fallback]",
            params = {
                "q":       keyword,
                "lang":    "en",
                "country": "in",
                "max":     10,
                "apikey":  settings.GNEWS_API_KEY,
            },
        )
    else:
        # GDELT — no key needed, always available
        data, source, is_fallback, ms = await safe_fetch(
            primary_url    = "https://api.gdeltproject.org/api/v2/doc/doc",
            primary_label  = "GDELT (no key required)",
            fallback_url   = None,
            params = {
                "query":       f"{keyword} sourcecountry:India",
                "mode":        "artlist",
                "maxrecords":  10,
                "format":      "json",
                "sort":        "DateDesc",
            },
        )

    if data is None:
        return {
            "error":          "News APIs unreachable.",
            "gnews_register": "https://gnews.io/register",
            "query":          keyword,
            "_source":        "none",
            "_fallback":      False,
            "_ms":            ms,
            "_legal":         LEGAL_NOTE,
        }

    articles = []

    # ── Normalise GNews response ──────────────────────────────────
    if "articles" in data and isinstance(data["articles"], list):
        for a in data["articles"]:
            articles.append({
                "title":       a.get("title"),
                "description": a.get("description"),
                "url":         a.get("url"),
                "source":      a.get("source", {}).get("name"),
                "published":   a.get("publishedAt"),
                "image":       a.get("image"),
            })

    # ── Normalise GDELT response ──────────────────────────────────
    elif isinstance(data, dict):
        gdelt_articles = data.get("articles", [])
        for a in gdelt_articles:
            articles.append({
                "title":       a.get("title"),
                "description": None,
                "url":         a.get("url"),
                "source":      a.get("domain"),
                "published":   a.get("seendate"),
                "image":       None,
            })

    return {
        "query":     keyword,
        "count":     len(articles),
        "articles":  articles,
        "_source":   source,
        "_fallback": is_fallback,
        "_ms":       ms,
        "_legal":    LEGAL_NOTE,
    }
