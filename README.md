

<div align="center">
  <br/>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/TRINETRA-v1.0.0-8b5cf6?style=for-the-badge&logo=appveyor&labelColor=0b0f1a">
    <img src="https://img.shields.io/badge/TRINETRA-v1.0.0-8b5cf6?style=for-the-badge&logo=appveyor&labelColor=0b0f1a" alt="TRINETRA">
  </picture>
  <br/>
  <h3>India-Focused OSINT Intelligence Dashboard</h3>
  <p>
    <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.11+"/>
    <img src="https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=white" alt="React 18"/>
    <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI"/>
    <img src="https://img.shields.io/badge/PostgreSQL-15-4169E1?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL"/>
    <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker Compose"/>
    <img src="https://img.shields.io/badge/TypeScript-5.6-3178C6?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript 5.6"/>
    <img src="https://img.shields.io/badge/Leaflet-1.9-199900?style=flat-square&logo=leaflet&logoColor=white" alt="Leaflet 1.9"/>
    <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="MIT License"/>
    <img src="https://img.shields.io/badge/tests-138%20passed-brightgreen?style=flat-square" alt="138 Tests Passing"/>
  </p>
  <br/>
</div>

> **Search any domain, IP, email, phone, or name — get 360° threat intelligence in seconds.**
>
> TRINETRA is an all-in-one OSINT platform built for India. It combines 19 parallel OSINT plugins, a live threat feed powered by real malicious IP data, and an automated watch monitoring system — all wrapped in a dark-themed interactive map dashboard.

<br/>

<p align="center">
  <b>🔍 OSINT Search</b>&nbsp;&nbsp;·&nbsp;&nbsp;
  <b>🗺️ Live Threat Map</b>&nbsp;&nbsp;·&nbsp;&nbsp;
  <b>📡 Real-Time Feed</b>&nbsp;&nbsp;·&nbsp;&nbsp;
  <b>👁️ Watch Monitoring</b>&nbsp;&nbsp;·&nbsp;&nbsp;
  <b>📊 Professional Reports</b>&nbsp;&nbsp;·&nbsp;&nbsp;
  <b>🧠 Relationship Graphs</b>
</p>

<br/>

---

## 📸 Dashboard Preview

<p align="center">
  <i>🚀 The dashboard features an interactive India threat map, live attack vectors from real threat intelligence feeds, city risk analysis, and comprehensive search results — all in one unified dark-themed interface.</i>
</p>

<br/>

---

## ⚡ Quick Start

```bash
# 1. Clone and enter
git clone https://github.com/K921-cyber/trinetra.git
cd trinetra

# 2. Environment setup
cp .env.example .env
# ⚠️ Edit .env with your API keys (optional — most features work without keys)

# 3. Launch everything
docker compose up --build -d
```

Open **http://localhost:3000** — that's it.

> **Prerequisites:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/Mac) or Docker Engine (Linux)

<br/>

---

## 🎯 What TRINETRA Does

### The Problem

Investigating a single domain typically means juggling **9+ separate tools**:

| Task | Tool | Time |
|------|------|------|
| WHOIS lookup | Separate website | ~2 min |
| DNS records | Another site | ~2 min |
| Port scan | nmap / Shodan | ~5 min |
| SSL check | Yet another tool | ~1 min |
| Subdomain discovery | crt.sh | ~2 min |
| Data breach check | Have I Been Pwned | ~1 min |
| CVE lookup | NVD | ~2 min |
| Tech fingerprint | Wappalyzer | ~1 min |
| Geo-location | ip-api.com | ~1 min |

**Total: 15–30 minutes** of context switching between tabs.

### TRINETRA's Solution

```
┌─────────────────────────────────────────────────────────────┐
│                    One Search. 19 Plugins.                   │
│                    Results in 10–15 seconds.                 │
└─────────────────────────────────────────────────────────────┘
```

**Three independent systems running simultaneously:**

#### 🔍 1. On-Demand OSINT Search
```
  Target Query ──→ Auto-Detect Type ──→ 19 Parallel Plugins ──→ Results Stream Live
                      │
                 domain / IP /
                 email / phone / name
```
- Auto-detects the target type (domain, IP, email, phone, or name)
- Fires all matching OSINT plugins in parallel via `asyncio.gather`
- Streams results back via WebSocket as each plugin completes
- Results in 10–15 seconds for a full deep-dive

