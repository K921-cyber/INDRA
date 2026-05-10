import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import settings
from database import SessionLocal
from models import FeedItem, ApiStatus
from fetch_utils import safe_fetch_xml, safe_fetch


logger    = logging.getLogger("indra.scheduler")
scheduler = AsyncIOScheduler()

async def fetch_certin_feed():
    """
    Fetch CERT-In / cyber advisory feed.
    Primary:  CERT-In RSS (may be blocked — detected by HTML response)
    Fallback: NVD NIST RSS (covers same CVEs, always accessible)
    Source:   Govt. of India public info / NIST public data
    """
    logger.info("[Scheduler] Fetching cyber advisory feed...")

    source_label = "CERT-In"

    # ── Try CERT-In first ─────────────────────────────────────────
    text, ms = await safe_fetch_xml(
        "https://www.cert-in.org.in/RSS_FEEDS/rss_certin_alerts.xml",
        label   = "CERT-In RSS",
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
            "Referer": "https://www.cert-in.org.in/",
        },
    )

    # Detect HTML response (bot block)
    if not text or text.strip().startswith("<!") or "<html" in text[:200].lower():
        logger.warning("[Scheduler] CERT-In blocked — switching to NVD NIST fallback")
        source_label = "NVD NIST"
        text, ms = await safe_fetch_xml(
            "https://nvd.nist.gov/feeds/xml/cve/misc/nvd-rss.xml",
            label   = "NVD NIST RSS",
            headers = {"User-Agent": "INDRA-OSINT/2.1 (academic research)"},
        )

    if not text:
        logger.warning("[Scheduler] All cyber advisory sources unreachable")
        return

    db = SessionLocal()
    try:
        # Strip XML namespaces so findall works regardless of feed format
        import re
        clean_text = re.sub(r'\s+xmlns[^"]*"[^"]*"', '', text)
        clean_text = re.sub(r'<(/?)[\w]+:', r'<\1', clean_text)

        try:
            root = ET.fromstring(clean_text)
        except ET.ParseError:
            # If namespace stripping broke it, try raw parse
            root = ET.fromstring(text)

        # Find items — works for RSS <item> and Atom <entry>
        items = (
            root.findall(".//item")
            or root.findall(".//entry")
            or root.findall(".//channel/item")
        )

        logger.info(f"[Scheduler] Found {len(items)} items in {source_label} feed")
        new_count = 0

        for item in items[:20]:
            # Title — try multiple tag names
            title = (
                (item.findtext("title")   or "")
                or (item.findtext("name")  or "")
            ).strip()

            # Link — RSS uses <link>, Atom uses <link> attr or <id>
            link_el = item.find("link")
            if link_el is not None:
                link = (link_el.text or link_el.get("href") or "").strip()
            else:
                link = (item.findtext("id") or "").strip()

            # Description — try multiple tag names
            desc = (
                (item.findtext("description") or "")
                or (item.findtext("summary")   or "")
                or (item.findtext("content")   or "")
            ).strip()

            pub = (
                item.findtext("pubDate")
                or item.findtext("published")
                or item.findtext("updated")
            )

            if not title:
                continue

            # Deduplication check
            exists = (
                db.query(FeedItem)
                .filter(
                    FeedItem.source == "CERT-In",
                    FeedItem.title  == title[:490],
                )
                .first()
            )
            if exists:
                continue

            # Severity detection from title
            severity    = "medium"
            title_lower = title.lower()
            if any(k in title_lower for k in [
                "critical", "remote code", "zero-day", "zero day",
                "ransomware", "rce", "cvss 9", "cvss 10"
            ]):
                severity = "high"
            elif any(k in title_lower for k in [
                "low", "information", "informational", "cvss 1",
                "cvss 2", "cvss 3"
            ]):
                severity = "low"

            # Parse date
            pub_dt = None
            if pub:
                try:
                    from email.utils import parsedate_to_datetime
                    pub_dt = parsedate_to_datetime(pub)
                except Exception:
                    try:
                        from datetime import datetime
                        pub_dt = datetime.fromisoformat(
                            pub.replace("Z", "+00:00")
                        )
                    except Exception:
                        pub_dt = None

            db.add(FeedItem(
                source       = "CERT-In",
                title        = title[:490],
                summary      = desc[:1000] if desc else None,
                url          = link[:990]  if link else None,
                severity     = severity,
                category     = "Cybersecurity",
                published_at = pub_dt,
            ))
            new_count += 1

        db.commit()
        logger.info(
            f"[Scheduler] CERT-In feed: +{new_count} new items "
            f"(source: {source_label})"
        )

    except ET.ParseError as e:
        logger.error(f"[Scheduler] XML parse error: {e}")
        db.rollback()
    except Exception as e:
        logger.error(f"[Scheduler] Unexpected error: {e}")
        db.rollback()
    finally:
        db.close()
        """
    Fetch CERT-In / cyber advisory feed.
    Primary:  CERT-In RSS (may be blocked — detected by HTML response)
    Fallback: NVD NIST RSS (covers same CVEs, always accessible)
    Source:   Govt. of India public info / NIST public data
    """
    logger.info("[Scheduler] Fetching cyber advisory feed...")

    source_label = "CERT-In"

    # ── Try CERT-In first ─────────────────────────────────────────
    text, ms = await safe_fetch_xml(
        "https://www.cert-in.org.in/RSS_FEEDS/rss_certin_alerts.xml",
        label   = "CERT-In RSS",
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
            "Referer": "https://www.cert-in.org.in/",
        },
    )

    # Detect HTML response (bot block)
    if not text or text.strip().startswith("<!") or "<html" in text[:200].lower():
        logger.warning("[Scheduler] CERT-In blocked — switching to NVD NIST fallback")
        source_label = "NVD NIST"
        text, ms = await safe_fetch_xml(
            "https://nvd.nist.gov/feeds/xml/cve/misc/nvd-rss.xml",
            label   = "NVD NIST RSS",
            headers = {"User-Agent": "INDRA-OSINT/2.1 (academic research)"},
        )

    if not text:
        logger.warning("[Scheduler] All cyber advisory sources unreachable")
        return

    db = SessionLocal()
    try:
        # Strip XML namespaces so findall works regardless of feed format
        import re
        clean_text = re.sub(r'\s+xmlns[^"]*"[^"]*"', '', text)
        clean_text = re.sub(r'<(/?)[\w]+:', r'<\1', clean_text)

        try:
            root = ET.fromstring(clean_text)
        except ET.ParseError:
            # If namespace stripping broke it, try raw parse
            root = ET.fromstring(text)

        # Find items — works for RSS <item> and Atom <entry>
        items = (
            root.findall(".//item")
            or root.findall(".//entry")
            or root.findall(".//channel/item")
        )

        logger.info(f"[Scheduler] Found {len(items)} items in {source_label} feed")
        new_count = 0

        for item in items[:20]:
            # Title — try multiple tag names
            title = (
                (item.findtext("title")   or "")
                or (item.findtext("name")  or "")
            ).strip()

            # Link — RSS uses <link>, Atom uses <link> attr or <id>
            link_el = item.find("link")
            if link_el is not None:
                link = (link_el.text or link_el.get("href") or "").strip()
            else:
                link = (item.findtext("id") or "").strip()

            # Description — try multiple tag names
            desc = (
                (item.findtext("description") or "")
                or (item.findtext("summary")   or "")
                or (item.findtext("content")   or "")
            ).strip()

            pub = (
                item.findtext("pubDate")
                or item.findtext("published")
                or item.findtext("updated")
            )

            if not title:
                continue

            # Deduplication check
            exists = (
                db.query(FeedItem)
                .filter(
                    FeedItem.source == "CERT-In",
                    FeedItem.title  == title[:490],
                )
                .first()
            )
            if exists:
                continue

            # Severity detection from title
            severity    = "medium"
            title_lower = title.lower()
            if any(k in title_lower for k in [
                "critical", "remote code", "zero-day", "zero day",
                "ransomware", "rce", "cvss 9", "cvss 10"
            ]):
                severity = "high"
            elif any(k in title_lower for k in [
                "low", "information", "informational", "cvss 1",
                "cvss 2", "cvss 3"
            ]):
                severity = "low"

            # Parse date
            pub_dt = None
            if pub:
                try:
                    from email.utils import parsedate_to_datetime
                    pub_dt = parsedate_to_datetime(pub)
                except Exception:
                    try:
                        from datetime import datetime
                        pub_dt = datetime.fromisoformat(
                            pub.replace("Z", "+00:00")
                        )
                    except Exception:
                        pub_dt = None

            db.add(FeedItem(
                source       = "CERT-In",
                title        = title[:490],
                summary      = desc[:1000] if desc else None,
                url          = link[:990]  if link else None,
                severity     = severity,
                category     = "Cybersecurity",
                published_at = pub_dt,
            ))
            new_count += 1

        db.commit()
        logger.info(
            f"[Scheduler] CERT-In feed: +{new_count} new items "
            f"(source: {source_label})"
        )

    except ET.ParseError as e:
        logger.error(f"[Scheduler] XML parse error: {e}")
        db.rollback()
    except Exception as e:
        logger.error(f"[Scheduler] Unexpected error: {e}")
        db.rollback()
    finally:
        db.close()
    """
    Fetch CERT-In security advisories RSS feed.
    Source: cert-in.org.in — Govt. of India public information.
    """
    logger.info("[Scheduler] Fetching CERT-In RSS...")
    url      = "https://www.cert-in.org.in/RSS_FEEDS/rss_certin_alerts.xml"
    text, ms = await safe_fetch_xml(
        url,
        label   = "CERT-In RSS",
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
        },
    )
  # CERT-In sometimes blocks bots and returns HTML — detect and fallback
    if not text or text.strip().startswith("<!"):
        logger.warning("[Scheduler] CERT-In returned HTML (bot block) — trying NVD fallback")
        text, ms = await safe_fetch_xml(
            "https://nvd.nist.gov/feeds/xml/cve/misc/nvd-rss.xml",
            label   = "NVD NIST RSS [fallback]",
            headers = {"User-Agent": "INDRA-OSINT/2.1 (academic research)"},
        )
        if not text or text.strip().startswith("<!"):
            logger.warning("[Scheduler] Both CERT-In and NVD unreachable — will retry next cycle")
            return

    db = SessionLocal()
    try:
        root    = ET.fromstring(text)
        channel = root.find("channel")
        items   = channel.findall("item") if channel else root.findall(".//item")
        new_count = 0

        for item in items[:20]:
            title = (item.findtext("title")       or "").strip()
            link  = (item.findtext("link")        or "").strip()
            desc  = (item.findtext("description") or "").strip()
            pub   = item.findtext("pubDate")

            if not title:
                continue

            exists = (
                db.query(FeedItem)
                .filter(
                    FeedItem.source == "CERT-In",
                    FeedItem.title  == title[:490],
                )
                .first()
            )
            if exists:
                continue

            severity    = "medium"
            title_lower = title.lower()
            if any(k in title_lower for k in [
                "critical", "remote code", "zero-day",
                "ransomware", "zero day", "rce"
            ]):
                severity = "high"
            elif any(k in title_lower for k in [
                "low", "information", "informational"
            ]):
                severity = "low"

            pub_dt = None
            if pub:
                try:
                    from email.utils import parsedate_to_datetime
                    pub_dt = parsedate_to_datetime(pub)
                except Exception:
                    pub_dt = None

            db.add(FeedItem(
                source       = "CERT-In",
                title        = title[:490],
                summary      = desc[:1000] if desc else None,
                url          = link[:990]  if link else None,
                severity     = severity,
                category     = "Cybersecurity",
                published_at = pub_dt,
            ))
            new_count += 1

        db.commit()
        logger.info(f"[Scheduler] CERT-In: +{new_count} new items stored")

    except ET.ParseError as e:
        logger.error(f"[Scheduler] CERT-In XML parse error: {e}")
        db.rollback()
    except Exception as e:
        logger.error(f"[Scheduler] CERT-In unexpected error: {e}")
        db.rollback()
    finally:
        db.close()


