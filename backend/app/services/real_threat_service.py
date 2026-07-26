"""
TRINETRA — Real Threat Intelligence Service

Fetches real malicious IP addresses from free threat intel feeds
(Abuse.ch ThreatFox, Feodo Tracker) and geo-locates them to
generate real attack vector data for the map.

No API keys required — uses public CSV/data dumps.

Sources:
  - ThreatFox: https://threatfox.abuse.ch/export/csv/recent/
  - Feodo Tracker: https://feodotracker.abuse.ch/downloads/ipblocklist.csv
  - IPsum (aggregate): https://raw.githubusercontent.com/stamparm/ipsum/master/ipsum.txt

Geo-location:
  - ip-api.com (free, 45 req/min, no key required)
  - Results are cached in-memory to minimize API calls
"""

import asyncio
import csv
import io
import logging
import random
import re
import time
from datetime import datetime, timezone
from typing import Optional, Dict, List

import aiohttp

logger = logging.getLogger("trinetra.real_threat")

# Free threat data feeds (no API key required)
THREAT_FEEDS = {
    "feodo": "https://feodotracker.abuse.ch/downloads/ipblocklist.csv",
    "threatfox_recent": "https://threatfox.abuse.ch/export/csv/recent/",
    "ipsum": "https://raw.githubusercontent.com/stamparm/ipsum/master/ipsum.txt",
}

# Indian cities for targeting (real data maps generic threats to Indian visualization)
INDIAN_CITIES = [
    {"name": "New Delhi", "lat": 28.6139, "lng": 77.2090},
    {"name": "Mumbai", "lat": 19.0760, "lng": 72.8777},
    {"name": "Bangalore", "lat": 12.9716, "lng": 77.5946},
    {"name": "Hyderabad", "lat": 17.3850, "lng": 78.4867},
    {"name": "Chennai", "lat": 13.0827, "lng": 80.2707},
    {"name": "Kolkata", "lat": 22.5726, "lng": 88.3639},
    {"name": "Pune", "lat": 18.5204, "lng": 73.8567},
    {"name": "Ahmedabad", "lat": 23.0225, "lng": 72.5714},
    {"name": "Jaipur", "lat": 26.9124, "lng": 75.7873},
    {"name": "Srinagar", "lat": 34.0837, "lng": 74.7973},
]

# Country codes → full names for display
COUNTRY_NAMES = {
    "US": "USA", "CN": "China", "RU": "Russia", "KP": "North Korea",
    "IR": "Iran", "PK": "Pakistan", "BR": "Brazil", "NL": "Netherlands",
    "DE": "Germany", "FR": "France", "GB": "United Kingdom",
    "UA": "Ukraine", "KR": "South Korea", "JP": "Japan",
    "IN": "India", "VN": "Vietnam", "ID": "Indonesia",
    "EG": "Egypt", "TR": "Turkey", "IL": "Israel",
    "SA": "Saudi Arabia", "AE": "UAE", "SG": "Singapore",
    "HK": "Hong Kong", "TW": "Taiwan", "MY": "Malaysia",
    "TH": "Thailand", "ZZ": "Unknown",
}

# Country coordinates for map display (approximate centers)
COUNTRY_COORDS = {
    "USA": (39.8283, -98.5795),
    "China": (35.8617, 104.1954),
    "Russia": (61.5240, 105.3188),
    "North Korea": (40.3399, 127.5101),
    "Iran": (32.4279, 53.6880),
    "Pakistan": (30.3753, 69.3451),
    "Brazil": (-14.2350, -51.9253),
    "Netherlands": (52.1326, 5.2913),
    "Germany": (51.1657, 10.4515),
    "France": (46.6034, 1.8883),
    "United Kingdom": (55.3781, -3.4360),
    "Ukraine": (48.3794, 31.1656),
    "South Korea": (35.9078, 127.7669),
    "Japan": (36.2048, 138.2529),
    "India": (20.5937, 78.9629),
    "Vietnam": (14.0583, 108.2772),
    "Indonesia": (-0.7893, 113.9213),
    "Egypt": (26.8206, 30.8025),
    "Turkey": (38.9637, 35.2433),
    "Israel": (31.0461, 34.8516),
    "Saudi Arabia": (23.8859, 45.0792),
    "Singapore": (1.3521, 103.8198),
    "Hong Kong": (22.3964, 114.1095),
    "Taiwan": (23.6978, 120.9605),
    "Malaysia": (4.2105, 101.9758),
    "Thailand": (15.8700, 100.9925),
    "Unknown": (0, 0),
}

