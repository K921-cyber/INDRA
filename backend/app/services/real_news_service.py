"""
TRINETRA — Real News Feed Service

Fetches real cyber security news from public RSS feeds.
No API keys required — uses free RSS/Atom feeds from major
cyber news outlets.

Sources:
  - The Hacker News (feedburner)
  - BleepingComputer
  - KrebsOnSecurity
  - CyberScoop
  - The Record (Recorded Future)
"""

import asyncio
import logging
import feedparser
from datetime import datetime, timezone
from typing import Optional

# Max seen URLs to track for deduplication
_MAX_SEEN_URLS = 2000

logger = logging.getLogger("trinetra.real_news")

# RSS feed sources (public, no API key required)
RSS_FEEDS = [
    {"name": "The Hacker News", "url": "https://feeds.feedburner.com/TheHackersNews", "icon": "📰"},
    {"name": "BleepingComputer", "url": "https://www.bleepingcomputer.com/feed/", "icon": "💻"},
    {"name": "KrebsOnSecurity", "url": "https://krebsonsecurity.com/feed/", "icon": "🔒"},
    {"name": "The Record", "url": "https://therecord.media/feed/", "icon": "📝"},
]

# Attack type keywords to categorize news
ATTACK_KEYWORDS = {
    "ransomware": "Ransomware",
    "phishing": "Phishing",
    "ddos": "DDoS",
    "malware": "Malware",
    "trojan": "Malware",
    "botnet": "Botnet",
    "apt": "APT Attack",
    "zero-day": "Zero-Day Exploit",
    "data breach": "Data Breach",
    "vulnerability": "Vulnerability",
    "exploit": "Exploit",
    "supply chain": "Supply Chain Attack",
}


def _categorize_attack(title: str, summary: str) -> str:
    """Categorize a news headline into an attack type."""
    text = (title + " " + summary).lower()
    for keyword, attack_type in ATTACK_KEYWORDS.items():
        if keyword in text:
            return attack_type
    return "Cyber Attack"


def _determine_severity(text: str) -> str:
    """Determine severity based on keywords."""
    text = text.lower()
    critical_words = ["critical", "emergency", "urgent", "0-day", "zero-day", "massive", "major"]
    medium_words = ["warning", "alert", "threat", "vulnerability", "attack"]
    for w in critical_words:
        if w in text:
            return "critical"
    for w in medium_words:
        if w in text:
            return "medium"
    return "medium"


class RealNewsService:
    """Fetches real cyber news from public RSS feeds."""

    def __init__(self):
        self._latest_headlines: list[dict] = []
        self._running = False
        self._task: asyncio.Task | None = None
        self._seen_urls: set[str] = set()
        # RSS feed health tracking
        self._feed_health: dict[str, dict] = {
            f["name"]: {"status": "unknown", "last_fetch": None, "articles": 0, "error": None}
            for f in RSS_FEEDS
        }

    async def start(self):
        """Start the background news fetcher."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._fetch_loop())

    async def stop(self):
        """Stop the background news fetcher."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    def get_latest(self, count: int = 20) -> list[dict]:
        """Get the latest headlines."""
        return self._latest_headlines[:count]

    def get_feed_health(self) -> dict[str, dict]:
        """Get health status of all RSS news feeds."""
        return dict(self._feed_health)

    async def _fetch_single_feed(self, feed_info: dict) -> list[dict]:
        """Fetch and parse a single RSS feed."""
        entries = []
        feed_name = feed_info["name"]
        try:
            # Run feedparser in executor since it's synchronous
            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(
                None, lambda: feedparser.parse(feed_info["url"])
            )

            if feed.bozo and not feed.entries:
                logger.warning("Failed to parse feed: %s", feed_info["url"])
                self._feed_health[feed_name] = {
                    "status": "error", "last_fetch": datetime.now(timezone.utc).isoformat(),
                    "articles": 0, "error": "Failed to parse RSS feed"
                }
                return entries

            for entry in feed.entries[:10]:  # max 10 per feed
                link = entry.get("link", "")
                if link in self._seen_urls:
                    continue
                self._seen_urls.add(link)
                # Prune seen URLs set to prevent unbounded growth
                if len(self._seen_urls) > _MAX_SEEN_URLS:
                    # Keep only the most recent half
                    self._seen_urls = set(list(self._seen_urls)[-_MAX_SEEN_URLS//2:])

                title = entry.get("title", "Untitled")
                summary = entry.get("summary", "") or entry.get("description", "")
                published = entry.get("published_parsed")
                if published:
                    timestamp = datetime(*published[:6], tzinfo=timezone.utc).isoformat()
                else:
                    timestamp = datetime.now(timezone.utc).isoformat()

                attack_type = _categorize_attack(title, summary)
                severity = _determine_severity(title)

                entries.append({
                    "type": "news_event",
                    "id": f"news-{len(self._seen_urls)}",
                    "text": title,
                    "url": link,
                    "icon": feed_info["icon"],
                    "severity": severity,
                    "attackType": attack_type,
                    "source": feed_info["name"],
                    "timestamp": timestamp,
                })

            self._feed_health[feed_name] = {
                "status": "healthy", "last_fetch": datetime.now(timezone.utc).isoformat(),
                "articles": len(entries), "error": None
            }

        except Exception as e:
            logger.error("Error fetching feed %s: %s", feed_info["url"], e)
            self._feed_health[feed_name] = {
                "status": "error", "last_fetch": datetime.now(timezone.utc).isoformat(),
                "articles": len(entries), "error": str(e)[:100]
            }

        return entries

    async def _fetch_loop(self):
        """Background loop that fetches RSS feeds periodically."""
        try:
            await asyncio.sleep(5)  # initial delay

            while self._running:
                all_entries = []
                for feed_info in RSS_FEEDS:
                    entries = await self._fetch_single_feed(feed_info)
                    all_entries.extend(entries)
                    await asyncio.sleep(1)  # be polite between feed fetches

                # Sort by timestamp (newest first)
                all_entries.sort(
                    key=lambda e: e["timestamp"], reverse=True
                )

                if all_entries:
                    self._latest_headlines = all_entries + self._latest_headlines
                    # Keep max 200 headlines
                    if len(self._latest_headlines) > 200:
                        self._latest_headlines = self._latest_headlines[:200]
                    logger.info(
                        "Fetched %d new news items from %d feeds",
                        len(all_entries), len(RSS_FEEDS)
                    )

                # Fetch every 5 minutes
                await asyncio.sleep(300)

        except asyncio.CancelledError:
            pass


# Singleton
real_news_service = RealNewsService()
