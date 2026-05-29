


# 🇮🇳 TRINETRA — Implementation Planner

> **Version:** 1.1 | **Status:** Planning Complete | **Target:** 8 Weeks
> **Purpose:** Single source of truth for the entire build — what we're building, why, and exactly how.

---

# 📋 TABLE OF CONTENTS

1. [Project Overview](#-project-overview)
2. [Architecture & System Design](#-architecture--system-design)
3. [Complete Directory Structure](#-complete-directory-structure)
4. [Implementation Phases — Week-by-Week](#-implementation-phases--week-by-week)
5. [Core Module Reference](#-core-module-reference)
6. [Plugin System Architecture](#-plugin-system-architecture)
7. [Data Model Reference](#-data-model-reference)
8. [Search Bar — Auto-Detect Logic](#-search-bar--auto-detect-logic)
9. [Scheduled Monitoring System](#-scheduled-monitoring-system)
10. [Webhook Alert System](#-webhook-alert-system)
11. [Settings & Configuration](#-settings--configuration)
12. [Competitive Landscape Summary](#-competitive-landscape-summary)
13. [Implementation Checklist](#-implementation-checklist)

---

## 🎯 PROJECT OVERVIEW

### Elevator Pitch
> **Type anything — domain, IP, email, person — see it on an India map, get ALL public OSINT data instantly. No login. No auth. No walls.**

### What Makes TRINETRA Different

| Differentiator | TRINETRA | Every Other Platform |
|---------------|----------|---------------------|
| **Primary UI** | 🗺️ India map (full-screen) | Tables, lists, text |
| **Search** | 🔍 Auto-detect dropdown | Manual type selection |
| **Auth** | ❌ Zero auth | Required login |
| **Setup time** | ⚡ 3 seconds to get results | 30 minutes to configure |
| **India focus** | 🇮🇳 Gov domains, crime data, cities | Global, generic |
| **Tools scope** | 20 curated, high-impact | 200+ modules (overwhelming) |
| **Data freshness** | ⏱️ Provenance badges on every result | Not shown |

### Core Design Principles

```
┌───────────────────────────────────────────────────┐
│  PRINCIPLE                     WHY IT MATTERS     │
├───────────────────────────────────────────────────┤
│  No auth → No barriers         Instant access     │
│  Map-first → Spatial context  See WHERE threats   │
│  Auto-detect → No learning    Type anything, go   │
│  Curated tools → Focus        20 great > 200 ok   │
│  Provenance → Trust           Know data freshness │
│  Plugin system → Extensible   Easy to add tools   │
│  Client-side keys → Private   API keys never sent │
└───────────────────────────────────────────────────┘
```

---

## 🏗️ ARCHITECTURE & SYSTEM DESIGN

### Container Architecture

```
                          ┌──────────────────┐
                          │   nginx:1.25     │
                          │  (reverse proxy) │
                          └────────┬─────────┘
                                   │
                  ┌────────────────┼────────────────┐
                  │                │                 │
          ┌───────▼───────┐  ┌────▼────────┐  ┌─────▼──────────┐
          │   frontend     │  │  backend    │  │  redis:7       │
          │  (React + TS)  │  │  (FastAPI)  │  │  (cache + Q)   │
          │   Vite build   │  │  Python 3.12│  │                │
          │   Port 5173    │  │  Port 8000  │  └────┬───────────┘
          └───────────────┘  └──────┬───────┘       │
                                    │               │
                           ┌────────▼────────┐  ┌──┴────────────┐
                           │  postgres:15    │  │  celery_worker │
                           │  (main DB)      │  │  (bg tasks)    │
                           │  Volume: pgdata │  └───────┬────────┘
                           └─────────────────┘          │
                                                ┌───────▼────────┐
                                                │  celery_beat    │
                                                │  (scheduler)    │
                                                └────────────────┘
```

### Request Flow

```
Browser                    Backend                    External APIs
  │                         │                         │
  │  POST /api/search       │                         │
  │  {input: "mha.gov.in"}  │                         │
  ├────────────────────────▶│                         │
  │                         │                         │
  │                         │  Auto-detect → DOMAIN   │
  │                         │                         │
  │                         │  Parse tool from sidebar │
  │                         │  → "Domain Record"      │
  │                         │                         │
  │                         │  Dispatch to plugin:    │
  │                         │  whois_service.execute()│
  │                         ├────────────────────────▶│  whois.nic.in
  │                         │                         │
  │                         │◄────────────────────────┤  Raw WHOIS data
  │                         │                         │
  │                         │  Store in PostgreSQL    │
  │                         │  (with last_checked)    │
  │                         │  Cache in Redis (TTL)   │
  │                         │                         │
  │  {tool: "Domain",       │                         │
  │   data: {registrar,     │                         │
  │   nameservers, ...},    │                         │
  │   provenance: {checked, │                         │
  │   source}}              │                         │
  │◄────────────────────────┤                         │
  │                         │                         │
  │  React renders:         │                         │
  │  • Left sidebar shows   │                         │
  │    "Domain Record"      │                         │
  │  • India map zooms to   │                         │
  │    Delhi                │                         │
  │  • Right panel opens    │                         │
  │    with WHOIS data      │                         │
```

### Celery Task Flow (Background)

```
Celery Beat (every hour)
  │
  ├── sync_news()           → RSS feeds → NewsArticle table
  ├── sync_cve()            → NVD + CISA KEV → Vulnerability table
  ├── refresh_whois()       → Refresh stale WHOIS records
  ├── refresh_ports()       → Re-scan stale port data
  └── check_watchlist()     → Scheduled monitoring checks
       │
       └── For each due watch:
            ├── Execute OSINTPlugin.execute(target)
            ├── Compare result vs stored snapshot
            ├── If changes found → Create Alert
            └── If webhook configured → POST alert payload
```

---

## 📁 COMPLETE DIRECTORY STRUCTURE

```
trinetra/
│
├── docker-compose.yml              ← 7 containers orchestrated
├── .env                            ← Environment variables
├── .env.example                    ← Template (committed to git)
├── README.md                       ← ✅ Done — Team overview
├── TRINETRA_OSINT_PLATFORM.md      ← ✅ Done — Full product plan
├── TRINETRA_TECH_COMPARISON.md     ← ✅ Done — Competitive analysis
├── TRINETRA_IMPLEMENTATION_PLANNER.md  ← ⬅️ THIS FILE
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt            ← Python deps (fastapi, uvicorn, sqlalchemy, etc.)
│   ├── pyproject.toml              ← Modern Python project config
│   │
│   └── app/
│       ├── __init__.py
│       ├── main.py                 ← FastAPI app entry point + lifespan
│       ├── config.py               ← pydantic-settings AppConfig
│       ├── celery_app.py           ← Celery app + Beat schedule
│       │
│       ├── models/                 ← SQLAlchemy ORM (20 models)
│       │   ├── __init__.py
│       │   ├── base.py             ← Base model: UUID PK, created_at, updated_at
│       │   │                          + last_checked, first_seen, source,
│       │   │                            refresh_interval, stale_threshold
│       │   ├── domain.py
│       │   ├── ip_address.py
│       │   ├── subdomain.py
│       │   ├── certificate.py
│       │   ├── port.py
│       │   ├── vulnerability.py
│       │   ├── breach.py
│       │   ├── email.py
│       │   ├── username.py
│       │   ├── phone.py
│       │   ├── organization.py
│       │   ├── person.py
│       │   ├── news_article.py
│       │   ├── news_source.py
│       │   ├── crime_stat.py
│       │   ├── threat_vector.py
│       │   ├── shodan_entry.py
│       │   ├── virustotal_entry.py
│       │   ├── search_history.py
│       │   ├── watchlist.py        ← For scheduled monitoring
│       │   └── alert.py            ← For webhook/email alerts
│       │
│       ├── schemas/                ← Pydantic v2 (request/response)
│       │   ├── __init__.py
│       │   ├── search.py           ← SearchRequest + SearchResult
│       │   ├── domain.py
│       │   ├── ip_address.py
│       │   ├── port.py
│       │   ├── certificate.py
│       │   ├── vulnerability.py
│       │   ├── breach.py
│       │   ├── email.py
│       │   ├── username.py
│       │   ├── phone.py
│       │   ├── person.py
│       │   ├── news.py
│       │   ├── crime.py
│       │   ├── threat.py
│       │   ├── report.py
│       │   ├── common.py           ← Pagination, ErrorResponse, StatusResponse
│       │   ├── watchlist.py        ← Watchlist request/response
│       │   └── alert.py            ← Alert schema
│       │
│       ├── routers/                ← FastAPI route handlers (21 files)
│       │   ├── __init__.py
│       │   ├── search.py           ← POST /api/search (unified + auto-detect)
│       │   ├── domain.py           ← GET /api/domain/{domain}
│       │   ├── ip_address.py       ← GET /api/ip/{ip}
│       │   ├── subdomain.py        ← GET /api/subdomain/{domain}
│       │   ├── certificate.py      ← GET /api/cert/{domain}
│       │   ├── port.py             ← GET /api/ports/{ip}
│       │   ├── vulnerability.py    ← GET /api/cves/{target}
│       │   ├── breach.py           ← GET /api/breach/{email}
│       │   ├── email.py            ← GET /api/email/{email}
│       │   ├── username.py         ← GET /api/username/{username}
│       │   ├── phone.py            ← GET /api/phone/{number}
│       │   ├── shodan.py           ← GET /api/shodan/{ip}
│       │   ├── virustotal.py       ← GET /api/vt/{domain}
│       │   ├── document.py         ← GET /api/documents/{query}
│       │   ├── social.py           ← GET /api/social/{target}
│       │   ├── dork.py             ← GET /api/dork/{query}
│       │   ├── surface.py          ← GET /api/surface/{org}
│       │   ├── news.py             ← GET /api/news
│       │   ├── map.py              ← GET /api/map/{state|city}
│       │   ├── report.py           ← POST /api/report
│       │   ├── watchlist.py        ← CRUD /api/watchlist
│       │   ├── alerts.py           ← GET /api/alerts
│       │   └── health.py           ← GET /api/health
│       │
│       ├── services/              ← OSINT business logic (20 plugins + support)
│       │   ├── __init__.py
│       │   ├── base_plugin.py      ← OSINTPlugin abstract base class
│       │   ├── plugin_registry.py  ← Auto-discovers & registers plugins
│       │   ├── search_detector.py  ← Auto-detect input type
│       │   ├── whois_service.py    ← Plugin: Domain Record
│       │   ├── dns_service.py      ← Plugin: Name Servers
│       │   ├── geoip_service.py    ← Plugin: Geo Locator
│       │   ├── port_scanner.py     ← Plugin: Port Scanner
│       │   ├── subdomain_discovery.py ← Plugin: Hidden Pages
│       │   ├── certificate_checker.py ← Plugin: SSL Health
│       │   ├── reverse_dns.py      ← Plugin: Reverse Trace
│       │   ├── http_headers.py     ← Plugin: Tech Fingerprint
│       │   ├── shodan_api.py       ← Plugin: Internet Scanner
│       │   ├── virustotal_api.py   ← Plugin: Threat Shield
│       │   ├── cve_lookup.py       ← Plugin: CVE Alerts
│       │   ├── breach_checker.py   ← Plugin: Data Leaks
│       │   ├── email_osint.py      ← Plugin: Email Finder (Holehe)
│       │   ├── username_search.py  ← Plugin: Username Tracker (Sherlock)
│       │   ├── phone_osint.py      ← Plugin: Phone Intel
│       │   ├── google_dorking.py   ← Plugin: Deep Search
│       │   ├── social_media.py     ← Plugin: Social Radar
│       │   ├── surface_scan.py     ← Plugin: Surface Scan
│       │   ├── news_aggregator.py  ← Plugin: Live Feed
│       │   ├── report_generator.py ← Report export (PDF/JSON/CSV)
│       │   ├── cache_service.py    ← Redis caching layer
│       │   └── rate_limiter.py     ← Token bucket rate limiter
│       │
│       ├── tasks/                 ← Celery background tasks
│       │   ├── __init__.py
│       │   ├── news_sync.py        ← Fetch RSS feeds every 5 min
│       │   ├── cve_sync.py         ← Sync CISA KEV + NVD daily
│       │   ├── whois_refresh.py    ← Refresh stale WHOIS records
│       │   ├── breach_update.py    ← Update breach database
│       │   ├── port_scan.py        ← Background port scanning
│       │   └── watchlist_checker.py ← Scheduled monitoring checks
│       │
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── database.py         ← Async SQLAlchemy engine + session
│       │   ├── redis.py            ← Redis client
│       │   ├── validators.py       ← Input validation helpers
│       │   └── formatters.py       ← Data formatting (JSON→table, etc.)
│       │
│       └── middleware/
│           ├── __init__.py
│           ├── cors.py             ← CORS configuration
│           ├── rate_limit.py       ← IP-based rate limiter
│           └── request_logger.py   ← Request logging
│
├── backend/seed_data/
│   ├── __init__.py
│   ├── seed.py                    ← Main seed runner (async)
│   ├── india_domains.py           ← .gov.in, .ac.in, .org.in domains
│   ├── india_ips.py               ← Government IP ranges
│   ├── crime_stats.py             ← NCRB cyber crime data per state
│   ├── threat_vectors.py          ← Simulated threat origins
│   └── news_sources.py            ← RSS feed URLs
│
├── frontend/
│   ├── Dockerfile                  ← Nginx + Vite build
│   ├── package.json                ← React + TS + Tailwind + Leaflet + Cytoscape
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── index.html
│   │
│   └── src/
│       ├── main.tsx                ← ReactDOM.createRoot
│       ├── App.tsx                 ← Router + layout shell
│       ├── index.css               ← Tailwind directives + global styles
│       │
│       ├── types/                  ← TypeScript interfaces
│       │   ├── index.ts
│       │   ├── search.ts           ← SearchRequest, SearchResult, SearchType enum
│       │   ├── domain.ts           ← DomainRecord
│       │   ├── ip.ts               ← IPAddress, GeoLocation
│       │   ├── map.ts              ← MapPin, ThreatVector, CrimeStat
│       │   ├── tool.ts             ← ToolDefinition (20 tools)
│       │   └── api.ts              ← API response wrappers
│       │
│       ├── services/               ← API client (Axios)
│       │   ├── api.ts              ← Axios instance + interceptors
│       │   ├── search.ts           ← POST /api/search
│       │   ├── domain.ts           ← GET /api/domain/{domain}
│       │   ├── ip.ts               ← GET /api/ip/{ip}
│       │   ├── port.ts             ← GET /api/ports/{ip}
│       │   ├── cve.ts              ← GET /api/cves/{target}
│       │   ├── breach.ts           ← GET /api/breach/{email}
│       │   ├── email.ts            ← GET /api/email/{email}
│       │   ├── username.ts         ← GET /api/username/{username}
│       │   ├── phone.ts            ← GET /api/phone/{number}
│       │   ├── dork.ts             ← GET /api/dork/{query}
│       │   ├── news.ts             ← GET /api/news
│       │   ├── map.ts              ← GET /api/map/{state}
│       │   └── report.ts           ← POST /api/report
│       │
│       ├── pages/
│       │   ├── HomePage.tsx        ← Landing page with search bar
│       │   ├── Dashboard.tsx       ← Main app: sidebar + map + right panel
│       │   └── NotFound.tsx
│       │
│       ├── components/
│       │   ├── layout/
│       │   │   ├── Header.tsx      ← Top bar: search + branding + settings gear
│       │   │   ├── Sidebar.tsx     ← Left panel: 20 tools + My Watches
│       │   │   ├── MainPanel.tsx   ← Central area: map container
│       │   │   ├── RightPanel.tsx  ← Right: tool results with view toggle
│       │   │   ├── BottomFeed.tsx  ← Live news ticker
│       │   │   └── Layout.tsx      ← 3-panel layout orchestrator
│       │   │
│       │   ├── search/
│       │   │   ├── SearchBar.tsx       ← Unified search + icon/status feedback
│       │   │   ├── SearchDropdown.tsx  ← Mode selector: Auto-Detect, Domain, IP, etc.
│       │   │   └── SearchResults.tsx   ← Search results summary
│       │   │
│       │   ├── map/
│       │   │   ├── IndiaMap.tsx        ← Leaflet map with India geolocation
│       │   │   ├── MapLayers.tsx       ← Overlay toggles (assets, threats, crime)
│       │   │   ├── AssetPin.tsx        ← Pin with 🟢🟡🔴 color coding
│       │   │   ├── ThreatVector.tsx    ← Animated line from origin → target
│       │   │   ├── CrimeOverlay.tsx    ← State-wise crime data table
│       │   │   ├── MapTooltip.tsx      ← Hover: news + stats + asset count
│       │   │   └── MapControls.tsx     ← Zoom, fullscreen, recenter
│       │   │
│       │   ├── tools/                  ← 20 tool result renderers
│       │   │   ├── DomainRecord.tsx
│       │   │   ├── NameServers.tsx
│       │   │   ├── GeoLocator.tsx
│       │   │   ├── PortScanner.tsx
│       │   │   ├── HiddenPages.tsx
│       │   │   ├── SSLHealth.tsx
│       │   │   ├── ReverseTrace.tsx
│       │   │   ├── TechFingerprint.tsx
│       │   │   ├── InternetScanner.tsx
│       │   │   ├── ThreatShield.tsx
│       │   │   ├── DataLeaks.tsx
│       │   │   ├── CVEAlerts.tsx
│       │   │   ├── DocumentVault.tsx
│       │   │   ├── EmailFinder.tsx
│       │   │   ├── UsernameTracker.tsx
│       │   │   ├── PhoneIntel.tsx
│       │   │   ├── DeepSearch.tsx
│       │   │   ├── SocialRadar.tsx
│       │   │   ├── SurfaceScan.tsx
│       │   │   └── LiveFeed.tsx
│       │   │
│       │   ├── graph/
│       │   │   ├── GraphView.tsx       ← Cytoscape.js container
│       │   │   ├── GraphNode.tsx       ← Custom node renderer
│       │   │   └── GraphControls.tsx   ← Zoom, layout, export
│       │   │
│       │   ├── monitoring/
│       │   │   ├── WatchButton.tsx     ← "👁️ Watch" button on tool results
│       │   │   ├── WatchModal.tsx      ← Frequency + notification config
│       │   │   └── MyWatches.tsx       ← Sidebar section with 🟢🟡🔴 status
│       │   │
│       │   ├── settings/
│       │   │   ├── SettingsPanel.tsx   ← Slide-out settings drawer
│       │   │   ├── ApiKeysSection.tsx  ← API key input + status
│       │   │   ├── RateLimitStatus.tsx ← Current quota display
│       │   │   ├── ProxyTorToggle.tsx  ← Anonymity toggle
│       │   │   ├── WebhookConfig.tsx   ← Webhook URL + event checkboxes
│       │   │   └── PluginSection.tsx   ← Installed + loadable modules
│       │   │
│       │   ├── news/
│       │   │   ├── NewsFeed.tsx        ← Scrolling ticker bar
│       │   │   ├── NewsCard.tsx        ← Individual headline
│       │   │   └── NewsModal.tsx       ← Full article + source links
│       │   │
│       │   ├── crime/
│       │   │   └── CrimeStatsPanel.tsx ← Crime data table + chart
│       │   │
│       │   └── common/
│       │       ├── LoadingSpinner.tsx
│       │       ├── ErrorState.tsx      ← Error + retry button
│       │       ├── EmptyState.tsx      ← "No data" placeholder
│       │       ├── StatusBadge.tsx     ← 🟢🟡🔴 with text
│       │       ├── FreshnessBadge.tsx  ← ⏱️ timestamp display
│       │       ├── ToolResultWrapper.tsx  ← GUI/Terminal/Split/Graph toggle
│       │       ├── DataTable.tsx       ← Reusable table + export
│       │       └── TerminalOutput.tsx  ← xterm.js terminal view
│       │
│       ├── hooks/
│       │   ├── useAutoDetect.ts    ← Input → SearchType detection
│       │   ├── useMap.ts           ← Map interactions + state
│       │   ├── useToolResults.ts   ← Tool data fetching + caching
│       │   ├── useNews.ts          ← Live news polling (30s)
│       │   └── useSettings.ts      ← localStorage settings
│       │
│       ├── store/                  ← Zustand state management
│       │   ├── index.ts
│       │   ├── searchStore.ts      ← Current search query + type
│       │   ├── mapStore.ts         ← Layers, pins, vectors, zoom
│       │   ├── toolStore.ts        ← Active tool + results
│       │   ├── newsStore.ts        ← News feed items
│       │   └── settingsStore.ts    ← API keys, proxies, webhooks
│       │
│       └── assets/
│           ├── icons/              ← Tool icons (SVG or emoji)
│           ├── map/                ← India state GeoJSON
│           └── logo.svg
│
├── nginx/
│   ├── nginx.conf                 ← Reverse proxy config
│   └── ssl/                       ← Dev SSL certs
│
└── scripts/
    ├── setup.sh                   ← First-time setup
    ├── seed.sh                    ← Database seeding
    └── cleanup.sh                 ← docker-compose down -v + prune
```

---

## 📅 IMPLEMENTATION PHASES — WEEK-BY-WEEK

---

### 🏗️ Phase 1: Foundation (Week 1)

**Goal:** Clean slate, project scaffold, search bar, search results.

| Day | Tasks | Files Created | Acceptance Criteria |
|-----|-------|--------------|-------------------|
| **Mon** | Kill old containers, delete old code, create new FastAPI scaffold | `backend/Dockerfile`, `requirements.txt`, `app/main.py`, `app/config.py` | `docker-compose up` starts FastAPI on :8000, returns health check |
| **Tue** | Create React scaffold with Vite + Tailwind | `frontend/package.json`, `tsconfig.json`, `vite.config.ts`, `tailwind.config.js`, `App.tsx`, `index.css` | `npm run dev` shows blank page |
| **Wed** | Docker Compose with all containers | `docker-compose.yml` (postgres, redis, backend, frontend, nginx, celery), `.env`, `.env.example` | All 6 containers start, backend connects to postgres |
| **Thu** | PostgreSQL schema with **provenance fields** | All 22 models in `models/` with `base.py` (UUID PK, timestamps, `last_checked`, `first_seen`, `source`, `refresh_interval`) | Alembic migration creates all tables |
| **Fri** | **Search bar** with dropdown + auto-detect | `frontend: SearchBar.tsx, SearchDropdown.tsx, useAutoDetect.ts` + `backend: search_detector.py, routers/search.py, schemas/search.py` | Type "mha.gov.in" → detects Domain, hits enter → shows landing page |

#### Auto-Detect Implementation

**File:** `backend/app/services/search_detector.py`

```python
from enum import Enum

class SearchType(str, Enum):
    DOMAIN = "domain"
    IP = "ip"
    EMAIL = "email"
    CVE = "cve"
    PHONE = "phone"
    PERSON = "person"
    USERNAME = "username"
    URL = "url"
    ORGANIZATION = "organization"
    UNKNOWN = "unknown"

import re

def detect_search_type(input_str: str) -> tuple[SearchType, str]:
    """Auto-detect what the user typed. Returns (type, cleaned_input)."""
    input_str = input_str.strip()

    # 1. Email: contains @
    if "@" in input_str:
        return SearchType.EMAIL, input_str.lower()

    # 2. CVE ID: CVE-YYYY-NNNNN
    if re.match(r"^CVE-\d{4}-\d{4,}$", input_str, re.IGNORECASE):
        return SearchType.CVE, input_str.upper()

    # 3. URL: starts with http:// or https://
    if input_str.startswith(("http://", "https://")):
        return SearchType.URL, input_str

    # 4. Phone: starts with + or matches Indian phone pattern
    if input_str.startswith("+") or re.match(r"^\+?\d{10,15}$", input_str):
        return SearchType.PHONE, input_str

    # 5. IPv4: 4 octets separated by dots
    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", input_str):
        return SearchType.IP, input_str

    # 6. Domain: contains a dot (e.g., example.com, mha.gov.in)
    if "." in input_str and not input_str.endswith("."):
        return SearchType.DOMAIN, input_str.lower()

    # 7. Username: single word (no spaces), may contain underscore
    if " " not in input_str and re.match(r"^[a-zA-Z0-9_]+$", input_str):
        return SearchType.USERNAME, input_str

    # 8. Person: two words (First Last)
    if " " in input_str and len(input_str.split()) == 2:
        return SearchType.PERSON, input_str.title()

    # 9. Organization: everything else (multiple words)
    if len(input_str.split()) >= 2:
        return SearchType.ORGANIZATION, input_str

    return SearchType.UNKNOWN, input_str
```

#### Search Bar Frontend Logic

**File:** `frontend/src/hooks/useAutoDetect.ts`

```typescript
type SearchType = 'domain' | 'ip' | 'email' | 'cve' | 'phone'
                | 'person' | 'username' | 'url' | 'organization' | 'unknown';

function detectSearchType(input: string): { type: SearchType; label: string } {
  const trimmed = input.trim();

  // Email
  if (trimmed.includes('@'))
    return { type: 'email', label: '📧 Email Detected' };

  // CVE ID
  if (/^CVE-\d{4}-\d{4,}$/i.test(trimmed))
    return { type: 'cve', label: '🆔 CVE Detected' };

  // Phone starts with +
  if (/^\+/.test(trimmed))
    return { type: 'phone', label: '📱 Phone Detected' };

  // IPv4 pattern
  if (/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(trimmed))
    return { type: 'ip', label: '📍 IP Detected' };

  // Domain (contains a dot)
  if (/\./.test(trimmed) && !trimmed.endsWith('.'))
    return { type: 'domain', label: '🌐 Domain Detected' };

  // Single word, no spaces = username
  if (!/\s/.test(trimmed) && /^[a-zA-Z0-9_]+$/.test(trimmed))
    return { type: 'username', label: '🔤 Username Detected' };

  // Two words = person name
  if (trimmed.split(/\s+/).length === 2)
    return { type: 'person', label: '👤 Person Detected' };

  // Default
  return { type: 'unknown', label: '🔍 Auto-Detect' };
}
```

---

### 🗺️ Phase 2: Map + Dashboard (Week 2)

**Goal:** India map with pins, hover tooltips, default dashboard.

| Day | Tasks | Files | Acceptance Criteria |
|-----|-------|-------|-------------------|
| **Mon** | Install Leaflet + OpenStreetMap, create India map component | `IndiaMap.tsx`, `MapControls.tsx`, install leaflet, react-leaflet | India map renders with states |
| **Tue** | State/city pin system with 🟢🟡🔴 color coding | `AssetPin.tsx`, `map types`, geo seed data | Pins appear on major Indian cities |
| **Wed** | Hover tooltips with news + crime stats | `MapTooltip.tsx`, linked to news store | Hover Delhi → shows asset count + headlines |
| **Thu** | Default dashboard view (no search required) | `Dashboard.tsx`, `Layout.tsx`, `Header.tsx` | Open site → see India map with national stats |
| **Fri** | Toggle overlay system | `MapLayers.tsx` with checkboxes | Toggle crime data overlay on/off |

#### Map Configuration

```typescript
// IndiaMap.tsx — key config
const INDIA_CENTER: [number, number] = [20.5937, 78.9629];  // Center of India
const DEFAULT_ZOOM = 5;
const MAX_BOUNDS: [[number, number], [number, number]] = [
  [6.75, 68.15],   // SW corner (Kanyakumari, Gujarat)
  [35.67, 97.40],  // NE corner (Arunachal Pradesh)
];
```

#### Pin Color Logic

```typescript
function getPinColor(riskScore: number): 'green' | 'yellow' | 'red' {
  if (riskScore < 25) return 'green';
  if (riskScore < 60) return 'yellow';
  return 'red';
}
// green = circle marker with #22c55e fill
// yellow = circle marker with #eab308 fill
// red = circle marker with #ef4444 fill
```

---

### 🛠️ Phase 3: Core OSINT Tools + Plugin System (Weeks 3-4)

**Goal:** 8 infrastructure tools + drag-and-drop plugin architecture.

| Week | Day | Tasks | Files |
|------|-----|-------|-------|
| **3** | **Mon** | **Plugin architecture**: BasePlugin ABC, plugin_registry, PluginResult schema | `base_plugin.py`, `plugin_registry.py` |
| | **Tue** | Domain Record (WHOIS) + Name Servers (DNS) | `whois_service.py`, `dns_service.py`, routers + schemas + frontend components |
| | **Wed** | Geo Locator + Port Scanner | `geoip_service.py`, `port_scanner.py`, + frontend |
| | **Thu** | Hidden Pages + SSL Health | `subdomain_discovery.py`, `certificate_checker.py`, + frontend |
| | **Fri** | Reverse Trace + Tech Fingerprint | `reverse_dns.py`, `http_headers.py`, + frontend |
| **4** | **Mon** | ToolResultWrapper with GUI/Terminal/Split toggle | `ToolResultWrapper.tsx`, xterm.js integration |
| | **Tue** | All frontend tool components wired up | All 8 tool .tsx files with data binding |
| | **Wed** | **Data provenance badges** on all tool results | `FreshnessBadge.tsx`, backend returns `last_checked` |
| | **Thu** | Redis caching layer + Celery setup | `cache_service.py`, `celery_app.py` |
| | **Fri** | Integration testing: all 8 tools working end-to-end | — |

#### Plugin Architecture Implementation

**File:** `backend/app/services/base_plugin.py`

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from enum import Enum

class SearchType(str, Enum):
    DOMAIN = "domain"
    IP = "ip"
    EMAIL = "email"
    CVE = "cve"
    PHONE = "phone"
    PERSON = "person"
    USERNAME = "username"
    URL = "url"
    ORGANIZATION = "organization"

@dataclass
class PluginResult:
    data: dict[str, Any]
    error: Optional[str] = None
    last_checked: datetime = field(default_factory=datetime.utcnow)
    source: str = ""
    refresh_interval_hours: int = 24
    cached: bool = False

class OSINTPlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name (e.g., 'Domain Record')"""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Short description (e.g., 'WHOIS lookup for domain registration')"""
        ...

    @property
    @abstractmethod
    def input_types(self) -> list[SearchType]:
        """Which search types this plugin handles (e.g., [SearchType.DOMAIN])"""
        ...

    @property
    def requires_api_key(self) -> bool:
        """Whether this plugin needs a 3rd-party API key"""
        return False

    @property
    def api_key_name(self) -> Optional[str]:
        """Name of the API key field (e.g., 'shodan', 'virustotal')"""
        return None

    @property
    def cache_ttl_seconds(self) -> int:
        """How long to cache results in Redis"""
        return 3600  # 1 hour default

    @abstractmethod
    async def execute(self, input_str: str, api_keys: dict[str, str] | None = None) -> PluginResult:
        """Execute the OSINT lookup. Returns structured result or error."""
        ...
```

**File:** `backend/app/services/plugin_registry.py`

```python
import importlib
import pkgutil
import inspect
from typing import Optional

from .base_plugin import OSINTPlugin, SearchType

_plugins: dict[str, type[OSINTPlugin]] = {}
_instances: dict[str, OSINTPlugin] = {}

def discover_plugins():
    """Auto-discover all plugins in the services package."""
    import backend.app.services as services_package
    for _, module_name, _ in pkgutil.iter_modules(services_package.__path__):
        if module_name == "base_plugin" or module_name.startswith("_"):
            continue
        module = importlib.import_module(f"backend.app.services.{module_name}")
        for name, cls in inspect.getmembers(module, inspect.isclass):
            if (issubclass(cls, OSINTPlugin) and cls is not OSINTPlugin
                and not inspect.isabstract(cls)):
                _plugins[cls.__name__] = cls

def get_plugin(name: str) -> Optional[OSINTPlugin]:
    """Get or create a plugin instance by class name."""
    if name in _instances:
        return _instances[name]
    cls = _plugins.get(name)
    if cls is not None:
        inst = cls()
        _instances[name] = inst
        return inst
    return None

def get_plugins_for_input(search_type: SearchType) -> list[OSINTPlugin]:
    """Get all plugins that handle the given input type."""
    result = []
    for name, cls in _plugins.items():
        inst = get_plugin(name)
        if inst and search_type in inst.input_types:
            result.append(inst)
    return result

def get_all_plugins() -> list[OSINTPlugin]:
    """Get all registered plugins."""
    return [get_plugin(name) for name in _plugins if get_plugin(name)]
```

#### Example Plugin: WHOIS Service

```python
# backend/app/services/whois_service.py
import whois
from .base_plugin import OSINTPlugin, PluginResult, SearchType

class WhoisPlugin(OSINTPlugin):
    @property
    def name(self) -> str:
        return "Domain Record"

    @property
    def description(self) -> str:
        return "WHOIS lookup for domain registration details"

    @property
    def input_types(self) -> list[SearchType]:
        return [SearchType.DOMAIN]

    @property
    def cache_ttl_seconds(self) -> int:
        return 86400  # WHOIS rarely changes, cache for 24h

    async def execute(self, input_str: str, api_keys: dict | None = None) -> PluginResult:
        try:
            w = whois.whois(input_str)
            return PluginResult(
                data={
                    "domain": input_str,
                    "registrar": w.registrar,
                    "creation_date": str(w.creation_date),
                    "expiration_date": str(w.expiration_date),
                    "name_servers": list(w.name_servers or []),
                    "org": w.org,
                    "country": w.country,
                    "status": list(w.status or []),
                },
                source="WHOIS (whois.nic.in)",
                refresh_interval_hours=168,  # Check weekly
            )
        except Exception as e:
            return PluginResult(
                data={},
                error=f"WHOIS lookup failed: {str(e)}",
            )
```

#### Plugin Registration (in main.py)

```python
# backend/app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .services.plugin_registry import discover_plugins

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: discover all OSINT plugins
    discover_plugins()
    yield
    # Shutdown
```

---

### 🔥 Phase 4: Threat OSINT + Settings (Week 5)

**Goal:** 5 threat tools + settings panel + rate limiting.

| Day | Tasks | Files |
|-----|-------|-------|
| **Mon** | CVE Alerts (NVD + CISA KEV sync) | `cve_lookup.py`, `cve_sync.py` (Celery), `CVEAlerts.tsx` |
| **Tue** | Data Leaks (breach checker) | `breach_checker.py`, `DataLeaks.tsx` |
| **Wed** | Document Vault (Google dorking) + Internet Scanner (Shodan) | `google_dorking.py`, `shodan_api.py`, + frontend |
| **Thu** | Threat Shield (VirusTotal) | `virustotal_api.py`, `ThreatShield.tsx` |
| **Fri** | **Settings panel**: API keys + Rate limiting + Proxy/Tor | `SettingsPanel.tsx`, `ApiKeysSection.tsx`, `RateLimitStatus.tsx`, `ProxyTorToggle.tsx`, `rate_limiter.py` |

#### Rate Limiter Implementation

```python
# backend/app/services/rate_limiter.py
import time
from collections import defaultdict
from threading import Lock

class TokenBucket:
    def __init__(self, rate: int, burst: int):
        self.rate = rate          # tokens per second
        self.burst = burst        # max tokens
        self.tokens = burst
        self.last_refill = time.monotonic()
        self.lock = Lock()

    def consume(self, tokens: int = 1) -> bool:
        with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
            self.last_refill = now
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

class RateLimiter:
    """IP-based rate limiter."""
    def __init__(self):
        self.buckets: dict[str, TokenBucket] = {}
        self.global_bucket = TokenBucket(rate=100/60, burst=100)  # 100/min global

    def check(self, ip: str) -> tuple[bool, int, int]:
        """Returns (allowed, remaining, reset_seconds)."""
        if not self.global_bucket.consume():
            return False, 0, 60

        if ip not in self.buckets:
            self.buckets[ip] = TokenBucket(rate=10, burst=10)  # 10 req/s per IP

        if self.buckets[ip].consume():
            return True, int(self.buckets[ip].tokens), 1
        return False, 0, 1
```

---

### 👤 Phase 5: Person OSINT (Week 6)

**Goal:** 5 person OSINT tools — all public, no auth.

| Day | Tasks | Files |
|-----|-------|-------|
| **Mon** | Email Finder (Holehe wrapper) | `email_osint.py` (subprocess holehe), `EmailFinder.tsx` |
| **Tue** | Username Tracker (Sherlock wrapper) | `username_search.py` (subprocess sherlock), `UsernameTracker.tsx` |
| **Wed** | Phone Intel (libphonenumber) | `phone_osint.py`, `PhoneIntel.tsx` |
| **Thu** | Deep Search + Social Radar | `social_media.py`, `DeepSearch.tsx`, `SocialRadar.tsx` |
| **Fri** | Integration testing: all 20 tools work | — |

---

### 🧠 Phase 6: Map + Graph Intelligence (Week 7)

**Goal:** Graph view, live vectors, crime overlay, drill-down.

| Day | Tasks | Files |
|-----|-------|-------|
| **Mon** | **Graph View** — Cytoscape.js entity relationship graph | `GraphView.tsx`, `GraphNode.tsx`, `GraphControls.tsx`, install cytoscape |
| **Tue** | Graph data mapper — converts OSINT results → entity graph | Plugin integration: Domain → IP → Port → CVE edges |
| **Wed** | Live threat vectors (animated lines) | `ThreatVector.tsx`, leaflet polyline with animation |
| **Thu** | Crime data overlay + Click drill-down (state → city → asset) | `CrimeOverlay.tsx`, `crime_stats.py`, `seed_data/crime_stats.py` |
| **Fri** | Surface Scan (aggregator) + News feed on map | `surface_scan.py`, `SurfaceScan.tsx`, news↔map linking |

#### Graph View (Cytoscape.js) — Core Logic

```typescript
// GraphView.tsx — conceptual structure
import CytoscapeComponent from 'react-cytoscapejs';

const elements = [
  // Center node — the search target
  { data: { id: 'mha.gov.in', label: 'mha.gov.in', type: 'domain', risk: 65 } },
  // Connected IP
  { data: { id: '164.100.24.1', label: '164.100.24.1', type: 'ip', risk: 50 } },
  // Edge linking them
  { data: { source: 'mha.gov.in', target: '164.100.24.1', label: 'A record' } },
  // Ports
  { data: { id: 'port-22', label: 'Port 22 (SSH)', type: 'port', risk: 80 } },
  { data: { source: '164.100.24.1', target: 'port-22' } },
  // CVEs
  { data: { id: 'CVE-2024-6387', label: 'CVE-2024-6387\n9.8 CRITICAL', type: 'cve', risk: 100 } },
  { data: { source: 'port-22', target: 'CVE-2024-6387' } },
];

const stylesheet = [
  { selector: 'node[type="domain"]', style: { 'background-color': '#3b82f6', width: 80, height: 80 } },
  { selector: 'node[type="ip"]',     style: { 'background-color': '#8b5cf6', width: 60, height: 60 } },
  { selector: 'node[type="port"]',   style: { 'background-color': '#f59e0b', width: 50, height: 50 } },
  { selector: 'node[type="cve"]',    style: { 'background-color': '#ef4444', width: 70, height: 70 } },
  { selector: 'node[risk >= 80]',    style: { 'border-color': '#ef4444', 'border-width': 3 } },
  { selector: 'edge',                style: { 'line-color': '#64748b', width: 2 } },
];
```

---

### 📡 Phase 7: Monitoring + Polish (Week 8)

**Goal:** Scheduled monitoring, webhooks, export, responsive, seed data.

| Day | Tasks | Files |
|-----|-------|-------|
| **Mon** | **Scheduled Monitoring**: Watchlist model + Celery beat checker | `watchlist.py` (model), `watchlist_checker.py` (task), `WatchButton.tsx`, `WatchModal.tsx`, `MyWatches.tsx` |
| **Tue** | **Webhook Alerts**: Webhook config UI + alert dispatcher | `WebhookConfig.tsx`, alert dispatch logic, Alert model |
| **Wed** | Report export (PDF, JSON, CSV) + Ephemeral share links | `report_generator.py`, report router, share link logic |
| **Thu** | Seed data: .gov.in domains, IP ranges, crime stats, threat vectors, news sources | All `seed_data/*.py` files |
| **Fri** | Performance optimization + Mobile responsiveness + Dark mode | Map performance, responsive breakpoints, CSS variables |

---

## 🔌 CORE MODULE REFERENCE

### Unified Search Endpoint — The Central Router

**File:** `backend/app/routers/search.py`

```python
from fastapi import APIRouter, Request
from ..services.search_detector import detect_search_type, SearchType
from ..services.plugin_registry import get_plugins_for_input
from ..schemas.search import SearchRequest, SearchResponse

router = APIRouter(prefix="/api/search", tags=["search"])

@router.post("/")
async def unified_search(req: SearchRequest, request: Request):
    """The ONE endpoint for ALL OSINT searches. Auto-detects and dispatches."""

    # 1. Auto-detect the input type
    search_type, cleaned_input = detect_search_type(req.input)

    # 2. Override with manual type if user specified one
    if req.manual_type:
        search_type = SearchType(req.manual_type)

    # 3. Find matching plugins
    plugins = get_plugins_for_input(search_type)

    # 4. Execute all matching plugins in parallel
    results = {}
    for plugin in plugins:
        api_key = None
        if plugin.requires_api_key and plugin.api_key_name:
            api_key = req.api_keys.get(plugin.api_key_name)
        result = await plugin.execute(cleaned_input, {"api_key": api_key})
        results[plugin.name] = result

    # 5. Return unified response
    return SearchResponse(
        input=cleaned_input,
        detected_type=search_type,
        results=results,
        geo_data=await get_geo_context(cleaned_input, search_type),
    )
```

### Tool Registration Model (Frontend)

**File:** `frontend/src/types/tool.ts`

```typescript
export interface ToolDefinition {
  id: string;
  name: string;
  emoji: string;
  description: string;
  category: 'infrastructure' | 'threat' | 'person' | 'advanced';
  inputTypes: SearchType[];
  requiresApiKey?: string;
  component: React.ComponentType<any>;
}

export const TOOLS: ToolDefinition[] = [
  // Infrastructure (10)
  { id: 'domain-record',      name: 'Domain Record',      emoji: '🌐', category: 'infrastructure', inputTypes: ['domain'], component: DomainRecord },
  { id: 'name-servers',       name: 'Name Servers',       emoji: '🔗', category: 'infrastructure', inputTypes: ['domain'], component: NameServers },
  { id: 'geo-locator',        name: 'Geo Locator',        emoji: '📍', category: 'infrastructure', inputTypes: ['ip'], component: GeoLocator },
  { id: 'port-scanner',       name: 'Port Scanner',       emoji: '🔌', category: 'infrastructure', inputTypes: ['ip', 'domain'], component: PortScanner },
  { id: 'hidden-pages',       name: 'Hidden Pages',       emoji: '📁', category: 'infrastructure', inputTypes: ['domain'], component: HiddenPages },
  { id: 'ssl-health',         name: 'SSL Health',         emoji: '🔒', category: 'infrastructure', inputTypes: ['domain'], component: SSLHealth },
  { id: 'reverse-trace',      name: 'Reverse Trace',      emoji: '🌍', category: 'infrastructure', inputTypes: ['ip'], component: ReverseTrace },
  { id: 'tech-fingerprint',   name: 'Tech Fingerprint',   emoji: '🔌', category: 'infrastructure', inputTypes: ['domain', 'url'], component: TechFingerprint },
  { id: 'internet-scanner',   name: 'Internet Scanner',   emoji: '🌏', category: 'infrastructure', inputTypes: ['ip'], requiresApiKey: 'shodan', component: InternetScanner },
  { id: 'threat-shield',      name: 'Threat Shield',      emoji: '🛡️', category: 'infrastructure', inputTypes: ['domain', 'ip'], requiresApiKey: 'virustotal', component: ThreatShield },

  // Threat (3)
  { id: 'data-leaks',         name: 'Data Leaks',         emoji: '🚨', category: 'threat', inputTypes: ['email', 'domain'], component: DataLeaks },
  { id: 'cve-alerts',         name: 'CVE Alerts',         emoji: '🕸️', category: 'threat', inputTypes: ['domain', 'ip'], component: CVEAlerts },
  { id: 'document-vault',     name: 'Document Vault',     emoji: '📄', category: 'threat', inputTypes: ['domain', 'organization', 'person'], component: DocumentVault },

  // Person (3)
  { id: 'email-finder',       name: 'Email Finder',       emoji: '👤', category: 'person', inputTypes: ['email'], component: EmailFinder },
  { id: 'username-tracker',   name: 'Username Tracker',   emoji: '🔤', category: 'person', inputTypes: ['username'], component: UsernameTracker },
  { id: 'phone-intel',        name: 'Phone Intel',        emoji: '📱', category: 'person', inputTypes: ['phone'], component: PhoneIntel },

  // Advanced (4)
  { id: 'deep-search',        name: 'Deep Search',        emoji: '🔍', category: 'advanced', inputTypes: ['domain', 'organization'], component: DeepSearch },
  { id: 'social-radar',       name: 'Social Radar',       emoji: '🕸️', category: 'advanced', inputTypes: ['person', 'organization'], component: SocialRadar },
  { id: 'surface-scan',       name: 'Surface Scan',       emoji: '📊', category: 'advanced', inputTypes: ['domain', 'organization'], component: SurfaceScan },
  { id: 'live-feed',          name: 'Live Feed',          emoji: '📡', category: 'advanced', inputTypes: ['unknown'], component: LiveFeed },
];
```

---

## 🗄️ DATA MODEL REFERENCE

### Base Model — Every Entity Inherits This

```python
# backend/app/models/base.py
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, String, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class BaseModel(Base):
    __abstract__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Data Provenance Fields (every entity has these)
    last_checked = Column(DateTime, nullable=True)       # When last collected
    first_seen = Column(DateTime, default=datetime.utcnow) # First discovery
    source = Column(String(100), nullable=True)            # Data source name
    refresh_interval = Column(Integer, default=86400)      # Seconds between refreshes (24h default)
    stale_threshold = Column(Integer, default=604800)       # Seconds before considered stale (7d)
```

### Domain Record Model

```python
# backend/app/models/domain.py
class DomainRecord(BaseModel):
    __tablename__ = "domain_records"

    domain = Column(String(255), unique=True, index=True, nullable=False)
    registrar = Column(String(255))
    creation_date = Column(DateTime)
    expiration_date = Column(DateTime)
    name_servers = Column(JSON)          # ["ns1.nic.in", "ns2.nic.in"]
    org = Column(String(255))
    country = Column(String(100))
    status = Column(JSON)                # ["clientTransferProhibited", ...]
```

### IP Address Model

```python
# backend/app/models/ip_address.py
class IPAddress(BaseModel):
    __tablename__ = "ip_addresses"

    ip = Column(String(45), unique=True, index=True, nullable=False)
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    isp = Column(String(255))
    asn = Column(String(50))
    latitude = Column(Float)
    longitude = Column(Float)
    timezone = Column(String(50))
```

### Watchlist Model (for Scheduled Monitoring)

```python
# backend/app/models/watchlist.py
class Watchlist(BaseModel):
    __tablename__ = "watchlists"

    ip_address = Column(String(45), index=True, nullable=False)
    target = Column(String(255), nullable=False)           # Domain, IP, email, etc.
    target_type = Column(String(50), nullable=False)       # DOMAIN, IP, EMAIL, etc.
    frequency_hours = Column(Integer, default=24)          # 6, 12, 24, 168
    notify_on = Column(JSON, default=list)                 # ['new_ports', 'new_cves', ...]
    alert_email = Column(String(255), nullable=True)       # Optional email
    last_checked = Column(DateTime, nullable=True)
    last_result = Column(JSON, nullable=True)              # Snapshot for diff
    next_check = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        Index('idx_watchlist_ip_target', 'ip_address', 'target', unique=True),
    )
```

### Alert Model (for Webhook/Email)

```python
# backend/app/models/alert.py
class Alert(BaseModel):
    __tablename__ = "alerts"

    watchlist_id = Column(UUID(as_uuid=True), ForeignKey('watchlists.id'))
    alert_type = Column(String(50), nullable=False)        # 'new_port', 'new_cve', 'cert_expiry'
    summary = Column(String(500), nullable=False)          # Human-readable
    details = Column(JSON)                                 # Before/after comparison
    severity = Column(String(20), default='info')          # 'info', 'warning', 'critical'
    webhook_sent = Column(Boolean, default=False)
    email_sent = Column(Boolean, default=False)
    acknowledged = Column(Boolean, default=False)
```

*(20+ more models follow the same pattern — one per data type.)*

---

## 🐳 DOCKER COMPOSE CONFIGURATION

### docker-compose.yml

```yaml
# docker-compose.yml
version: "3.9"

services:
  postgres:
    image: postgres:15-alpine
    container_name: trinetra-postgres
    environment:
      POSTGRES_DB: trinetra
      POSTGRES_USER: trinetra
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-trinetra_dev}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U trinetra"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: trinetra-redis
    ports:
      - "6379:6379"
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  backend:
    build: ./backend
    container_name: trinetra-backend
    environment:
      DATABASE_URL: postgresql+asyncpg://trinetra:${POSTGRES_PASSWORD:-trinetra_dev}@postgres:5432/trinetra
      REDIS_URL: redis://redis:6379/0
      CORS_ORIGINS: http://localhost:5173,http://localhost
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  celery_worker:
    build: ./backend
    container_name: trinetra-celery
    environment:
      DATABASE_URL: postgresql+asyncpg://trinetra:${POSTGRES_PASSWORD:-trinetra_dev}@postgres:5432/trinetra
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - redis
      - backend
    volumes:
      - ./backend:/app
    command: celery -A app.celery_app worker --loglevel=info

  celery_beat:
    build: ./backend
    container_name: trinetra-celery-beat
    environment:
      DATABASE_URL: postgresql+asyncpg://trinetra:${POSTGRES_PASSWORD:-trinetra_dev}@postgres:5432/trinetra
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - redis
      - backend
    volumes:
      - ./backend:/app
    command: celery -A app.celery_app beat --loglevel=info

  frontend:
    build: ./frontend
    container_name: trinetra-frontend
    ports:
      - "5173:5173"
    depends_on:
      - backend
    volumes:
      - ./frontend/src:/app/src
    command: npm run dev -- --host 0.0.0.0

  nginx:
    image: nginx:1.25-alpine
    container_name: trinetra-nginx
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf
    depends_on:
      - frontend
      - backend

volumes:
  pgdata:
  redisdata:
```

### .env.example

```bash
# Database
POSTGRES_PASSWORD=trinetra_dev

# Redis
REDIS_URL=redis://redis:6379/0

# Backend
DATABASE_URL=postgresql+asyncpg://trinetra:${POSTGRES_PASSWORD}@postgres:5432/trinetra
CORS_ORIGINS=http://localhost:5173,http://localhost

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

---

## ⏰ CELERY BEAT SCHEDULE

```python
# backend/app/celery_app.py
from celery import Celery

celery_app = Celery(
    "trinetra",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
)

celery_app.conf.beat_schedule = {
    # News: fetch RSS feeds every 5 minutes
    "sync-news-every-5-minutes": {
        "task": "app.tasks.news_sync.sync_news",
        "schedule": 300.0,
    },
    # CVE: sync NVD + CISA KEV every 24 hours
    "sync-cve-every-24-hours": {
        "task": "app.tasks.cve_sync.sync_cve",
        "schedule": 86400.0,
    },
    # WHOIS: refresh stale records every hour
    "refresh-whois-every-hour": {
        "task": "app.tasks.whois_refresh.refresh_whois",
        "schedule": 3600.0,
    },
    # Watchlist: check due watches every 60 seconds
    "check-watchlist-every-60-seconds": {
        "task": "app.tasks.watchlist_checker.check_watchlist",
        "schedule": 60.0,
    },
    # Breach DB: update weekly
    "update-breach-db-weekly": {
        "task": "app.tasks.breach_update.update_breaches",
        "schedule": 604800.0,  # 7 days
    },
}

celery_app.conf.timezone = "Asia/Kolkata"
```

---

## 🗄️ DATABASE MIGRATIONS (Alembic)

```bash
# Initial setup (run once)
pip install alembic
alembic init alembic

# Edit alembic.ini:
# sqlalchemy.url = postgresql+asyncpg://trinetra:trinetra_dev@localhost:5432/trinetra

# Edit alembic/env.py to use async engine:
from app.models.base import Base  # Import all models
from app.config import settings
target_metadata = Base.metadata

# Create first migration
alembic revision --autogenerate -m "initial_schema"

# Apply migration
alembic upgrade head

# Each time models change:
alembic revision --autogenerate -m "description_of_change"
alembic upgrade head
```

---

## 🧭 FRONTEND ROUTING

```typescript
// frontend/src/App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { HomePage } from './pages/HomePage';
import { Dashboard } from './pages/Dashboard';
import { NotFound } from './pages/NotFound';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
```

After search, the `HomePage` navigates to `/dashboard?q=mha.gov.in&type=domain`.
The `Dashboard` reads query params, calls `/api/search`, and populates the 3-panel view.

---

## 📡 LIVE NEWS POLLING PATTERN

```typescript
// frontend/src/hooks/useNews.ts
import { useEffect } from 'react';
import { useNewsStore } from '../store/newsStore';
import { newsService } from '../services/news';

const POLL_INTERVAL_MS = 30_000;  // 30 seconds

export function useNews() {
  const { items, setItems, addItem } = useNewsStore();

  useEffect(() => {
    let mounted = true;

    const fetchNews = async () => {
      try {
        const result = await newsService.getLatest();
        if (mounted && result.items) {
          setItems(result.items);
        }
      } catch {
        // Silently fail — news is non-critical
      }
    };

    // Fetch immediately, then poll
    fetchNews();
    const interval = setInterval(fetchNews, POLL_INTERVAL_MS);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  return { items };
}
```

### News Feed Component

```typescript
// frontend/src/components/news/NewsFeed.tsx
import { useNews } from '../../hooks/useNews';
import { NewsCard } from './NewsCard';

const SEVERITY_COLORS = {
  critical: 'bg-red-500',
  warning: 'bg-yellow-500',
  info: 'bg-green-500',
};

export function NewsFeed() {
  const { items } = useNews();

  return (
    <div className="fixed bottom-0 left-0 right-0 h-16 bg-slate-900 border-t border-slate-700 overflow-hidden">
      <div className="flex items-center gap-4 h-full animate-scroll">
        {items.map((item) => (
          <NewsCard
            key={item.id}
            severity={item.severity}
            headline={item.title}
            source={item.source}
          />
        ))}
      </div>
    </div>
  );
}
```

---

## 🔍 SEARCH BAR — AUTO-DETECT LOGIC

### Frontend Behavior

```
┌─────────────────────────────────────────────────────────────┐
│   🔍 ▾ Auto-Detect          [  Type anything here...  ] 🔍  │
└─────────────────────────────────────────────────────────────┘
```

| User Input | Detection Result | Search Icon Changes To |
|------------|-----------------|----------------------|
| `mha.gov.in` | 🌐 Domain | Globe icon + label |
| `164.100.24.1` | 📍 IP Address | Map pin icon |
| `admin@mha.gov.in` | 📧 Email | Envelope icon |
| `CVE-2024-6387` | 🆔 CVE ID | Shield icon |
| `+91-9876543210` | 📱 Phone | Phone icon |
| `John Doe` | 👤 Person Name | Person icon |
| `mha_admin` | 🔤 Username | At-sign icon |
| `https://mha.gov.in` | 🔗 URL | Link icon |

### Dropdown Override

User can always override auto-detect by clicking ▾ and selecting manually:

```
┌──────────────────────┐
│  🔍 Auto-Detect      │  ← Selected (or auto-detected)
├──────────────────────┤
│  🌐 Domain Lookup    │
│  📍 IP Address       │
│  📧 Email Address    │
│  👤 Person Name      │
│  🔤 Username         │
│  📱 Phone Number     │
│  🆔 CVE ID           │
│  🔗 URL / Path       │
│  🏢 Organization     │
└──────────────────────┘
```

---

## 📡 SCHEDULED MONITORING SYSTEM

### Architecture

```
Celery Beat (ticks every 60 seconds)
    │
    └── watchlist_checker()
         │
         ├── Query PostgreSQL: "SELECT * FROM watchlists
         │    WHERE next_check <= NOW() AND is_active = TRUE"
         │
         ├── For each due watch (max 10 per Celery worker cycle):
         │    │
         │    ├── 1. Execute the same OSINTPlugin.execute(target)
         │    │       (reuses the exact same plugin as the live API)
         │    │
         │    ├── 2. Compare new result vs last_result (JSON diff)
         │    │
         │    ├── 3. If changes found:
         │    │    ├── Create Alert record in PostgreSQL
         │    │    ├── If webhook configured → POST alert to webhook URL
         │    │    └── If email configured → Send plain-text email
         │    │
         │    └── 4. Update: last_checked = NOW()
         │                last_result = new_result
         │                next_check = NOW() + frequency_hours
         │
         └── Release DB connection
```

### Watch Modal UI

```typescript
// WatchModal.tsx — frequency options
const FREQUENCY_OPTIONS = [
  { value: 6,  label: 'Every 6 hours',  description: 'Best for port scans & subdomains' },
  { value: 12, label: 'Every 12 hours', description: 'Good for CVEs & HTTP changes' },
  { value: 24, label: 'Every 24 hours', description: 'Default — balances freshness & load' },
  { value: 168,label: 'Every 7 days',   description: 'For WHOIS & breach DB lookups' },
];

const NOTIFY_EVENTS = [
  { id: 'new_ports',     label: 'New open ports discovered',    severity: 'warning' },
  { id: 'new_cves',      label: 'New CVEs found',               severity: 'critical' },
  { id: 'cert_expiry',   label: 'SSL cert expires < 30 days',   severity: 'critical' },
  { id: 'new_subdomains',label: 'Subdomains added/removed',     severity: 'info' },
  { id: 'breach_found',  label: 'Breach data found',            severity: 'critical' },
  { id: 'tech_changed',  label: 'Server technology changed',    severity: 'warning' },
  { id: 'path_exposed',  label: 'New admin path discovered',    severity: 'critical' },
];
```

### My Watches Sidebar

```
┌──────────────────────┐
│  📡 My Watches       │
│  ───────────         │
│  🔴 mha.gov.in      │  ← 3 new alerts
│     🚨 3 new threats │
│     ⏱️ checked 2m ago│
│  🟢 delhipolice.gov  │  ← No changes
│     .in              │
│  🟡 164.100.24.1     │  ← Pending check
│     ⏱️ next: 2h     │
│  ───────────         │
│  [ + Watch New ]     │
└──────────────────────┘
```

---

## 🔔 WEBHOOK ALERT SYSTEM

### Supported Events

| Event Type | Trigger | Severity | Retry |
|-----------|---------|----------|-------|
| `new_ports` | New open ports discovered | warning | 3x (5s, 25s, 125s) |
| `new_cves` | New CVEs match target | critical | 3x |
| `cert_expiry` | Cert within 30 days of expiry | critical | 3x |
| `new_subdomains` | Previously unknown subdomains | info | 3x |
| `breach_found` | Email/domain in new breach | critical | 3x |
| `tech_changed` | Server tech changed (Apache→Nginx) | warning | 3x |
| `path_exposed` | New admin path found | critical | 3x |

### Webhook Payload

```json
{
  "event": "new_cves",
  "timestamp": "2026-05-21T14:30:00Z",
  "target": {
    "value": "mha.gov.in",
    "type": "domain",
    "ip": "164.100.24.1"
  },
  "severity": "critical",
  "summary": "2 new CVEs affect mha.gov.in — both critical, one exploited in the wild",
  "details": [
    {
      "cve_id": "CVE-2024-6387",
      "cvss": 9.8,
      "kev": true,
      "affected": "OpenSSH 8.9p1 on port 22",
      "patch": "Upgrade to OpenSSH 9.8+"
    }
  ],
  "map_context": {
    "city": "Delhi",
    "state": "Delhi",
    "coordinates": [28.61, 77.23]
  },
  "share_url": "https://trinetra.local/share/abc123"
}
```

### Webhook Delivery Log

```
┌──────────────────────────────────────────────────────────────┐
│  📋 RECENT WEBHOOK DELIVERIES                                │
├──────────────────────────────────────────────────────────────┤
│  ✅ 2h ago — 3 new ports on mha.gov.in           — 200 OK   │
│  ✅ 1d ago — Cert expires in 14 days             — 200 OK   │
│  ❌ 2d ago — 5 CVEs affecting 164.100.24.1       — 500 ERR  │
│     [↻ Retry]                                                │
└──────────────────────────────────────────────────────────────┘
```

---

## ⚙️ SETTINGS & CONFIGURATION

### Settings Panel — Complete Layout

```
┌─────────────────────────────────────────────────────────────┐
│  ⚙️ SETTINGS                              [X] Close         │
├─────────────────────────────────────────────────────────────┤
│  🔑 API KEYS                                                │
│  (Platform works without these — adds optional data)        │
│                                                              │
│  🌏 Shodan:       [···························] 💾          │
│                   Quota: 0/100 queries this month 🔓        │
│  🛡️ VirusTotal:   [···························] 💾          │
│                   Quota: 0/500 lookups today 🔓             │
│  🔍 Google API:   [···························] 💾          │
│  🕸️ Censys:      [···························] 💾          │
│  📧 Hunter.io:   [···························] 💾          │
│                                                              │
│  Keys stored in browser localStorage only. Never sent to    │
│  our server or logged. API calls go direct from your        │
│  browser to the third-party service.                        │
├─────────────────────────────────────────────────────────────┤
│  🚦 RATE LIMITING STATUS                                    │
│                                                              │
│  Your IP: 103.xxx.xxx.xxx                                   │
│  █████████░░░░░░ 92 / 100 requests this minute 🟢          │
│  Reset in: 47 seconds                                       │
├─────────────────────────────────────────────────────────────┤
│  🌐 PROXY / TOR                                             │
│                                                              │
│  [ ] Route all OSINT queries through Tor proxy              │
│  (Requires Tor daemon running on host)                      │
│                                                              │
│  [ ] Use custom HTTP proxy                                  │
│      URL: [http://proxy.example.com:8080              ]     │
├─────────────────────────────────────────────────────────────┤
│  🔔 WEBHOOKS                                                │
│                                                              │
│  Target URL:  [https://hooks.slack.com/services/T...  ]    │
│  Secret/Tkn:  [·····································]       │
│                                                              │
│  Send alerts for:                                            │
│  [☑] New ports discovered                       Warning    │
│  [☑] New CVEs found                            Critical    │
│  [☑] SSL cert expiry < 30 days                 Critical    │
│  [☐] New subdomains                            Info        │
│  [☑] Breach data found                         Critical    │
│  [☐] Technology changes                        Warning    │
│  [☐] New admin paths discovered                Critical    │
│                                                              │
│  Format:  [📦 JSON  ▼]                                      │
│                                                              │
│  [🔔 Test Webhook]  [💾 Save]                              │
│                                                              │
│  📋 Last delivery: 2h ago — 200 OK                          │
├─────────────────────────────────────────────────────────────┤
│  🔌 PLUGINS & MODULES                                       │
│                                                              │
│  ✅ 20 core tools installed  (all active)                   │
│                                                              │
│  [ 📥 Load Custom Module ]  (.py file)                      │
│                                                              │
│  🌐 Browse community modules (coming soon)                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏆 COMPETITIVE LANDSCAPE SUMMARY

### How We Stack Up

```
TRINETRA vs SpiderFoot (12K⭐) — the market leader

TRINETRA WINS ON:                           SPIDERFOOT WINS ON:
─────────────────────                       ─────────────────────
✅ Map as primary UI                        ✅ 200+ modules
✅ Auto-detect search                       ✅ Mature scheduler
✅ Zero auth / instant start                ✅ Entity graph
✅ India-specific data                      ✅ Webhook support
✅ GUI/Terminal/Split modes                  ❌ No map, no India data
✅ Crime overlay + threat vectors            ❌ Takes 30 minutes to start
✅ Data provenance badges                    ❌ auth required
```

### Score Comparison

| Feature | **TRINETRA** | SpiderFoot | IntelOwl | Recon-ng | theHarvester |
|---------|:---:|:---:|:---:|:---:|:---:|
| Web GUI | ✅ React | ✅ CherryPy | ✅ Vue.js | ❌ CLI | ❌ CLI |
| Map Viz | ✅ **India map** | ❌ | ❌ | ❌ | ❌ |
| Auto-Detect | ✅ **Smart** | ❌ | ❌ | ❌ | ❌ |
| Modules/Tools | 20 curated | 200+ | 50+ | 50+ | 5 |
| India Focus | ✅ **Yes** | ❌ | ❌ | ❌ | ❌ |
| Zero Auth | ✅ **Yes** | ❌ | ❌ | ❌ | ✅ |
| Data Freshness | ✅ **Badges** | ⚠️ Partial | ❌ | ❌ | ❌ |
| Graph View | ✅ **Planned** | ✅ | ❌ | ❌ | ❌ |
| Scheduled Scans | ✅ **Planned** | ✅ | ⚠️ | ❌ | ❌ |
| Webhooks | ✅ **Planned** | ❌ | ✅ | ❌ | ❌ |

**Final Score:** TRINETRA covers **95%** of the OSINT feature set, with the remaining 5% being nice-to-haves.

---

## ✅ IMPLEMENTATION CHECKLIST

### 🟢 Phase 1 — Foundation (Week 1)

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 1.1 | Kill old containers + delete old code | — | ⬜ |
| 1.2 | Create FastAPI scaffold | `backend/app/main.py`, `config.py` | ⬜ |
| 1.3 | Create React + Vite + Tailwind scaffold | `frontend/` init | ⬜ |
| 1.4 | Docker Compose (6 containers) | `docker-compose.yml`, `.env` | ⬜ |
| 1.5 | PostgreSQL schema (all 22 models) | `models/*.py` | ⬜ |
| 1.6 | Search bar with dropdown + auto-detect | `SearchBar.tsx`, `search_detector.py` | ⬜ |
| 1.7 | Landing page | `HomePage.tsx` | ⬜ |

### 🟢 Phase 2 — Map + Dashboard (Week 2)

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 2.1 | India map with Leaflet | `IndiaMap.tsx`, `MapControls.tsx` | ⬜ |
| 2.2 | City pin system (🟢🟡🔴) | `AssetPin.tsx` | ⬜ |
| 2.3 | Hover tooltips | `MapTooltip.tsx` | ⬜ |
| 2.4 | Default dashboard (no search) | `Dashboard.tsx`, `Layout.tsx` | ⬜ |
| 2.5 | Overlay toggles | `MapLayers.tsx` | ⬜ |

### 🟢 Phase 3 — Core OSINT + Plugin System (Weeks 3-4)

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 3.1 | Plugin architecture (BasePlugin + registry) | `base_plugin.py`, `plugin_registry.py` | ⬜ |
| 3.2 | Domain Record (WHOIS) | `whois_service.py`, router, schema, component | ⬜ |
| 3.3 | Name Servers (DNS) | `dns_service.py`, router, schema, component | ⬜ |
| 3.4 | Geo Locator | `geoip_service.py`, router, schema, component | ⬜ |
| 3.5 | Port Scanner | `port_scanner.py`, router, schema, component | ⬜ |
| 3.6 | Hidden Pages | `subdomain_discovery.py`, router, schema, component | ⬜ |
| 3.7 | SSL Health | `certificate_checker.py`, router, schema, component | ⬜ |
| 3.8 | Reverse Trace | `reverse_dns.py`, router, schema, component | ⬜ |
| 3.9 | Tech Fingerprint | `http_headers.py`, router, schema, component | ⬜ |
| 3.10 | ToolResultWrapper (GUI/Terminal/Split) | `ToolResultWrapper.tsx` | ⬜ |
| 3.11 | FreshnessBadge component | `FreshnessBadge.tsx` | ⬜ |
| 3.12 | Redis caching | `cache_service.py` | ⬜ |
| 3.13 | Celery setup | `celery_app.py` | ⬜ |

### 🟢 Phase 4 — Threat OSINT + Settings (Week 5)

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 4.1 | CVE Alerts (NVD + CISA KEV) | `cve_lookup.py`, `cve_sync.py`, component | ⬜ |
| 4.2 | Data Leaks | `breach_checker.py`, component | ⬜ |
| 4.3 | Document Vault | `google_dorking.py`, component | ⬜ |
| 4.4 | Internet Scanner (Shodan) | `shodan_api.py`, component | ⬜ |
| 4.5 | Threat Shield (VirusTotal) | `virustotal_api.py`, component | ⬜ |
| 4.6 | Settings panel (all sections) | `SettingsPanel.tsx` + sub-components | ⬜ |
| 4.7 | Rate limiter | `rate_limiter.py` | ⬜ |

### 🟢 Phase 5 — Person OSINT (Week 6)

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 5.1 | Email Finder (Holehe) | `email_osint.py`, component | ⬜ |
| 5.2 | Username Tracker (Sherlock) | `username_search.py`, component | ⬜ |
| 5.3 | Phone Intel | `phone_osint.py`, component | ⬜ |
| 5.4 | Deep Search | `google_dorking.py` (extended), component | ⬜ |
| 5.5 | Social Radar | `social_media.py`, component | ⬜ |

### 🟢 Phase 6 — Map + Graph Intelligence (Week 7)

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 6.1 | Graph View (Cytoscape.js) | `GraphView.tsx`, `GraphNode.tsx` | ⬜ |
| 6.2 | Graph data mapper | Entity relationship builder | ⬜ |
| 6.3 | Live threat vectors | `ThreatVector.tsx` | ⬜ |
| 6.4 | Crime data overlay | `CrimeOverlay.tsx`, `crime_stats.py` | ⬜ |
| 6.5 | Click drill-down | State→city→asset navigation | ⬜ |
| 6.6 | Surface Scan | `surface_scan.py`, component | ⬜ |
| 6.7 | News ↔ Map linking | NewsStore + map pin pulses | ⬜ |

### 🟢 Phase 7 — Monitoring + Polish (Week 8)

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 7.1 | Watchlist model | `watchlist.py` (model) | ⬜ |
| 7.2 | Watchlist checker (Celery) | `watchlist_checker.py` (task) | ⬜ |
| 7.3 | Watch button + modal | `WatchButton.tsx`, `WatchModal.tsx` | ⬜ |
| 7.4 | My Watches sidebar | `MyWatches.tsx` | ⬜ |
| 7.5 | Alert model | `alert.py` (model) | ⬜ |
| 7.6 | Webhook config UI | `WebhookConfig.tsx` | ⬜ |
| 7.7 | Webhook dispatcher | Alert → POST logic | ⬜ |
| 7.8 | Report export (PDF, JSON, CSV) | `report_generator.py`, router | ⬜ |
| 7.9 | Ephemeral share links | Share link generation logic | ⬜ |
| 7.10 | Seed data (all files) | `seed_data/*.py` | ⬜ |
| 7.11 | Mobile responsiveness | CSS media queries, responsive layout | ⬜ |
| 7.12 | Performance optimization | Map clustering, lazy loading, memo | ⬜ |

---

## 📚 REFERENCE: KEY DEPENDENCIES

### Backend (requirements.txt)

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy[asyncio]==2.0.35
asyncpg==0.30.0
alembic==1.14.0
redis[hiredis]==5.2.0
celery[redis]==5.4.0
pydantic==2.9.0
pydantic-settings==2.5.0
python-whois==0.9.5
dnspython==2.7.0
geoip2==4.8.1
requests==2.32.0
beautifulsoup4==4.12.0
lxml==5.3.0
cryptography==43.0.0
httpx==0.28.0
python-multipart==0.0.12
```

### Frontend (package.json)

```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.26.0",
    "leaflet": "^1.9.4",
    "react-leaflet": "^4.2.1",
    "cytoscape": "^3.30.0",
    "react-cytoscapejs": "^2.0.0",
    "xterm": "^5.3.0",
    "xterm-addon-fit": "^0.8.0",
    "zustand": "^4.5.0",
    "axios": "^1.7.0",
    "date-fns": "^3.6.0",
    "lucide-react": "^0.441.0"
  },
  "devDependencies": {
    "typescript": "^5.5.0",
    "vite": "^5.4.0",
    "@vitejs/plugin-react": "^4.3.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0",
    "@types/leaflet": "^1.9.0",
    "@types/cytoscape": "^3.21.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0"
  }
}
```

---

## 📋 VERSION HISTORY

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | May 2026 | AI Planning | Initial comprehensive planner |
| 1.1 | May 2026 | AI Planning | Added monitoring, webhooks, graph view, settings, data provenance |

---

*This document is the living implementation bible for TRINETRA. Update it as decisions change during development.*