async def fetch_boomlive_feed():
    """
    Fetch BoomLive India fact-check RSS feed.
    Source: boomlive.in — Public RSS, editorial content.
    """
    logger.info("[Scheduler] Fetching BoomLive RSS...")

    url      = "https://www.boomlive.in/feed"
    text, ms = await safe_fetch_xml(url, label="BoomLive RSS")

    if not text:
        logger.warning("[Scheduler] BoomLive RSS unreachable — will retry next cycle")
        return

    db = SessionLocal()
    try:
        root      = ET.fromstring(text)
        items     = root.findall(".//item")
        new_count = 0

        for item in items[:15]:
            title = (item.findtext("title")       or "").strip()
            link  = (item.findtext("link")        or "").strip()
            desc  = (item.findtext("description") or "").strip()
            pub   = item.findtext("pubDate")

            if not title:
                continue

            exists = (
                db.query(FeedItem)
                .filter(
                    FeedItem.source == "BoomLive",
                    FeedItem.title  == title[:490],
                )
                .first()
            )
            if exists:
                continue

            pub_dt = None
            if pub:
                try:
                    from email.utils import parsedate_to_datetime
                    pub_dt = parsedate_to_datetime(pub)
                except Exception:
                    pub_dt = None

            db.add(FeedItem(
                source       = "BoomLive",
                title        = title[:490],
                summary      = desc[:1000] if desc else None,
                url          = link[:990]  if link else None,
                severity     = "medium",
                category     = "Fact-Check / Disinformation",
                published_at = pub_dt,
            ))
            new_count += 1

        db.commit()
        logger.info(f"[Scheduler] BoomLive: +{new_count} new items stored")

    except ET.ParseError as e:
        logger.error(f"[Scheduler] BoomLive XML parse error: {e}")
        db.rollback()
    except Exception as e:
        logger.error(f"[Scheduler] BoomLive unexpected error: {e}")
        db.rollback()
    finally:
        db.close()