# Map attack types from threat feed data
def _classify_threat(data: str) -> tuple[str, bool]:
    """Classify a threat indicator into an attack type.
    
    Returns (type_str, was_estimated) where was_estimated is True
    when no keywords matched and a random fallback was used.
    """
    data = data.lower()
    if "ransomware" in data or "ransom" in data:
        return "Ransomware", False
    if "phish" in data:
        return "Phishing", False
    if "ddos" in data or "dos" in data:
        return "DDoS", False
    if "botnet" in data or "c2" in data or "command" in data:
        return "Botnet C2", False
    if "malware" in data or "trojan" in data or "agent" in data:
        return "Malware", False
    if "scan" in data or "probe" in data:
        return "Recon Scan", False
    if "exploit" in data or "cve" in data:
        return "Exploit", False
    if "spam" in data:
        return "Spam Campaign", False
    if "brute" in data or "credential" in data:
        return "Brute Force", False
    return random.choice(["Recon Scan", "Malware", "Phishing", "Probe"]), True


class RealThreatService:
    """Fetches real threat IPs and geo-locates them for attack vectors."""

    def __init__(self):
        self._ip_cache: Dict[str, Optional[Dict]] = {}  # IP → geo data
        self._malicious_ips: List[str] = []
        self._active_vectors: List[Dict] = []
        self._running = False
        self._task: asyncio.Task | None = None
        self._event_id = 0
        self._session: aiohttp.ClientSession | None = None
        self._last_geo_check: Dict[str, float] = {}  # rate limiting
        # Per-IP real threat metadata from feeds
        self._ip_metadata: Dict[str, Dict] = {}  # IP → {source, attack_type, malware, score}
        # Data source health tracking
        self._source_health: Dict[str, Dict] = {
            "ThreatFox": {"status": "unknown", "last_fetch": None, "ip_count": 0, "error": None},
            "Feodo": {"status": "unknown", "last_fetch": None, "ip_count": 0, "error": None},
            "IPsum": {"status": "unknown", "last_fetch": None, "ip_count": 0, "error": None},
            "ip-api.com": {"status": "unknown", "last_fetch": None, "geo_lookups": 0, "error": None},
        }

    async def start(self):
        """Start the threat feed fetcher."""
        if self._running:
            return
        self._running = True
        self._session = aiohttp.ClientSession()
        self._task = asyncio.create_task(self._fetch_loop())

    async def stop(self):
        """Stop the threat feed fetcher."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._session:
            await self._session.close()
            self._session = None

    async def _fetch_threatfox_csv(self) -> List[Dict]:
        """Fetch recent IOCs from ThreatFox CSV export with real threat types."""
        results = []
        if not self._session:
            self._source_health["ThreatFox"] = {
                "status": "error", "last_fetch": datetime.now(timezone.utc).isoformat(),
                "ip_count": 0, "error": "No HTTP session"
            }
            return results
        try:
            async with self._session.get(THREAT_FEEDS["threatfox_recent"], timeout=15) as resp:
                if resp.status != 200:
                    logger.warning("ThreatFox returned status %d", resp.status)
                    self._source_health["ThreatFox"] = {
                        "status": "error", "last_fetch": datetime.now(timezone.utc).isoformat(),
                        "ip_count": 0, "error": f"HTTP {resp.status}"
                    }
                    return results
                text = await resp.text()
                reader = csv.reader(io.StringIO(text))
                for row in reader:
                    if not row or row[0].startswith("#") or row[0].startswith("id"):
                        continue
                    # ThreatFox CSV columns:
                    # 0=id, 1=date, 2=threat_type, 3=description, 4=ioc (IP),
                    # 5=ioc_type (malware family), ...
                    if len(row) >= 5:
                        ip = row[4].strip()
                        if not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
                            continue
                        threat_type = row[2].strip() if len(row) > 2 else ""
                        description = row[3].strip() if len(row) > 3 else ""
                        malware_family = row[5].strip() if len(row) > 5 else ""

                        # Classify human-readable attack type from the threat_type field
                        attack_type, type_estimated = _classify_threat(threat_type + " " + description)

                        results.append({
                            "ip": ip,
                            "source": "ThreatFox",
                            "threat_type": threat_type,  # e.g. "botnet_cc", "payload_delivery"
                            "malware": malware_family,    # e.g. "win.nanocore", "js.clearfake"
                            "attack_type": attack_type,   # human-readable: "Botnet C2", "Malware"
                            "description": description[:100] if description else "",
                            "type_estimated": type_estimated,  # True if no keywords matched
                        })
                        if len(results) >= 100:
                            break
                self._source_health["ThreatFox"] = {
                    "status": "healthy", "last_fetch": datetime.now(timezone.utc).isoformat(),
                    "ip_count": len(results), "error": None
                }
        except Exception as e:
            logger.error("Error fetching ThreatFox: %s", e)
            self._source_health["ThreatFox"] = {
                "status": "error", "last_fetch": datetime.now(timezone.utc).isoformat(),
                "ip_count": len(results), "error": str(e)[:100]
            }
        return results

    async def _fetch_feodo_csv(self) -> List[Dict]:
        """Fetch C2 IPs from Feodo Tracker CSV with real malware names."""
        results = []
        if not self._session:
            self._source_health["Feodo"] = {
                "status": "error", "last_fetch": datetime.now(timezone.utc).isoformat(),
                "ip_count": 0, "error": "No HTTP session"
            }
            return results
        try:
            async with self._session.get(THREAT_FEEDS["feodo"], timeout=15) as resp:
                if resp.status != 200:
                    logger.warning("Feodo Tracker returned status %d", resp.status)
                    self._source_health["Feodo"] = {
                        "status": "error", "last_fetch": datetime.now(timezone.utc).isoformat(),
                        "ip_count": 0, "error": f"HTTP {resp.status}"
                    }
                    return results
                text = await resp.text()
                reader = csv.reader(io.StringIO(text))
                for row in reader:
                    if not row or row[0].startswith("#") or row[0].startswith("first"):
                        continue
                    # Feodo CSV: first_seen, dst_ip, port, c2_status, last_online, malware
                    if len(row) >= 2:
                        ip = row[1].strip()
                        if not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
                            continue
                        malware_name = row[5].strip().strip('"') if len(row) > 5 else ""
                        c2_status = row[3].strip().strip('"') if len(row) > 3 else ""

                        results.append({
                            "ip": ip,
                            "source": "Feodo",
                            "malware": malware_name,   # e.g. "Dridex", "Emotet", "QakBot"
                            "c2_status": c2_status,     # e.g. "online", "offline"
                            "attack_type": "Botnet C2",
                        })
                        if len(results) >= 100:
                            break
                self._source_health["Feodo"] = {
                    "status": "healthy", "last_fetch": datetime.now(timezone.utc).isoformat(),
                    "ip_count": len(results), "error": None
                }
        except Exception as e:
            logger.error("Error fetching Feodo Tracker: %s", e)
            self._source_health["Feodo"] = {
                "status": "error", "last_fetch": datetime.now(timezone.utc).isoformat(),
                "ip_count": len(results), "error": str(e)[:100]
            }
        return results

    async def _fetch_ipsum(self) -> List[Dict]:
        """Fetch malicious IPs from IPsum list with blacklist scores."""
        results = []
        if not self._session:
            self._source_health["IPsum"] = {
                "status": "error", "last_fetch": datetime.now(timezone.utc).isoformat(),
                "ip_count": 0, "error": "No HTTP session"
            }
            return results
        try:
            async with self._session.get(THREAT_FEEDS["ipsum"], timeout=15) as resp:
                if resp.status != 200:
                    logger.warning("IPsum returned status %d", resp.status)
                    self._source_health["IPsum"] = {
                        "status": "error", "last_fetch": datetime.now(timezone.utc).isoformat(),
                        "ip_count": 0, "error": f"HTTP {resp.status}"
                    }
                    return results
                text = await resp.text()
                for line in text.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split()
                    if len(parts) >= 1 and re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", parts[0]):
                        ip = parts[0]
                        score = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
                        results.append({
                            "ip": ip,
                            "source": "IPsum",
                            "score": score,
                            "attack_type": "Recon Scan",
                        })
                        if len(results) >= 100:
                            break
                self._source_health["IPsum"] = {
                    "status": "healthy", "last_fetch": datetime.now(timezone.utc).isoformat(),
                    "ip_count": len(results), "error": None
                }
        except Exception as e:
            logger.error("Error fetching IPsum: %s", e)
            self._source_health["IPsum"] = {
                "status": "error", "last_fetch": datetime.now(timezone.utc).isoformat(),
                "ip_count": len(results), "error": str(e)[:100]
            }
        return results

    async def _geo_locate_ip(self, ip: str) -> Optional[Dict]:
        """Geo-locate an IP using ip-api.com (free, no key)."""
        # Check cache
        if ip in self._ip_cache:
            return self._ip_cache[ip]

        # Rate limit: max 45 req/min for free tier
        now = time.time()
        if len(self._last_geo_check) >= 40:
            # Check if we can make another request
            oldest = min(self._last_geo_check.values())
            if now - oldest < 60:
                return None  # Skip, will retry next cycle

        if not self._session:
            self._source_health["ip-api.com"] = {
                "status": "error", "last_fetch": None,
                "geo_lookups": 0, "error": "No HTTP session"
            }
            return None

        try:
            async with self._session.get(
                f"http://ip-api.com/json/{ip}",
                timeout=5,
                headers={"User-Agent": "TRINETRA-OSINT/1.0"}
            ) as resp:
                if resp.status != 200:
                    self._source_health["ip-api.com"] = {
                        "status": "error", "last_fetch": None,
                        "geo_lookups": 0, "error": f"HTTP {resp.status}"
                    }
                    return None
                data = await resp.json()
                if data.get("status") == "success":
                    result = {
                        "country": data.get("country", "Unknown"),
                        "countryCode": data.get("countryCode", "ZZ"),
                        "lat": data.get("lat", 0),
                        "lon": data.get("lon", 0),
                        "isp": data.get("isp", ""),
                        "org": data.get("org", ""),
                    }
                    self._ip_cache[ip] = result
                    self._last_geo_check[ip] = now
                    # Update health
                    geo_count = self._source_health["ip-api.com"].get("geo_lookups", 0) + 1
                    self._source_health["ip-api.com"] = {
                        "status": "healthy",
                        "last_fetch": datetime.now(timezone.utc).isoformat(),
                        "geo_lookups": geo_count,
                        "error": None,
                    }
                    # Prune old entries
                    if len(self._last_geo_check) > 200:
                        oldest_ip = min(self._last_geo_check, key=self._last_geo_check.get)
                        del self._last_geo_check[oldest_ip]
                    return result

                # Prune IP cache to prevent unbounded growth
                if len(self._ip_cache) > 1000:
                    # Remove half the entries
                    keys = list(self._ip_cache.keys())
                    for k in keys[:500]:
                        del self._ip_cache[k]
        except Exception as e:
            logger.debug("Geo-location failed for %s: %s", ip, e)
            self._source_health["ip-api.com"] = {
                "status": "error", "last_fetch": None,
                "geo_lookups": 0, "error": str(e)[:100],
            }

        self._ip_cache[ip] = None  # Cache failure
        return None

    def _get_weighted_city(self) -> dict:
        """Select an Indian city weighted by NCRB cyber crime statistics.
        
        Cities with higher cyber crime get more attack vector targets,
        reflecting real-world patterns. Falls back to uniform random if
        NCRB data is unavailable.
        """
        try:
            from app.data.ncrb_crime_data import NCRB_CRIME_DATA_2022
            # Map cities to states and get incident counts
            CITY_STATE_MAP = {
                "New Delhi": "Delhi",
                "Mumbai": "Maharashtra",
                "Bangalore": "Karnataka",
                "Hyderabad": "Telangana",
                "Chennai": "Tamil Nadu",
                "Kolkata": "West Bengal",
                "Pune": "Maharashtra",
                "Ahmedabad": "Gujarat",
                "Jaipur": "Rajasthan",
                "Srinagar": "Jammu & Kashmir",
            }
            state_crime = {d["state"]: d["incidentCount"] for d in NCRB_CRIME_DATA_2022}
            weights = []
            for c in INDIAN_CITIES:
                state = CITY_STATE_MAP.get(c["name"])
                count = state_crime.get(state, 1) if state else 1
                weights.append(max(count, 1))  # Ensure positive weight
            total = sum(weights)
            probabilities = [w / total for w in weights]
            return random.choices(INDIAN_CITIES, weights=probabilities, k=1)[0]
        except Exception:
            return random.choice(INDIAN_CITIES)

    def _ip_to_attack_vector(self, ip: str, geo: Dict) -> Optional[Dict]:
        """Convert a geo-located IP into an attack vector event using real threat data.
        
        Returns a dict with a ``note`` field that discloses which parts are
        real vs. statistically modeled for full transparency.
        """
        country = geo.get("country", "Unknown")
        coords = COUNTRY_COORDS.get(country)
        if not coords:
            coords = (geo.get("lat", 0), geo.get("lon", 0))

        target = self._get_weighted_city()
        self._event_id += 1

        # --- REAL ATTACK TYPE from threat feed metadata ---
        meta = self._ip_metadata.get(ip, {})
        attack_type = meta.get("attack_type", "Probe")
        source = meta.get("source", "Unknown")
        malware = meta.get("malware", "")
        ipsum_score = meta.get("score", 0)
        
        # Track which parts are estimated for the disclosure note
        notes = []
        
        # Detect if attack type was a fallback (randomly guessed, no keywords matched)
        if meta.get("type_estimated", False):
            attack_type = f"Estimated: {attack_type}"
            notes.append("attack type estimated from limited feed metadata")

        # --- REAL SEVERITY from IPsum blacklist score ---
        if ipsum_score >= 5:
            severity = "critical"
        elif ipsum_score >= 2:
            severity = "medium"
        elif ipsum_score > 0:
            severity = "safe"
        else:
            # Fallback: weight by source credibility
            if source == "Feodo":
                severity = "critical"  # Feodo tracks active C2 servers
            elif source == "ThreatFox":
                severity = random.choices(
                    ["critical", "medium", "safe"],
                    weights=[40, 40, 20]
                )[0]
                notes.append("severity estimated from source credibility weighting")
            else:
                severity = random.choices(
                    ["critical", "medium", "safe"],
                    weights=[25, 50, 25]
                )[0]
                notes.append("severity estimated (no blacklist score available)")

        return {
            "type": "attack_vector",
            "id": f"rav-{self._event_id}",
            "from": country,
            "fromLat": coords[0],
            "fromLng": coords[1],
            "to": target["name"],
            "toLat": target["lat"],
            "toLng": target["lng"],
            "attackType": attack_type,
            "severity": severity,
            "sourceIp": ip,
            "isp": geo.get("isp", ""),
            "org": geo.get("org", ""),
            "source": source,
            "malware": malware,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "modeledTarget": True,  # Target city is statistically assigned
            "note": "; ".join(notes) if notes else None,
        }

    def get_source_health(self) -> Dict[str, Dict]:
        """Get health status of all data sources."""
        return dict(self._source_health)

    def get_active_vectors(self, count: int = 20) -> List[Dict]:
        """Get the latest real attack vectors."""
        return self._active_vectors[-count:] if self._active_vectors else []

    async def get_initial_state(self) -> Dict:
        """Get initial state with real data for new WebSocket connections."""
        events = self.get_active_vectors(15)
        # City data is now built by threat_feed.get_initial_state() using NCRB data
        return {
            "type": "initial_state",
            "events": events,
            "cities": [],  # threat_feed.py handles city data from NCRB
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _fetch_loop(self):
        """Background loop that fetches threat data and geo-locates IPs."""
        try:
            await asyncio.sleep(3)

            while self._running:
                # Fetch from all sources in parallel (now returns enriched dicts)
                results = await asyncio.gather(
                    self._fetch_threatfox_csv(),
                    self._fetch_feodo_csv(),
                    self._fetch_ipsum(),
                    return_exceptions=True,
                )

                # Build IP metadata map and collect unique IPs
                self._ip_metadata = {}
                all_ips: List[str] = []
                for r in results:
                    if isinstance(r, list):
                        for entry in r:
                            if isinstance(entry, dict) and "ip" in entry:
                                ip = entry["ip"]
                                # Prefer richer sources over IPsum for metadata
                                if ip not in self._ip_metadata or self._ip_metadata[ip].get("source") == "IPsum":
                                    self._ip_metadata[ip] = {
                                        "source": entry.get("source", "Unknown"),
                                        "attack_type": entry.get("attack_type", "Probe"),
                                        "malware": entry.get("malware", ""),
                                        "score": entry.get("score", 0),
                                        "type_estimated": entry.get("type_estimated", False),
                                    }
                                all_ips.append(ip)

                all_ips = list(set(all_ips))
                logger.info(
                    "Fetched %d unique malicious IPs from threat feeds "
                    "(ThreatFox=%d, Feodo=%d, IPsum=%d)",
                    len(all_ips),
                    sum(1 for v in self._ip_metadata.values() if v["source"] == "ThreatFox"),
                    sum(1 for v in self._ip_metadata.values() if v["source"] == "Feodo"),
                    sum(1 for v in self._ip_metadata.values() if v["source"] == "IPsum"),
                )

                if all_ips:
                    self._malicious_ips = all_ips
                    # Geo-locate a batch (prioritize ThreatFox/Feodo over IPsum)
                    priority_ips = [
                        ip for ip in all_ips
                        if self._ip_metadata.get(ip, {}).get("source") in ("ThreatFox", "Feodo")
                    ][:10]
                    remaining = [
                        ip for ip in all_ips if ip not in priority_ips
                    ][:10]
                    batch = priority_ips + remaining
                    batch = batch[:20]

                    for ip in batch:
                        geo = await self._geo_locate_ip(ip)
                        if geo:
                            vector = self._ip_to_attack_vector(ip, geo)
                            if vector:
                                self._active_vectors.append(vector)
                        await asyncio.sleep(1.5)  # rate limit: ~40/min
                else:
                    logger.warning("No malicious IPs fetched — will retry")

                # Keep last 50 vectors
                if len(self._active_vectors) > 50:
                    self._active_vectors = self._active_vectors[-50:]

                # Fetch new data every 10 minutes
                await asyncio.sleep(600)

        except asyncio.CancelledError:
            pass


# Singleton
real_threat_service = RealThreatService()
