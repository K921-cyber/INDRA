<br/>

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
    <img src="https://img.shields.io/badge/TypeScript-5.6-3178C6?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript 5.6"/>
    <img src="https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker"/>
    <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL"/>
    <img src="https://img.shields.io/badge/Leaflet-1.9-199900?style=flat-square&logo=leaflet&logoColor=white" alt="Leaflet 1.9"/>
    <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="MIT License"/>
  </p>
  <br/>
</div>

> **Search any domain, IP, email, phone, or name — get 360° threat intelligence in seconds.**
>
> TRINETRA is an all-in-one OSINT platform built for India. It combines **15 parallel OSINT plugins**, a **live threat feed** powered by real malicious IP data, **automated watch monitoring**, and an **interactive threat map dashboard**.

<br/>

<p align="center">
  <b>🐳 Docker Ready</b>&nbsp;&nbsp;·&nbsp;&nbsp;
  <b>🔍 OSINT Search</b>&nbsp;&nbsp;·&nbsp;&nbsp;
  <b>🗺️ Live Threat Map</b>&nbsp;&nbsp;·&nbsp;&nbsp;
  <b>📡 Real-Time Feed</b>&nbsp;&nbsp;·&nbsp;&nbsp;
  <b>👁️ Watch Monitoring</b>&nbsp;&nbsp;·&nbsp;&nbsp;
  <b>📊 Professional Reports</b>&nbsp;&nbsp;·&nbsp;&nbsp;
  <b>🧠 Relationship Graphs</b>&nbsp;&nbsp;·&nbsp;&nbsp;
  <b>🔐 User Registration</b>
</p>

<br/>

---

<br/>

---

## 🚀 Run This in 60 Seconds

```bash
git clone <your-repo-url>
cd trinetra
cp .env.example .env        # set POSTGRES_PASSWORD inside
docker compose -p indra2 up -d --build
```

Then open **http://localhost:3000**, click **Register**, and start searching. Full details in [⚡ Quick Start (Docker)](#-quick-start-docker) below.

<br/>

---

## 📋 Table of Contents

