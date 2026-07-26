"""
TRINETRA — Threat Feed Service

Generates and broadcasts real-time threat events over WebSocket using
real data from free threat intelligence sources (Abuse.ch, Feodo Tracker,
IPsum) and real cyber news from RSS feeds (TheHackerNews, BleepingComputer, etc.).

No API keys required.

City marker data is derived from NCRB 2022 cyber crime statistics (real government data).
"""

import asyncio
import logging
import random
from datetime import datetime, timezone

from app.services.real_news_service import real_news_service
from app.services.real_threat_service import real_threat_service

logger = logging.getLogger("trinetra.threat_feed")


def _get_ncrb_city_data():
    """Build city marker data from real NCRB crime statistics.
    
    Maps major Indian cities to their state's NCRB incident counts
    to derive meaningful risk levels and asset counts.
    """
    from app.data.ncrb_crime_data import NCRB_CRIME_DATA_2022
    
    # Major Indian cities mapped to their states with coordinates
    CITIES = [
        {"name": "New Delhi", "lat": 28.6139, "lng": 77.2090, "state": "Delhi"},
        {"name": "Mumbai", "lat": 19.0760, "lng": 72.8777, "state": "Maharashtra"},
        {"name": "Bangalore", "lat": 12.9716, "lng": 77.5946, "state": "Karnataka"},
        {"name": "Hyderabad", "lat": 17.3850, "lng": 78.4867, "state": "Telangana"},
        {"name": "Chennai", "lat": 13.0827, "lng": 80.2707, "state": "Tamil Nadu"},
        {"name": "Kolkata", "lat": 22.5726, "lng": 88.3639, "state": "West Bengal"},
        {"name": "Pune", "lat": 18.5204, "lng": 73.8567, "state": "Maharashtra"},
        {"name": "Ahmedabad", "lat": 23.0225, "lng": 72.5714, "state": "Gujarat"},
        {"name": "Jaipur", "lat": 26.9124, "lng": 75.7873, "state": "Rajasthan"},
        {"name": "Srinagar", "lat": 34.0837, "lng": 74.7973, "state": "Jammu & Kashmir"},
    ]
    
    # Build state → incident count map
    state_crime = {d["state"]: d["incidentCount"] for d in NCRB_CRIME_DATA_2022}
    max_incidents = max(state_crime.values()) if state_crime else 1
    threshold_critical = max_incidents * 0.4
    threshold_medium = max_incidents * 0.1
    
    result = []
    for c in CITIES:
        count = state_crime.get(c["state"], 0)
        
        # Derive risk from NCRB data
        if count >= threshold_critical:
            risk = "critical"
        elif count >= threshold_medium:
            risk = "medium"
        else:
            risk = "safe"
        
        # assetCount: proportional to NCRB incident count (higher crime = more digital infrastructure)
        normalized = count / max_incidents if max_incidents > 0 else 0
        asset_count = int(500 + normalized * 3000)  # Range: 500–3500
        
        # activeThreats: proportional to risk level
        if risk == "critical":
            active_threats = random.randint(8, 15)
        elif risk == "medium":
            active_threats = random.randint(3, 7)
        else:
            active_threats = random.randint(0, 2)
        
        result.append({
            "name": c["name"],
            "lat": c["lat"],
            "lng": c["lng"],
            "risk": risk,
            "assetCount": asset_count,
            "activeThreats": active_threats,
            "note": "Active threat count is estimated based on NCRB crime statistics",
        })
    
    return result


class ThreatFeedService:
    """Generates and broadcasts real-time threat events over WebSocket.
    
    Uses real data from:
      - RealThreatService: malicious IPs from Abuse.ch, geo-located via ip-api.com
      - RealNewsService: cyber news headlines from RSS feeds
      - NCRB: city marker data from official government cyber crime statistics
    """

    def __init__(self):
        self._subscribers: list[asyncio.Queue] = []
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self):
        """Start the background threat event generator."""
        if self._running:
            return
        self._running = True

        await real_threat_service.start()
        await real_news_service.start()

        self._task = asyncio.create_task(self._generate_events_loop())
        logger.info("Threat feed started — real IPs from Abuse.ch, geo from ip-api.com, news from RSS, city data from NCRB")

    async def stop(self):
        """Stop the background threat event generator."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await real_threat_service.stop()
        await real_news_service.stop()

    def subscribe(self) -> asyncio.Queue:
        """Subscribe to the threat feed. Returns a Queue that receives events."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=50)
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        """Unsubscribe from the threat feed."""
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    async def _broadcast(self, event: dict):
        """Broadcast an event to all subscribers."""
        dead = []
        for q in self._subscribers:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                dead.append(q)
        for q in dead:
            self._subscribers.remove(q)

    async def _generate_events_loop(self):
        """Background loop that broadcasts events at a throttled rate."""
        try:
            await asyncio.sleep(3)
            last_news_index = 0

            while self._running:
                # --- Broadcast 1 attack vector every 8-12 seconds (reduced from 2-5) ---
                vectors = real_threat_service.get_active_vectors(30)
                if vectors:
                    batch = random.sample(vectors, min(1, len(vectors)))
                    for v in batch:
                        await self._broadcast(v)

                # --- Broadcast 1 news headline per cycle, wrapping around when exhausted ---
                news = real_news_service.get_latest(50)
                if news:
                    # Reset index if we've broadcast all available news
                    if last_news_index >= len(news):
                        last_news_index = 0
                    await self._broadcast(news[last_news_index])
                    last_news_index += 1

                # Throttled interval: 8-12 seconds (was 2-5)
                await asyncio.sleep(random.uniform(8.0, 12.0))

        except asyncio.CancelledError:
            pass

    def get_initial_state(self) -> dict:
        """Get the current state for a newly connected client using real data."""
        events = []

        vectors = real_threat_service.get_active_vectors(20)
        for v in vectors:
            events.append(v)

        news = real_news_service.get_latest(10)
        for n in news:
            events.append(n)

        return {
            "type": "initial_state",
            "events": events,
            "cities": _get_ncrb_city_data(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# Singleton instance
threat_feed = ThreatFeedService()