#### 📡 2. Live Threat Feed (Background Loop)
```
ThreatFox ──┐
Feodo     ──┼──→ Fetch Real Malicious IPs ──→ Geo-locate ──→ Animate on Map
IPsum    ───┘                              Every 8-12 seconds
                                            
RSS Feeds ──→ The Hacker News / BleepingComputer / Krebs / Record
```
- Fetches real malicious IPs from Abuse.ch ThreatFox, Feodo Tracker, and IPsum
- Geo-locates them via ip-api.com (free tier)
- Animates attack vectors on the India map with origin intelligence
- Streams live cyber news headlines alongside attack data
- **No API key required** — all sources are free and public

#### 👁️ 3. Watch Monitoring (Background Checks)
```
Scheduler ──→ Check Due Watches ──→ Run Plugins ──→ Compare with Previous Scan
                                                         │
                                                    Change detected?
                                                    ├── Yes → Alert created
                                                    └── No  → Skip
```
- Configure targets to be re-scanned at intervals from 5 minutes to 7 days
- Automatic change detection — get alerted when results differ
- Select which specific plugins run for each watch

<br/>

---

## ✨ Features

### 🔍 OSINT Search (19 Plugins)

| Category | Plugins | What They Find |
|----------|---------|----------------|
| **Infrastructure** | WHOIS, DNS Lookup, Port Scanner, SSL Health, Subdomain Finder, Reverse DNS, Name Servers, HTTP Headers, Tech Fingerprint | Registrar info, A/MX/NS records, open ports, certificate validity, subdomains, tech stack |
| **Threat Intel** | CVE Alerts, Data Leaks, Document Vault | Known vulnerabilities (NVD), breach data (LeakIX, XposedOrNot, LeakCheck), document metadata |
| **Person Recon** | Email Finder, Phone Intel, Username Tracker | Email reputation (EmailRep.io, Gravatar, 20+ platforms), phone number intel, social media presence |
| **Advanced** | Deep Search, Surface Scan, Social Radar, Live Feed | Web intelligence, surface web recon, social media footprint, real-time indicators |

**Every plugin queries live, free data sources** — no simulated or placeholder results.

### 🗺️ Interactive India Threat Map

- **Animated attack vectors** — Dashed lines with traveling dots from 25+ origin countries to Indian cities
- **City risk markers** — Color-coded circles (green/yellow/red) based on NCRB 2022 cyber crime statistics
- **Crime heatmap overlay** — State-wise NCRB cyber crime data with hover tooltips and click popups
- **Destination threat pins** — Aggregated attack destination markers showing live vector count, origin countries, attack types, and feed sources
- **Threat Intelligence panel** — Severity distribution bars, origin intelligence summary (flags + counts), detailed attack routes table
- **Live attack counter** — Real-time badge with critical/medium breakdown and LIVE indicator
- **Data Sources Health panel** — Live status of ThreatFox, Feodo, IPsum, ip-api.com, RSS feeds

### 📡 Real-Time Threat Feed

- **Live events timeline** — Filterable by All, Attacks, Events, or News
- **Attack vector cards** — Color-coded by severity with origin→target route, type, and timestamp
- **Cyber news** — Latest headlines from The Hacker News, BleepingComputer, KrebsOnSecurity, The Record
- **Vector detail modal** — Full intelligence with copy IP, ISP, organization, AbuseIPDB/AlienVault/CERT-In report actions

### 📊 Professional Report View

- **Three view modes** — GUI (structured table), Terminal (raw output), Split (both side-by-side)
- **Export options** — Copy to clipboard, download as `.txt`, print/save as PDF
- **Full system report** — Executive summary, threat landscape, watches & alerts, intelligence events, recent scans

### 🧠 Relationship Graph

- **Dynamic Cytoscape visualization** — Auto-generated graph connecting search results by relationships
- **Color-coded node types** — Infrastructure (blue), Threat (red), Person (purple), Advanced (orange)
- **Export to PNG** — Save graphs at 2x resolution for reports

### 👁️ Watch & Monitoring

- **Automated re-scanning** — Every 5 minutes to 7 days
- **Smart change detection** — Compares `gui_data` across scans, generates human-readable diffs
- **Alert history** — Full timeline of changes per watch target
- **Plugin-level control** — Select exactly which plugins to run per watch