async def ping_apis():
    """
    Ping all external APIs and update api_status table.
    Runs every 10 minutes.
    """
    logger.info("[Scheduler] Pinging API health...")

    apis_to_check = [
        {
            "name":         "ip-api.com",
            "url":          "http://ip-api.com/json/8.8.8.8",
            "requires_key": False,
            "license":      "Non-commercial CC Attribution",
        },
        {
            "name":         "rdap.org",
            "url":          "https://rdap.org/domain/google.com",
            "requires_key": False,
            "license":      "Public RDAP Protocol",
        },
        {
            "name":         "Nominatim/OSM",
            "url":          "https://nominatim.openstreetmap.org/status",
            "requires_key": False,
            "license":      "ODbL Attribution Required",
        },
        {
            "name":         "data.gov.in",
            "url":          "https://api.data.gov.in",
            "requires_key": True,
            "license":      "OGDL-India 1.0",
        },
        {
            "name":         "GDELT",
            "url":          (
                "https://api.gdeltproject.org/api/v2/doc/doc"
                "?query=india&mode=artlist&maxrecords=1&format=json"
            ),
            "requires_key": False,
            "license":      "Open Data",
        },
        {
            "name":         "AbuseIPDB",
            "url":          "https://api.abuseipdb.com",
            "requires_key": True,
            "license":      "AbuseIPDB ToS",
        },
    ]

    db = SessionLocal()
    try:
        import httpx
        import time

        for api in apis_to_check:
            start   = time.monotonic()
            healthy = False
            ms      = None

            try:
                async with httpx.AsyncClient(timeout=6.0) as client:
                    resp = await client.get(
                        api["url"],
                        headers={"User-Agent": "INDRA-HealthCheck/2.1"},
                    )
                    ms      = int((time.monotonic() - start) * 1000)
                    healthy = resp.status_code < 500
            except Exception:
                ms = int((time.monotonic() - start) * 1000)

            key_configured = False
            if api["name"] == "data.gov.in":
                key_configured = bool(settings.DATA_GOV_IN_API_KEY)
            elif api["name"] == "AbuseIPDB":
                key_configured = bool(settings.ABUSEIPDB_API_KEY)

            record = (
                db.query(ApiStatus)
                .filter(ApiStatus.api_name == api["name"])
                .first()
            )

            if record:
                record.is_healthy       = healthy           # type: ignore[assignment]
                record.last_response_ms = ms                # type: ignore[assignment]
                record.last_checked     = datetime.now(timezone.utc)  # type: ignore[assignment]
                record.key_configured   = key_configured    # type: ignore[assignment]
            else:
                db.add(ApiStatus(
                    api_name         = api["name"],
                    base_url         = api["url"],
                    is_healthy       = healthy,
                    last_response_ms = ms,
                    last_checked     = datetime.now(timezone.utc),
                    requires_key     = api["requires_key"],
                    key_configured   = key_configured,
                    license_type     = api["license"],
                ))

        db.commit()
        logger.info("[Scheduler] API health updated for all APIs")

    except Exception as e:
        logger.error(f"[Scheduler] Health ping error: {e}")
        db.rollback()
    finally:
        db.close()


def start_scheduler():
    """Start all jobs. Called from main.py lifespan on startup."""
    interval = settings.FEED_REFRESH_INTERVAL_MINUTES

    scheduler.add_job(
        fetch_certin_feed,
        trigger          = IntervalTrigger(minutes=interval),
        id               = "certin_feed",
        replace_existing = True,
    )
    scheduler.add_job(
        fetch_boomlive_feed,
        trigger          = IntervalTrigger(minutes=interval),
        id               = "boomlive_feed",
        replace_existing = True,
    )
    scheduler.add_job(
        ping_apis,
        trigger          = IntervalTrigger(minutes=10),
        id               = "api_health",
        replace_existing = True,
    )

    scheduler.start()
    logger.info(
        f"[Scheduler] Started — feeds every {interval} min, "
        f"health ping every 10 min"
    )


def stop_scheduler():
    """Stop scheduler cleanly. Called from main.py lifespan on shutdown."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[Scheduler] Stopped cleanly")