- [⚡ Quick Start (Docker)](#-quick-start-docker)
- [🛠️ Manual Installation (No Docker)](#️-manual-installation-no-docker)
- [🎯 What TRINETRA Does](#-what-trinetra-does)
- [🏗️ Architecture & Workflow](#️-architecture--workflow)
- [🔍 OSINT Search — How It Works](#-osint-search--how-it-works)
- [📡 Live Threat Feed](#-live-threat-feed)
- [👁️ Watch Monitoring](#️-watch-monitoring)
- [🤖 AI Chatbot Assistant](#-ai-chatbot-assistant)
- [🗺️ Interactive Map](#️-interactive-map)
- [🔐 Authentication & User System](#-authentication--user-system)
- [📡 Real Data Sources](#-real-data-sources)
- [✨ Features](#-features)
- [📡 API Reference](#-api-reference)
- [🗂️ Project Structure](#️-project-structure)
- [⚙️ Configuration Reference](#️-configuration-reference)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

<br/>

---

## ⚡ Quick Start (Docker)

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (version 24+)
- [Docker Compose](https://docs.docker.com/compose/install/) (included with Docker Desktop)

### Setup

```bash
# Clone the repository
git clone https://github.com/your-org/trinetra.git
cd trinetra

# (Optional) Copy and customize environment variables
cp .env.example .env
# Edit .env — at minimum set POSTGRES_PASSWORD

# Start all services (project name: indra2)
docker compose -p indra2 up -d
```

### Access Points

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | [http://localhost:3000](http://localhost:3000) | React dashboard — register & start searching |
| **Backend API** | [http://localhost:8000](http://localhost:8000) | FastAPI REST API |
| **API Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive Swagger documentation |
| **PostgreSQL** | `localhost:5432` | Main database (auth uses dedicated SQLite) |
| **Redis** | `localhost:6380` | Cache & TaskIQ broker |

### First-Time Steps

1. Open [http://localhost:3000](http://localhost:3000)
2. Click **Register** and create an account (first user becomes admin)
3. Start searching domains, IPs, emails, phones, or names

### Container Architecture

```
┌──────────────────────────────────────────────────────┐
│                   Docker Compose (indra2)              │
│                                                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────┐  │
│  │ Frontend │  │ Backend  │  │ Worker   │  │ DB   │  │
│  │ :3000→80 │  │ :8000    │  │ (TaskIQ) │  │:5432 │  │
│  │  React   │  │ FastAPI  │  │  Async   │  │ PG15 │  │
│  │  Nginx   │  │ Uvicorn  │  │  Tasks   │  │      │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──┬───┘  │
│       └─────────────┴─────────────┴────────────┘      │
│                         │                             │
│                    ┌────▼─────┐                       │
│                    │  Redis   │                       │
│                    │  :6380   │                       │
│                    │  Cache   │                       │
│                    └──────────┘                       │
└──────────────────────────────────────────────────────┘
```

### Useful Docker Commands

```bash
# View container logs
docker compose -p indra2 logs -f backend    # Backend logs
docker compose -p indra2 logs -f frontend   # Frontend logs

# Restart a service
docker compose -p indra2 restart backend

# Rebuild after code changes
docker compose -p indra2 build backend

# Stop everything
docker compose -p indra2 down

# Stop and delete volumes (wipes database)
docker compose -p indra2 down -v
```

<br/>

---

## 🛠️ Manual Installation (No Docker)

### Prerequisites

- Python 3.11+
- Node.js 18+
- SQLite (included with Python) or PostgreSQL 15 (optional)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the backend server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8010 --reload
```

The database (`trinetra.db`) and users table are created automatically on first startup. The first user to register becomes an admin.

### Frontend Setup

```bash
cd frontend
npm install
npx vite --host 0.0.0.0 --port 3000
```

### TaskIQ Worker (Optional — only needed if you set `REDIS_URL`)

By default in manual mode `REDIS_URL` is empty, so watch re-checks run **inline** inside the backend process automatically — you don't need this step for Watch Monitoring to work. Only run a separate worker if you've deliberately set `REDIS_URL` in `.env` to mimic the production setup:

```bash
cd backend
source venv/bin/activate
taskiq worker app.tasks.broker:broker app.tasks.watch_tasks
```

Then open **http://localhost:3000** — register a new account and start searching.

> **Note on ports:** In Docker mode the backend runs on port **8000**. In manual mode it runs on port **8010**. All API examples in this README use port **8000** for Docker. For manual mode, replace `8000` with `8010`.

<br/>

---

## 🎯 What TRINETRA Does

### The Problem

Investigating a single domain typically means juggling **multiple separate tools**:

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
┌─────────────────────────────────────────────────────────┐
│              One Search. 15 Plugins.                      │
│              Results in 10–15 seconds.                    │
└─────────────────────────────────────────────────────────┘
```

**Five independent systems running simultaneously:**

1. **🔍 On-Demand OSINT Search** — Run 15 parallel plugins against any target
2. **📡 Live Threat Feed** — Background loop fetching real malicious IPs and cyber news
3. **👁️ Watch Monitoring** — Automated re-scanning with change detection alerts
4. **🗺️ Interactive Threat Map** — Real-time India-focused attack visualization
5. **🤖 AI Chatbot Assistant** — In-app SOC-analyst helper that explains findings and generates downloadable Word reports

<br/>

---

## 🏗️ Architecture & Workflow

```
                    ┌──────────────────────────────────────────┐
                    │   User's Browser (port 3000)              │
                    │   React 18 + TypeScript + Vite            │
                    │   Leaflet Map + Cytoscape Graphs          │
                    └──────────────┬──────────┬─────────────────┘
                                  HTTP       WebSocket
                                    │            │
                    ┌───────────────▼────────────▼─────────────┐
                    │         FastAPI Backend                   │
                    │         (port 8000 Docker / 8010 Manual)  │
                    │                                          │
                    │  ┌──────────┐  ┌────────────────────┐    │
                    │  │ REST API │  │ WebSocket Streaming│    │
                    │  │ /search  │  │ /ws/search         │    │
                    │  │ /auth/*  │  │ /ws/threats        │    │
                    │  │ /watch   │  └────────────────────┘    │
                    │  │ /plugins │                            │
                    │  └────┬─────┘                            │
                    │        │                                 │
                    │  ┌────▼─────────────────────────────┐    │
                    │  │    Plugin Orchestrator            │    │
                    │  │   ┌──────────┐ ┌──────────┐      │    │
                    │  │   │ 15 OSINT │ │ Watch    │      │    │
                    │  │   │ Plugins  │ │ Scheduler│      │    │
                    │  │   └──────────┘ └──────────┘      │    │
                    │  └──────────────────────────────────┘    │
                    │                                          │
                    │  ┌──────────────────────┐  ┌──────────┐ │
                    │  │ Threat Feed Service  │  │ TaskIQ   │ │
                    │  │ (background loop)    │  │ Worker   │ │
                    │  └──────────────────────┘  └──────────┘ │
                    │                                          │
                    │  ┌──────────────────┐                    │
                    │  │ Telegram Bot     │                    │
                    │  │ (optional)       │                    │
                    │  └──────────────────┘                    │
                    └──────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 18 + TypeScript + Vite | Dashboard UI, map, reports, graphs, live feed, watch panel |
| **Mapping** | Leaflet + react-leaflet | India threat map with animated attack vectors |
| **Graphs** | Cytoscape + cytoscape-dagre | Relationship visualization from scan results |
| **Backend** | FastAPI + Python 3.11 | REST API + WebSocket server |
| **Database** | PostgreSQL 15 (Docker) / SQLite (manual) | Main data storage |
| **Auth DB** | SQLite (dedicated `trinetra_auth.db`) | User accounts, sessions — independent of main DB |
| **Cache** | Redis 7 (Docker) | TaskIQ broker, caching |
| **Worker** | TaskIQ | Background watch task execution |
| **Data** | httpx + feedparser | External API calls + RSS parsing |
| **AI Chatbot** | Google Gemini API | In-app SOC assistant + report generation |
| **Report Export** | python-docx | Markdown → Word (.docx) report conversion |
| **Bot** | python-telegram-bot | Telegram OSINT leak search (optional) |

<br/>

---

## 🔍 OSINT Search — How It Works

### Workflow

```
Target Query → Input Sanitizer → Auto-Detect Type → 15 Parallel Plugins → Stream Results
                      │                    │
                Control chars,        domain / IP /
                injection checks      email / phone / name
```

### Step-by-Step

1. **Input Sanitization** — Validated against maximum length, no control characters, null bytes, or shell metacharacters
2. **Auto-Detect Type** — Regex matching for IP, email, domain, phone; falls back to "name"
3. **Plugin Registry** — Auto-discovers all `OSINTPlugin` subclasses at startup
4. **Plugin Orchestration** — Fires matching plugins concurrently via `asyncio.gather` with 30s timeout
5. **WebSocket Streaming** — Results stream back in real-time as they complete

### The 15 OSINT Plugins

| Category | Plugin ID | Name | What It Finds | Input Types |
|----------|-----------|------|---------------|-------------|
| **Infrastructure** | `domain-record` | Domain Record | WHOIS registration, registrar info, creation/expiry dates | domain |
| | `name-servers` | Name Servers | DNS records: A, AAAA, MX, NS, CNAME, TXT, SOA | domain |
| | `port-scanner` | Port Scanner | Open TCP ports (24 common ports), service identification | domain, ip |
| | `ssl-health` | SSL Health | Certificate validity, cipher suites, protocol support, grade | domain |
| | `subdomain-finder` | Subdomain Finder | Subdomains via crt.sh, HackerTarget API, DNS brute-force (185+ prefixes) | domain |
| | `geo-locator` | Geo Locator | Server location, country, city, ISP, ASN, coordinates | domain, ip |
| | `http-headers` | HTTP Headers | Security headers (HSTS, CSP, XFO, etc.), server info, cookies | domain |
| | `tech-fingerprint` | Tech Fingerprint | Web server, frameworks, CMS, Cloudflare detection | domain |
| **Threat Intel** | `cve-alerts` | CVE Alerts | Known vulnerabilities from NVD API matching target | domain, ip |
| | `data-leaks` | Data Leaks | Breach data from XposedOrNot, LeakCheck, LeakIX + curated breach DB (70+ India-specific breaches) | domain, email, username |
| | `document-vault` | Document Vault | Exposed documents, .env, .git/config, backup files on common paths | domain |
| | `osint-leak` | OSINT Leak | Deep breach search via Leakosint API (email, phone, name, IP, username) | email, phone, username, name, ip |
| **Advanced** | `deep-search` | Deep Search | Google dorking queries for sensitive files, admin panels, backups | domain, name |
| | `live-feed` | Live Feed | Real-time cyber news from RSS feeds (The Hacker News) | domain, ip, name |
| | `surface-scan` | Surface Scan | Aggregated risk score, attack surface analysis, key port scanning | domain, ip |

### Performance

| Metric | Value |
|--------|-------|
| **Full scan (all matching plugins)** | 10–15 seconds |
| **Plugins run per search** | Up to 15 (depending on target type) |
| **API rate limit (search)** | 10 req/min per IP |
| **Plugin timeout** | 30 seconds (configurable) |

<br/>

---

## 📡 Live Threat Feed

### Background Services

#### 1. RealThreatService (Malicious IP Fetcher)

- **Interval**: Every 10 minutes
- **Sources**: Three free threat intelligence feeds in parallel
  - **ThreatFox** (Abuse.ch) — Malware IOCs
  - **Feodo Tracker** — C2 server IPs (Dridex, Emotet, QakBot)
  - **IPsum** — Blacklisted IPs with detection scores
- **Processing**: Parse IPs, geo-locate via ip-api.com, build attack vectors, cache results

#### 2. RealNewsService (RSS News Fetcher)

- **Interval**: Every 5 minutes
- **Sources**: The Hacker News, BleepingComputer, KrebsOnSecurity, The Record
- **Deduplication**: Up to 2,000 seen URLs tracked
- **Rolling buffer**: Max 200 headlines kept in memory

#### 3. ThreatFeedService (Broadcast Loop)

- **Interval**: Every 8–12 seconds per event
- **On connect**: Sends initial state with 20 recent vectors + 10 recent news headlines + city data
- **Subscriber model**: Each WebSocket connection gets a dedicated `asyncio.Queue`

### Data Transparency

| Data Point | Real? | Source |
|-----------|-------|--------|
| Source IP | ✅ Real | ThreatFox, Feodo, IPsum feeds |
| Geo-location | ✅ Real | ip-api.com |
| Attack Type | ✅ Real | Feed metadata keywords |
| Malware Family | ✅ Real | Feodo (Dridex, Emotet, QakBot) / ThreatFox |
| Severity | ✅ Real | IPsum blacklist score / source credibility |
| Target City | ⚠️ Statistical | NCRB 2022 crime-weighted distribution |

<br/>

---

## 👁️ Watch Monitoring

Create watches to automatically re-scan targets at configurable intervals and get alerts when data changes.

### Key Features

- **Configurable Intervals**: 5 minutes to 7 days
- **Plugin Selection**: Choose exactly which plugins run per watch
- **Smart Change Detection**: Compares `gui_data` JSON across scans — generates human-readable diffs
- **Alert History**: Full timeline of changes per watch target
- **Pause/Resume**: Toggle watches on/off without deleting them

### Retry Logic

On SQLite lock contention, watch tasks retry up to 3 times with exponential backoff (1s, 2s, 4s).

<br/>

---

## 🤖 AI Chatbot Assistant

A floating in-app assistant (powered by Google Gemini) that acts as a SOC-analyst helper — it explains dashboard features, answers questions about a scan in progress, and can turn live scan data into a formatted investigation report.

### How It Works

1. Click the chat bubble in the bottom-right corner to open the assistant
2. While a scan is active, the current target's findings are automatically passed to the assistant as context
3. Ask questions directly, or click **Generate Report** to produce a structured SOC report (Target Overview, Key Findings, Risk Assessment, Recommended Actions)
4. Any report-length reply shows a **Download as Word (.docx)** button underneath it

### Word (.docx) Report Export

Report replies aren't limited to the chat window — they can be exported as a polished, ready-to-share Word document:

- Markdown from the chatbot (headings, bullets, nested lists, tables, bold, inline code) is converted into real Word formatting — not just plain text
- Each export includes a cover page with the TRINETRA title, target, report date, and a classification-style footer
- The generated `.docx` is suitable to send directly to a SOC analyst, client, or third party
- Powered by `python-docx` on the backend (`POST /api/report/docx`) — no server-side dependency on Microsoft Word

<br/>

---

## 🗺️ Interactive Map

### Map Architecture

```
IndiaMap (React Component)
├── MapContainer (Leaflet)
│   ├── TileLayer (CartoDB dark basemap)
│   ├── MapController (programmatic center/zoom)
│   ├── AnimatedAttackOverlay (SVG lines + traveling dots)
│   ├── CrimeHeatmap (GeoJSON state boundaries + NCRB)
│   ├── CityMarkers (10 major Indian cities, NCRB-risk)
│   └── DestinationPins (aggregated attack targets)
├── AttackCounter (live badge: critical/medium count)
├── AttackInfoPanel (severity bars, origin intel, table)
├── VectorDetailModal (full IP intel + report actions)
├── DataSourcesPanel (feed health status)
├── Map Controls (show/hide attacks, crime, data sources)
└── Legend (threat levels, data source colors)
```

### Animation System

Attack vectors are rendered as an **SVG overlay** using Leaflet's `L.svgOverlay`:

- **Dashed lines** from origin country coordinates to Indian city coordinates
- **Traveling dots** moving along the line with easing
- **Glow filter** for visual emphasis
- **10 FPS throttle** to optimize performance
- **Pauses animation when tab is hidden** (visibility API)
- **Shallow comparison** on vector IDs to avoid unnecessary rebuilds

### City Risk Markers

10 major Indian cities plotted with NCRB 2022 cyber crime statistics:
- **Color-coded circles**: Safe (green), Medium (yellow), Critical (red)
- **Pulsing animation** for critical destinations
- **Radius proportional** to risk level (7/10/14px)

<br/>

---

## 🔐 Authentication & User System

TRINETRA uses a **username/password registration system** with session tokens, backed by a dedicated React sign-up/login UI (`frontend/src/components/LoginPage/LoginPage.tsx`) with real-time field validation and animated transitions between Sign In and Register.

### How It Works

1. **First visit** — Login page appears with **Sign In** and **Register** tabs
2. **Register** — Create an account with username, email, and password
3. **First user becomes admin** — Subsequent users get the "user" role
4. **Auto-login** — After registration, you're automatically logged in
5. **Session tokens** — Stored in `localStorage`, verified on page reload
6. **Token expiry** — Tokens are valid until server restart or logout

### Auth Database

User accounts are stored in a **dedicated SQLite file** (`trinetra_auth.db`) that is independent of the main database connection. This means:

- In **Docker mode** (PostgreSQL): auth still uses SQLite — no extra setup needed
- In **manual mode** (SQLite): auth shares the SQLite approach
- The auth DB file is created automatically on first startup
- Set `AUTH_DB_PATH` env var to customize the location

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/auth/status` | Check if auth is enabled and registration is open |
| `POST` | `/api/auth/register` | Create a new account `{username, email, password}` |
| `POST` | `/api/auth/login` | Log in with credentials `{username, password}` |
| `POST` | `/api/auth/verify` | Check if a session token is still valid `{token}` |
| `POST` | `/api/auth/logout` | Invalidate the current session token |

### Authentication Methods

Once logged in, all API endpoints require the session token via:

```
X-API-Key: <your_session_token>
# or
Authorization: Bearer <your_session_token>
# or (WebSocket only)
?api_key=<your_session_token>  (as query parameter)
```

### Security Features

- **Password hashing** — SHA-256 with random 16-byte salt
- **Session tokens** — 32-byte cryptographically random hex strings
- **In-memory token store** — Tokens are cleared on server restart
- **Input validation** — Username regex, email format, minimum password length
- **Rate limiting** — Per-IP sliding window for all endpoints

<br/>

---

## 📡 Real Data Sources

All data in TRINETRA is **real** — no simulated or placeholder data.

### Threat Intelligence Feeds

| Source | Type | Data Provided | Key Required? |
|--------|------|---------------|---------------|
| [Abuse.ch ThreatFox](https://threatfox.abuse.ch/) | Malware IOCs | Malicious IPs, malware families, attack types | ❌ Free |
| [Feodo Tracker](https://feodotracker.abuse.ch/) | C2 Tracker | C2 server IPs, botnet malware (Dridex, Emotet, QakBot) | ❌ Free |
| [IPsum](https://github.com/stamparm/ipsum) | IP Blacklist | Blacklisted IPs with detection scores (1-7) | ❌ Free |
| [ip-api.com](https://ip-api.com/) | Geo-location | Country, city, lat/lon, ISP, org | ❌ Free |

### OSINT Plugins Data Sources

| Plugin | Source(s) | Key Required? |
|--------|-----------|---------------|
| Domain Record | WHOIS servers (direct TCP on port 43) | ❌ Free |
| Name Servers | dnspython (direct DNS resolution) | ❌ Free |
| Port Scanner | Built-in async TCP scanner (24 common ports) | ❌ Free |
| SSL Health | OpenSSL via socket (certificate chain, cipher, protocols) | ❌ Free |
| Subdomain Finder | crt.sh + HackerTarget API + DNS brute-force (185+ prefixes) | ❌ Free |
| Geo Locator | ip-api.com | ❌ Free |
| HTTP Headers | httpx (security headers analysis) | ❌ Free |
| Tech Fingerprint | httpx (server header, x-powered-by, cookie analysis) | ❌ Free |
| CVE Alerts | NVD API v2.0 | ❌ Free |
| Data Leaks | XposedOrNot + LeakCheck + LeakIX + curated breach DB | ❌ Free |
| Document Vault | httpx (12 common sensitive paths checked) | ❌ Free |
| OSINT Leak | leakosintapi.com | 🔑 API Key |
| Deep Search | Google dork query generation (manual execution) | ❌ Free |
| Live Feed | RSS (The Hacker News) via feedparser | ❌ Free |
| Surface Scan | Built-in async port scanner + risk analyzer | ❌ Free |

### RSS News Feeds

| Feed | Topic | Icon |
|------|-------|------|
| [The Hacker News](https://thehackernews.com/) | General cybersecurity | 📰 |
| [BleepingComputer](https://www.bleepingcomputer.com/) | Tech news + malware | 💻 |
| [KrebsOnSecurity](https://krebsonsecurity.com/) | In-depth security reporting | 🔒 |
| [The Record](https://therecord.media/) | Cyber crime + policy | 📝 |

### India-Specific Data

- **NCRB 2022** — Official cyber crime statistics for 23 Indian states/UTs
- **70+ curated India-specific data breaches** (Aadhaar, IRCTC, BigBasket, CoWIN, Truecaller, Jio, etc.)
- **India GeoJSON** — State boundaries for all states/UTs
- **City targeting** — 10 major Indian cities with NCRB-weighted attack distribution

<br/>

---

## ✨ Features

### 🔍 OSINT Search (15 Plugins)

| Category | Plugins | What They Find |
|----------|---------|----------------|
| **Infrastructure** | WHOIS, DNS Lookup, Port Scanner, SSL Health, Subdomain Finder, Geo Locator, HTTP Headers, Tech Fingerprint | Registrar info, A/MX/NS records, open ports, certificate validity, subdomains, geo-location, security headers, tech stack |
| **Threat Intel** | CVE Alerts, Data Leaks, Document Vault, OSINT Leak | Known vulnerabilities (NVD), breach data (LeakIX, XposedOrNot, LeakCheck), exposed documents, deep leak search |
| **Advanced** | Deep Search, Live Feed, Surface Scan | Google dork queries, risk scoring, real-time cyber news |

### 🗺️ Interactive India Threat Map

- Animated attack vectors with traveling dots from 25+ origin countries
- City risk markers based on NCRB 2022 cyber crime statistics
- Crime heatmap overlay with hover tooltips
- Threat intelligence panel with severity distribution
- Vector detail modal with AbuseIPDB, AlienVault, CERT-In report actions
- 10 FPS optimized animation (pauses when tab is hidden)

### 📡 Real-Time Threat Feed

- Live events timeline — filterable by All, Attacks, Events, or News
- Attack vector cards color-coded by severity
- Cyber news from 4 RSS feeds
- Vector detail modal with full IP intelligence

### 📊 Report & Graph Views

- **Report View** — Three modes: GUI (structured table), Terminal (raw output), Split (both)
- **Full Report** — Executive summary, threat landscape, watches & alerts, intelligence events
- **Relationship Graph** — Dynamic Cytoscape visualization with color-coded nodes
- **Export** — Save graphs to PNG, copy to clipboard, or export chatbot reports as Word (.docx)

### 🤖 AI Chatbot Assistant

- Google Gemini-powered in-app SOC analyst assistant
- Context-aware — automatically sees the current scan's findings
- One-click **Generate Report** for a structured investigation summary
- **Download as Word (.docx)** — formatted, cover-paged report ready to share

### 👁️ Watch & Monitoring

- Automated re-scanning from 5 minutes to 7 days
- Smart change detection with human-readable diffs
- Alert history with full timeline
- Plugin-level control per watch
- Pause/resume without data loss

### 🔐 User Authentication

- Dedicated React Sign Up / Login UI with real-time validation
- Username/password registration and login
- First user becomes admin
- Session tokens stored in localStorage
- All API endpoints require authentication
- Dedicated SQLite auth database (works with both SQLite and PostgreSQL modes)

### 🐳 Docker Deployment

- Fully containerized: PostgreSQL 15, Redis 7, FastAPI, React/Nginx
- Docker Compose with health checks and dependency ordering
- Dev mode with hot-reload via bind mounts
- TaskIQ worker for background watch tasks
- Non-root container security (all services run as unprivileged users)

### 🛡️ India-Specific Intelligence

- NCRB 2022 cyber crime data for 23 states/UTs
- 70+ curated India-specific data breaches
- India GeoJSON map with state boundaries
- CERT-In incident reporting

<br/>

---

## 📡 API Reference

### Authentication Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/api/auth/status` | Check auth status + registration open | ❌ Public |
| `POST` | `/api/auth/register` | Register new user `{username, email, password}` | ❌ Public |
| `POST` | `/api/auth/login` | Log in `{username, password}` → session token | ❌ Public |
| `POST` | `/api/auth/verify` | Verify session token `{token}` | ❌ Public |
| `POST` | `/api/auth/logout` | Invalidate session token | ✅ Required |

### OSINT Search Endpoints

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| `POST` | `/api/search` | Run OSINT scan on a target | 10/min |
| `GET` | `/api/search/{target}` | GET variant of search | 10/min |
| `GET` | `/api/detect?target=` | Auto-detect target type | 60/min |
| `GET` | `/api/plugins` | List all 15 OSINT plugins | 60/min |

### Chatbot & Report Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/chat` | Send a message to the AI assistant `{message, history, context}` | ✅ Required |
| `POST` | `/api/report/docx` | Convert a markdown report into a Word `.docx` file `{target, markdown}` | ✅ Required |

### Watch Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/watches` | List all watches |
| `POST` | `/api/watches` | Create a watch |
| `GET` | `/api/watches/{id}` | Get watch details |
| `DELETE` | `/api/watches/{id}` | Delete a watch |
| `POST` | `/api/watches/{id}/toggle` | Pause/resume a watch |
| `GET` | `/api/watches/alerts` | Recent alerts (configurable limit) |
| `GET` | `/api/watches/{id}/alerts` | Alerts for a specific watch |

### Data Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/api/crime-data` | NCRB 2022 cyber crime data | ❌ Public |
| `GET` | `/api/health/sources` | Data source health status | ❌ Public |
| `GET` | `/health` | Backend health + plugin counts | ❌ Public |

### WebSocket Endpoints

| Endpoint | Description |
|----------|-------------|
| `/ws/search` | Streaming OSINT search results |
| `/ws/threats` | Live threat feed for map |

### WebSocket /ws/search Protocol

```
Client → Server:  {"target": "example.com", "type": "domain"}
Server → Client:  {"type": "start", "total": N, "plugins": [...]}
Server → Client:  {"type": "result", "result": {...}, "completed": X, "total": N}  × N times
Server → Client:  {"type": "complete", "total": N, "completed": N}
```

### WebSocket /ws/threats Protocol

```
Server → Client:  {"type": "initial_state", "events": [...], "cities": [...], "timestamp": "..."}
Server → Client:  {"type": "attack_vector", "id": "...", "from": "China", ...}
Server → Client:  {"type": "news_event", "id": "...", "text": "...", ...}
Client → Server:  {"action": "pause"} | {"action": "resume"} | {"action": "stop"}
```

### API Examples

> **Note:** These examples use port **8000** (Docker mode). For manual mode, replace with port **8010**.

**Register a user:**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "email": "admin@example.com", "password": "securepass123"}'
```

**Login:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "securepass123"}'
```

**Run a search (with auth token):**
```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your_session_token>" \
  -d '{"target": "example.com"}'
```

**List plugins:**
```bash
curl -H "X-API-Key: <token>" http://localhost:8000/api/plugins
```

<br/>

---

## 🗂️ Project Structure

```
trinetra/
├── backend/
│   ├── app/
│   │   ├── api/                        # REST + WebSocket routes
│   │   │   ├── routes.py               # Auth (login/register), search, detect, plugins
│   │   │   ├── websocket_routes.py     # /ws/search streaming
│   │   │   ├── threat_routes.py        # /ws/threats live feed
│   │   │   ├── watch_routes.py         # Watch CRUD + alerts
│   │   │   ├── chat_routes.py          # AI chatbot (/api/chat)
│   │   │   ├── report_routes.py        # Word (.docx) report export (/api/report/docx)
│   │   │   └── data_routes.py          # NCRB crime data, source health
│   │   ├── core/                       # App core
│   │   │   ├── config.py               # Settings via pydantic-settings + .env
│   │   │   ├── detector.py             # Auto-detect target type
│   │   │   ├── sanitizer.py            # Input validation & sanitization
│   │   │   ├── rate_limiter.py         # In-memory sliding window rate limiter
│   │   │   └── api_key_auth.py         # User auth (register, login, tokens, dedicated SQLite DB)
│   │   ├── data/
│   │   │   └── ncrb_crime_data.py      # NCRB 2022 cyber crime statistics
│   │   ├── models/
│   │   │   └── schemas.py              # Pydantic request/response models
│   │   ├── plugins/                    # 15 OSINT plugins (auto-discovered)
│   │   │   ├── base.py                 # Abstract base class (OSINTPlugin)
│   │   │   ├── registry.py             # Auto-discovery plugin registry
│   │   │   ├── infrastructure/         # 8 plugins (domain, DNS, ports, SSL, subdomains, geo, headers, tech)
│   │   │   ├── threat/                 # 4 plugins (CVE, data leaks, document vault, OSINT leak)
│   │   │   └── advanced/               # 3 plugins (deep search, live feed, surface scan)
│   │   ├── services/
│   │   │   ├── orchestrator.py         # Plugin orchestrator (parallel execution)
│   │   │   ├── threat_feed.py          # Live threat feed broadcaster
│   │   │   ├── real_threat_service.py  # Real malicious IP fetcher (ThreatFox, Feodo, IPsum)
│   │   │   ├── real_news_service.py    # Real RSS news fetcher (4 feeds)
│   │   │   ├── watch_service.py        # Watch CRUD + alert service
│   │   │   ├── chat_service.py         # Gemini AI chatbot service
│   │   │   ├── docx_report_service.py  # Markdown → Word (.docx) report generator
│   │   │   ├── database.py             # Async SQLAlchemy (SQLite/PostgreSQL)
│   │   │   └── telegram_bot.py         # Telegram OSINT bot (optional)
│   │   ├── tasks/
│   │   │   ├── broker.py               # TaskIQ broker (Redis-backed)
│   │   │   ├── scheduler.py            # Watch scheduler
│   │   │   └── watch_tasks.py          # Watch scan + change detection
│   │   └── main.py                     # FastAPI app factory + lifespan
│   ├── tests/
│   │   ├── test_api_key_auth.py        # Auth unit tests
│   │   ├── test_data_leaks.py          # Data leak plugin tests
│   │   ├── test_watch_alerts.py        # Watch alert tests
│   │   ├── test_watch_retry.py         # Watch retry logic tests
│   │   ├── test_watch_routes.py        # Watch API route tests
│   │   └── test_watch_service.py       # Watch service tests
│   ├── Dockerfile                      # Multi-stage Python 3.11 build
│   ├── init.sql                        # PostgreSQL initial schema
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── LoginPage/              # React Sign Up / Login UI (real-time validation)
│   │   │   ├── ChatBot/                # AI chatbot assistant + Word (.docx) report export
│   │   │   ├── LandingPage/            # Pre-search landing/welcome screen
│   │   │   ├── Map/IndiaMap.tsx        # Interactive India threat map
│   │   │   ├── SearchBar/SearchBar.tsx # Auto-detect search input
│   │   │   ├── CommandPalette/         # Cmd/Ctrl+K quick command palette
│   │   │   ├── ReportView/             # Plugin detail report (GUI/Terminal/Split)
│   │   │   ├── FullReportView/         # Full system intelligence report
│   │   │   ├── LiveFeed/LiveFeed.tsx   # Real-time events page
│   │   │   ├── WatchPanel/             # Watch management
│   │   │   ├── GraphView/              # Cytoscape relationship graph
│   │   │   ├── VectorDetailModal/      # Attack vector details
│   │   │   ├── Sidebar/                # Plugin status sidebar
│   │   │   ├── DataSourcesPanel/       # Data source health
│   │   │   ├── DashboardStats/         # Stats bar
│   │   │   ├── ScanProgress/           # Scan progress indicator
│   │   │   ├── EmptyState/             # No-results placeholder
│   │   │   ├── ErrorState/             # Error placeholder
│   │   │   ├── Skeleton/               # Shimmer loading skeleton
│   │   │   ├── Icons/                  # Shared icon set
│   │   │   └── ToastNotification/      # Toast notifications
│   │   ├── store/
│   │   │   ├── AppContext.tsx           # Global app state
│   │   │   ├── AuthContext.tsx          # Auth state + login/register/logout
│   │   │   └── ThreatContext.tsx        # Live threat feed state
│   │   ├── types/index.ts               # TypeScript type definitions
│   │   ├── utils/
│   │   │   ├── api.ts                   # REST API client
│   │   │   ├── detectSearchType.ts      # Client-side type detection
│   │   │   ├── useWebSocket.ts          # WebSocket scan hook
│   │   │   ├── useThreatFeed.ts         # WebSocket threat feed hook
│   │   │   ├── wsUtils.ts              # WebSocket URL builder
│   │   │   ├── pluginMapper.ts          # API response → frontend types
│   │   │   └── indiaStatesGeoJSON.ts    # India GeoJSON boundaries
│   │   ├── App.tsx                      # Root app component
│   │   ├── main.tsx                     # React entry point
│   │   └── styles.css                   # Complete dark-themed design system
│   ├── Dockerfile                       # Multi-stage Node → Nginx build
│   ├── nginx.conf                       # Nginx reverse proxy config
│   └── package.json
├── docker-compose.yml                   # Production compose (PostgreSQL, Redis, Backend, Worker, Frontend)
├── docker-compose.override.yml          # Dev overrides (hot-reload bind mounts)
├── .env.example                         # Environment variable template
└── README.md
```

<br/>

---

## ⚙️ Configuration Reference

### Global Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `TRINETRA OSINT API` | Application display name |
| `DEBUG` | `false` | Enable debug mode |
| `DATABASE_URL` | `sqlite+aiosqlite:///./trinetra.db` | Database connection |
| `AUTH_DB_PATH` | `trinetra_auth.db` | Path to dedicated SQLite auth database (auto-created) |
| `CORS_ORIGINS` | `["http://localhost:3000","http://localhost:5173"]` | Allowed CORS origins |
| `PLUGIN_TIMEOUT` | `30` | Per-plugin timeout in seconds |
| `HIBP_API_KEY` | `""` | Have I Been Pwned API key |
| `TELEGRAM_BOT_TOKEN` | `""` | Telegram Bot token |
| `TELEGRAM_OSINT_API_URL` | `""` | OSINT Leak API base URL |
| `TELEGRAM_OSINT_API_KEY` | `""` | API key for OSINT API |
| `GEMINI_API_KEY` | `""` | Google Gemini API key (enables the AI chatbot & report generation) |
| `GEMINI_MODEL` | `gemini-flash-latest` | Gemini model used for chatbot replies |

### Database Backend Selection

| URL Pattern | Backend | Best For |
|-------------|---------|----------|
| `sqlite+aiosqlite:///./trinetra.db` | SQLite | Development, single-user |
| `postgresql+asyncpg://user:pass@host:5432/db` | PostgreSQL | Docker, production, multi-user |

> **Note:** User authentication always uses a dedicated SQLite database (`trinetra_auth.db`) regardless of the main `DATABASE_URL` setting. This means auth works seamlessly in both SQLite and PostgreSQL modes.

<br/>

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

- **Report bugs** — Open an issue with reproduction steps
- **Suggest features** — Open an issue with your idea
- **Add plugins** — New OSINT plugins welcome! See the base class in `backend/app/plugins/base.py`
- **Improve the map** — Better visualizations, new overlays, performance optimizations

### How to Add a New Plugin

1. Create a new `.py` file in the appropriate category directory under `backend/app/plugins/`
2. Subclass `OSINTPlugin` and implement the `run()` method
3. Set `plugin_id`, `name`, `category`, `description`, `input_types`
4. The plugin is **auto-discovered** — no registration needed

```python
from app.plugins.base import OSINTPlugin, PluginResult

class MyNewPlugin(OSINTPlugin):
    plugin_id = "my-plugin"
    name = "My Plugin"
    category = "threat"  # infrastructure, threat, advanced
    description = "What this plugin finds"
    input_types = ["domain", "ip"]

    async def run(self, target: str) -> PluginResult:
        # Your OSINT logic here
        return PluginResult(
            plugin_id=self.plugin_id,
            plugin_name=self.name,
            category=self.category,
            target=target,
            gui_data={"key": "value"},
            terminal_data="key: value",
        )
```

### Development Setup

```bash
# Docker (recommended)
docker compose -p indra2 up -d          # Full stack with hot-reload
docker compose -p indra2 logs -f backend  # Watch backend logs

# Manual (no Docker)
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8010
cd frontend && npm install && npx vite --host 0.0.0.0 --port 3000
```

<br/>

---

## 📄 License

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
    <a href="https://github.com/your-username/trinetra/issues">Report Bug</a> ·
    <a href="https://github.com/your-username/trinetra/issues">Request Feature</a> ·
    <a href="https://github.com/your-username/trinetra">GitHub</a>
  </p>
</div>