### 🛡️ India-Specific Intelligence

- **NCRB 2022 cyber crime data** embedded for all 23 states/UTs
- **70+ curated India-specific data breaches** (Aadhaar, IRCTC, BigBasket, CoWIN, etc.)
- **India-focused map** with state boundaries, city markers, crime heatmap
- **Target city modeling** — Attack destinations statistically assigned from NCRB data

<br/>

---

## 🏗️ Architecture

```
                    ┌──────────────────────────────────────┐
                    │   User's Browser (port 3000)          │
                    │   React 18 + TypeScript + Vite        │
                    │   Leaflet Map + Cytoscape Graphs      │
                    └──────────────┬──────────┬─────────────┘
                                  HTTP       WebSocket
                                    │            │
                    ┌───────────────▼────────────▼─────────────┐
                    │           nginx (port 3000)               │
                    │   Serves static build /api/* → backend   │
                    │              /ws/* → backend             │
                    └──────────────────────┬───────────────────┘
                                           │
                    ┌──────────────────────▼───────────────────┐
                    │    FastAPI Backend (port 8000)            │
                    │                                          │
                    │  ┌──────────┐  ┌──────────────────────┐  │
                    │  │ REST API │  │  WebSocket Streaming  │  │
                    │  │ /search  │  │  /ws/search           │  │
                    │  │ /watch   │  │  /ws/threat-feed      │  │
                    │  │ /plugins │  └──────────────────────┘  │
                    │  └────┬─────┘                            │
                    │        │                                 │
                    │  ┌────▼─────────────────────────────┐    │
                    │  │    Plugin Orchestrator            │    │
                    │  │   ┌──────────┐ ┌──────────┐      │    │
                    │  │   │ 19 OSINT │ │ Thread   │      │    │
                    │  │   │ Plugins  │ │ Scheduler│      │    │
                    │  │   └──────────┘ └──────────┘      │    │
                    │  └──────────────────────────────────┘    │
                    │                                          │
                    │  ┌──────────────────────┐  ┌──────────┐ │
                    │  │ Threat Feed Service  │  │ TaskIQ   │ │
                    │  │ (background loop)    │  │ Worker   │ │
                    │  └──────────────────────┘  └──────────┘ │
                    └────────────┬────────┬────────┬──────────┘
                                │        │        │
                    ┌───────────▼──┐ ┌───▼───┐ ┌─▼──────────┐
                    │  PostgreSQL  │ │ Redis │ │  External   │
                    │  (watches,   │ │(cache)│ │  APIs &     │
                    │   alerts)    │ │       │ │  Feeds      │
                    └──────────────┘ └───────┘ └─────────────┘
```

### Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 18 + TypeScript + Vite | UI — map, reports, graphs |
| **Mapping** | Leaflet + react-leaflet | India threat map with animations |
| **Graphs** | Cytoscape + cytoscape-dagre | Relationship visualization |
| **Backend** | FastAPI + Python 3.11 | REST API + WebSocket server |
| **Database** | PostgreSQL 15 / SQLite | Persistent storage (watches, alerts) |
| **Cache** | Redis | Task queue + caching |
| **Worker** | TaskIQ | Background watch execution |
| **Data** | httpx + aiohttp + feedparser | External API calls + RSS parsing |
| **Container** | Docker + Docker Compose | Deployment |

<br/>

---

## 📡 Real Data Sources

All data in TRINETRA is **real** — no simulated or placeholder data.

