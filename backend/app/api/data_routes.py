"""
TRINETRA — Data & Health API Routes

Provides endpoints for:
  - Real NCRB crime statistics by state
  - Health status of all data sources (threat feeds, geo-location, RSS news)
"""

import logging
from fastapi import APIRouter
from datetime import datetime, timezone

from app.data.ncrb_crime_data import get_ncrb_data
from app.services.real_threat_service import real_threat_service
from app.services.real_news_service import real_news_service

logger = logging.getLogger("trinetra.data_routes")
router = APIRouter(prefix="/api", tags=["data"])

# Feed source URLs for the health panel
FEED_SOURCE_DETAILS = {
    "ThreatFox": {
        "url": "https://threatfox.abuse.ch/export/csv/recent/",
        "description": "Malware IOC feed — threat types & malware families",
    },
    "Feodo": {
        "url": "https://feodotracker.abuse.ch/downloads/ipblocklist.csv",
        "description": "Active C2 server IPs tracked by Abuse.ch",
    },
    "IPsum": {
        "url": "https://raw.githubusercontent.com/stamparm/ipsum/master/ipsum.txt",
        "description": "Aggregated blacklist with detection scores",
    },
    "ip-api.com": {
        "url": "http://ip-api.com/json/",
        "description": "Free IP geo-location (45 req/min limit)",
    },
}

RSS_FEED_DETAILS = {
    "The Hacker News": {"url": "https://feeds.feedburner.com/TheHackersNews"},
    "BleepingComputer": {"url": "https://www.bleepingcomputer.com/feed/"},
    "KrebsOnSecurity": {"url": "https://krebsonsecurity.com/feed/"},
    "The Record": {"url": "https://therecord.media/feed/"},
}


@router.get("/crime-data")
async def get_crime_data():
    """Get real NCRB 2022 cyber crime data by Indian state."""
    data = get_ncrb_data()
    logger.info(
        "Serving NCRB crime data: %d states, %d total cases",
        len(data["states"]), data["total_cases"]
    )
    return data


@router.get("/health/sources")
async def get_data_source_health():
    """Get health status of all live data sources used by the dashboard.

    Returns the status of threat feeds, geo-location, and RSS news feeds,
    including last fetch time, counts, and any errors.
    """
    threat_health = real_threat_service.get_source_health()

    # Build threat feed health with details
    feeds = {}
    for name, health in threat_health.items():
        details = FEED_SOURCE_DETAILS.get(name, {})
        feeds[name] = {
            "status": health.get("status", "unknown"),
            "last_fetch": health.get("last_fetch"),
            "error": health.get("error"),
            "url": details.get("url", ""),
            "description": details.get("description", ""),
            "metrics": {
                k: v for k, v in health.items()
                if k not in ("status", "last_fetch", "error")
            },
        }

    # Build RSS feed health
    rss_health = real_news_service.get_feed_health()
    rss_feeds = {}
    for name, health in rss_health.items():
        details = RSS_FEED_DETAILS.get(name, {})
        rss_feeds[name] = {
            "status": health.get("status", "unknown"),
            "last_fetch": health.get("last_fetch"),
            "error": health.get("error"),
            "url": details.get("url", ""),
            "metrics": {
                k: v for k, v in health.items()
                if k not in ("status", "last_fetch", "error")
            },
        }

    # NCRB data status
    ncrb_status = {
        "source": "NCRB Crime in India 2022",
        "status": "static",
        "description": "Annual report data — updated yearly",
        "year": 2022,
    }

    # Overall system health
    all_healthy = all(
        h.get("status") == "healthy" for h in feeds.values()
    )
    all_rss_healthy = all(
        h.get("status") == "healthy" for h in rss_feeds.values()
    )

    return {
        "overall": {
            "status": "healthy" if (all_healthy or all_rss_healthy) else "degraded",
            "threat_feeds_healthy": all_healthy,
            "rss_feeds_healthy": all_rss_healthy,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "threat_intel_feeds": feeds,
        "news_rss_feeds": rss_feeds,
        "reference_data": ncrb_status,
    }