### Threat Intelligence Feeds
| Source | Type | Data Provided | Key Required? |
|--------|------|---------------|---------------|
| [Abuse.ch ThreatFox](https://threatfox.abuse.ch/) | Malware IOCs | Malicious IPs, malware families, attack types | ❌ Free |
| [Feodo Tracker](https://feodotracker.abuse.ch/) | C2 Tracker | C2 server IPs, botnet malware (Dridex, Emotet, QakBot) | ❌ Free |
| [IPsum](https://github.com/stamparm/ipsum) | IP Blacklist | Blacklisted IPs with detection scores | ❌ Free |
| [ip-api.com](https://ip-api.com/) | Geo-location | Country, city, lat/lon, ISP, org (free: 45 req/min) | ❌ Free |

### OSINT Plugins (19 total)
| Plugin | Source | Key Required? |
|--------|--------|---------------|
| WHOIS Lookup | whois servers (direct) | ❌ Free |
| DNS Records | dnspython (direct) | ❌ Free |
| Port Scanner | Built-in TCP scanner | ❌ Free |
| SSL Health | OpenSSL / direct | ❌ Free |
| Subdomain Finder | crt.sh | ❌ Free |
| Reverse DNS | dnspython | ❌ Free |
| Name Servers | dnspython | ❌ Free |
| HTTP Headers | httpx | ❌ Free |
| Tech Fingerprint | Wappalyzer (regex-based) | ❌ Free |
| CVE Alerts | NVD API | ❌ Free |
| Data Leaks | LeakIX, XposedOrNot, LeakCheck | ❌ Free |
| Document Vault | Direct checks | ❌ Free |
| Email Finder | EmailRep.io | ❌ Free |
| Phone Intel | phonenumbers library | ❌ Free |
| Username Tracker | Social platform HEAD requests | ❌ Free |
| Deep Search | DuckDuckGo + Bing | ❌ Free |
| Surface Scan | Built-in crawler | ❌ Free |
| Social Radar | Social media HEAD checks | ❌ Free |
| Live Feed | RSS (THN, BleepingComputer, Krebs, Record) | ❌ Free |

### RSS News Feeds
| Feed | Topic |
|------|-------|
| [The Hacker News](https://thehackernews.com/) | General cybersecurity |
| [BleepingComputer](https://www.bleepingcomputer.com/) | Tech news + malware |
| [KrebsOnSecurity](https://krebsonsecurity.com/) | In-depth security reporting |
| [The Record](https://therecord.media/) | Cyber crime + policy |

### India-Specific Data
| Source | Description |
|--------|-------------|
| **NCRB 2022** | Cyber crime statistics for 23 Indian states/UTs | 
| **Local Breach DB** | 70+ curated India-specific breaches (Aadhaar, IRCTC, BigBasket, CoWIN, etc.) |

<br/>

---

## 🚀 Setup Guide

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/Mac) or Docker Engine (Linux)
- [Git](https://git-scm.com/)

### Quick Start (2 Minutes)

```bash
# 1. Clone the repository
git clone https://github.com/K921-cyber/trinetra.git
cd trinetra

# 2. Configure environment variables
cp .env.example .env

# 3. Launch the full stack
docker compose up --build -d
```

### Access the Dashboard

| Service | URL |
|---------|-----|
| **Dashboard** | [http://localhost:3000](http://localhost:3000) |
| **API Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) |
| **Health Check** | [http://localhost:8000/health](http://localhost:8000/health) |

### Common Commands

```bash
docker compose up -d                 # Start all services
docker compose up --build -d         # Rebuild and start
docker compose down                  # Stop all services
docker compose down -v               # Stop and clear volumes
docker compose logs -f backend       # Watch backend logs
docker compose logs -f frontend      # Watch frontend logs
docker compose ps                    # Check container health
```

### Configuration (.env)

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | TRINETRA | Application name |
| `DEBUG` | `true` | Enable debug mode |
| `DATABASE_URL` | SQLite (dev) / PostgreSQL (Docker) | Database connection |
| `REDIS_URL` | `redis://redis:6379` | Redis connection |
| `API_KEY` | (empty) | Optional API key for auth |

### Running Without Docker (Local Dev)

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

<br/>

---

## 📡 API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/search` | Run OSINT scan on a target | Optional |
| `GET` | `/api/search/{target}` | GET variant of search | Optional |
| `GET` | `/api/detect?target=` | Auto-detect target type | Optional |
| `GET` | `/api/plugins` | List all 19 OSINT plugins | Optional |
| `GET` | `/api/target-intel?target=` | Web intelligence (DuckDuckGo + news) | Optional |
| `GET` | `/api/crime-data` | NCRB 2022 cyber crime data | ❌ Public |
| `GET` | `/api/health/sources` | Health of all data sources | ❌ Public |
| `GET` | `/api/watches` | List all watches | Optional |
| `POST` | `/api/watches` | Create a watch | Optional |
| `GET` | `/api/watches/{id}` | Get watch details | Optional |
| `DELETE` | `/api/watches/{id}` | Delete a watch | Optional |
| `POST` | `/api/watches/{id}/toggle` | Pause/resume a watch | Optional |
| `GET` | `/api/watches/alerts` | Recent alerts across all watches | Optional |
| `GET` | `/api/watches/{id}/alerts` | Alerts for a specific watch | Optional |
| `WS` | `/ws/search` | Streaming OSINT search | Optional |
| `WS` | `/ws/threat-feed` | Live threat feed (map data) | Optional |
| `GET` | `/health` | Backend health check | ❌ Public |

<br/>

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| **OSINT Search (19 plugins)** | 10–15 seconds (parallel execution) |
| **Threat feed fetch interval** | Every 10 minutes |
| **Map animation refresh** | Every 8–12 seconds |
| **Watch scheduler check** | Every 60 seconds |
| **API rate limit (search)** | 10 req/min per IP |
| **API rate limit (general)** | 60 req/min per IP |
| **Geo-location limit** | ~40 req/min (ip-api.com free tier) |
| **Max attack vectors stored** | 50 (rolling buffer) |
| **Max headlines stored** | 200 (rolling buffer) |
| **Unit tests** | **138 passing** |

<br/>

---

## 🧪 Running Tests

```bash
cd backend
pytest tests/ -v           # Run all 138 tests
pytest tests/ -v --cov     # Run with coverage report
```

<br/>

---

## 🗂️ Project Structure

```
trinetra/
├── backend/
│   ├── app/
│   │   ├── api/           # REST + WebSocket routes
│   │   │   ├── routes.py          # Search, detect, plugins
│   │   │   ├── websocket_routes.py # Streaming search WS
│   │   │   ├── watch_routes.py     # Watch CRUD + alerts
│   │   │   ├── threat_routes.py    # Live threat feed WS
│   │   │   └── data_routes.py      # Crime data, health
│   │   ├── core/          # Config, auth, rate limiting
│   │   ├── models/        # Pydantic schemas
│   │   ├── plugins/       # 19 OSINT plugins (4 categories)
│   │   │   ├── infrastructure/  # 9 plugins
│   │   │   ├── threat/          # 3 plugins
│   │   │   ├── person/          # 3 plugins
│   │   │   └── advanced/        # 4 plugins
│   │   ├── services/      # Orchestrator, threat feed, DB
│   │   ├── tasks/         # Watch scheduler + execution
│   │   └── data/          # NCRB 2022 crime statistics
│   ├── tests/             # 138 unit tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   │   ├── Map/           # IndiaMap, destination pins
│   │   │   ├── SearchBar/     # Auto-detect input
│   │   │   ├── ReportView/    # Plugin detail report
│   │   │   ├── FullReportView/# Full system report
│   │   │   ├── LiveFeed/      # Real-time events page
│   │   │   ├── WatchPanel/    # Watch management
│   │   │   ├── GraphView/     # Relationship graph
│   │   │   ├── VectorDetailModal/ # Attack detail modal
│   │   │   ├── Sidebar/       # Plugin status sidebar
│   │   │   └── ...            # Stats, toast, icons, etc.
│   │   ├── store/        # AppContext + ThreatContext
│   │   ├── types/        # TypeScript type definitions
│   │   ├── utils/        # API client, hooks, helpers
│   │   └── styles.css    # Complete design system
│   └── package.json
├── docker-compose.yml
├── docker-compose.override.yml
└── README.md
```

<br/>

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

- **Report bugs** — Open an issue with reproduction steps
- **Suggest features** — Open an issue with your idea
- **Add plugins** — New OSINT plugins welcome! See the base class in `backend/app/plugins/base.py`
- **Improve the map** — Better visualizations, new overlays, performance optimizations

### Development Setup

```bash
# Backend (local)
cd backend
pip install -r requirements.txt
pip install pytest pytest-asyncio  # For running tests
uvicorn app.main:app --reload

# Frontend (local)
cd frontend
npm install
npm run dev
```

<br/>

---

## 📄 License
s
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

<br/>

---

<div align="center">
  <p>
    <b>Built with 🛡️ for India's cybersecurity community</b>
  </p>
  <p>
    <sub>TRINETRA — Open Source Intelligence for a safer digital India</sub>
  </p>
  <br/>
  <p>
    <a href="https://github.com/K921-cyber/trinetra/issues">Report Bug</a> ·
    <a href="https://github.com/K921-cyber/trinetra/issues">Request Feature</a> ·
    <a href="https://github.com/K921-cyber/trinetra">GitHub</a>
  </p>
</div>


