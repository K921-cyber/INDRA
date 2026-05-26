
<div align="center">
  <h1>🇮🇳 TRINETRA</h1>
  <p><strong>India's Open-Source Intelligence Platform</strong></p>
  <p>Search any domain, IP, email, or person → See an interactive India map → Get all public OSINT data instantly.</p>
  <p><em>No login. No auth. No walls. Pure open-source intelligence.</em></p>
</div>

---

## 🔍 What is TRINETRA?

TRINETRA is a **map-centric OSINT platform** built for India. Type anything — a domain, an IP address, an email, a person's name, a phone number, or even a CVE ID — and get instant access to **20 different OSINT tools** with results displayed on an interactive map of India.

**Think of it as:** Google Maps meets Shodan, meet CERT-In, all in one browser tab.

---

## ✨ Key Features

### 🗺️ Interactive India Map
The map is the **centerpiece** of the platform — not a sidebar widget. It shows:
- **Colored pins** per city (🟢 safe / 🟡 medium / 🔴 critical)
- **Live threat vectors** — animated attack arrows from origin countries
- **Hover tooltips** — news headlines + crime stats + asset counts per city
- **Crime data overlay** — per-state cyber crime statistics (NCRB data)
- **Click drill-down** — state → city → individual asset details

### 🔍 Smart Search Bar
A single search bar with **auto-detection** — type anything and the system figures out what it is:

| You Type | Auto-Detected As |
|----------|-----------------|
| `mha.gov.in` | 🌐 Domain |
| `164.100.24.1` | 📍 IP Address |
| `admin@mha.gov.in` | 📧 Email |
| `CVE-2024-6387` | 🆔 CVE ID |
| `+91-9876543210` | 📱 Phone Number |
| `John Doe` | 👤 Person Name |
| `mha_admin` | 🔤 Username |

A dropdown also lets you manually select the search type if you prefer.

### 🛠️ 20 OSINT Tools (All Public)

**Infrastructure OSINT**
| Tool | What It Does |
|------|-------------|
| 🌐 Domain Record | Full WHOIS registration data |
| 🔗 Name Servers | All DNS records (A, MX, NS, TXT, CNAME, SOA) |
| 📍 Geo Locator | IP geolocation with map pin |
| 🔌 Port Scanner | Open ports + service detection |
| 📁 Hidden Pages | Subdomain discovery + common path probe |
| 🔒 SSL Health | Certificate validity, expiry, weak algo check |
| 🌍 Reverse Trace | PTR records + hostname mapping |
| 🔌 Tech Fingerprint | Server headers, CMS, tech stack |
| 🌏 Internet Scanner | Shodan integration for exposed services |
| 🛡️ Threat Shield | VirusTotal domain/IP reputation |

**Threat OSINT**
| Tool | What It Does |
|------|-------------|
| 🚨 Data Leaks | Known breach database lookup |
| 🕸️ CVE Alerts | Vulnerability matching + CISA KEV feed |
| 📄 Document Vault | Google-indexed public document discovery |

**Person OSINT**
| Tool | What It Does |
|------|-------------|
| 👤 Email Finder | Platform registration check (Holehe) |
| 🔤 Username Tracker | 400+ site username search (Sherlock) |
| 📱 Phone Intel | Carrier, location, messaging app detection |

**Advanced OSINT**
| Tool | What It Does |
|------|-------------|
| 🔍 Deep Search | Automated Google dorking |
| 🕸️ Social Radar | Public social media footprint |
| 📊 Surface Scan | Aggregated attack surface analysis |
| 📡 Live Feed | Real-time scrolling cyber headlines |

### 📐 Layout
```
┌─────────────────────────────────────────────────────────────────┐
│  🇮🇳 TRINETRA       🔍 ▾ [Search...]      ⏱️ Live              │
├──────────────┬──────────────────────────────────┬────────────────┤
│  📋 TOOLS    │     🗺️ INDIA MAP                 │ TOOL RESULTS  │
│  Sidebar     │     (Full Height)                │ Right Panel   │
│  with all    │     Pins, vectors,               │ opens on      │
│  20 tools    │     heatmap, overlays            │ click         │
└──────────────┴──────────────────────────────────┴────────────────┘
```

**View Modes:** [GUI Mode] [Terminal Mode] [Split Mode]

---

## 🏗️ Architecture

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  React   │────▶│ FastAPI  │────▶│PostgreSQL│     │  Redis   │
│  + TS    │     │  Backend │     │   Data   │     │  Cache   │
│  Frontend│     │          │     │  Layer   │     │   + Q    │
└──────────┘     └────┬─────┘     └──────────┘     └──────────┘
                      │
              ┌───────┴────────┐
              │   Celery Tasks  │
              │  (Background)   │
              │ • CISA KEV sync │
              │ • News fetching │
              │ • WHOIS refresh │
              │ • Port scanning │
              └────────────────┘
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React + TypeScript + Tailwind CSS |
| **Map** | Leaflet.js + OpenStreetMap (free, no API key) |
| **Backend** | Python FastAPI |
| **Database** | PostgreSQL 15 |
| **Cache/Queue** | Redis 7 + Celery |
| **Terminal UI** | xterm.js |
| **Containers** | Docker Compose (6 containers) |

### Data Sources (All Free / Open-Source)

| Source | What We Get |
|--------|-------------|
| WHOIS Servers | Domain registration |
| DNS Resolution | All record types |
| crt.sh (CT Logs) | Subdomains, certificates |
| MaxMind GeoLite2 | Free IP geolocation |
| CISA KEV Catalog | Known exploited vulns |
| NVD / NIST | CVE database |
| VirusTotal | Domain/IP reputation (500/day free) |
| Shodan | Internet-facing services (100/mo free) |
| The Hacker News / CERT-In / BleepingComputer | Cyber news RSS |
| Holehe / Sherlock (Python) | Email & username OSINT |
| OpenStreetMap + Leaflet | Map tiles |
| NCRB / public data | Cyber crime statistics |

---

## 📅 Build Timeline

| Phase | Weeks | What We Build |
|-------|-------|---------------|
| **1** | Week 1 | Clean slate, new project scaffold, search bar with auto-detect |
| **2** | Week 2 | India map with pins, hover tooltips, default dashboard view |
| **3-4** | Weeks 3-4 | 8 core OSINT tools: Domain Record, Name Servers, Geo Locator, Port Scanner, Hidden Pages, SSL Health, Reverse Trace, Tech Fingerprint |
| **5** | Week 5 | Threat tools: CVE Alerts, Data Leaks, Document Vault, Internet Scanner, Threat Shield |
| **6** | Week 6 | Person OSINT: Email Finder, Username Tracker, Phone Intel, Deep Search, Social Radar |
| **7** | Week 7 | Map intelligence: live vectors, crime overlay, surface scan, click drill-down |
| **8** | Week 8 | Polish: live feed, reports, performance, mobile responsiveness |

**Total: ~8 weeks** development timeline to full platform.

---

## 🚀 Getting Started (For Devs)

```bash
# Prerequisites: Docker + Docker Compose installed

# 1. Start all containers
docker-compose up -d

# 2. Seed initial data
# (Container name TBD — will be set during Phase 1 scaffold)
docker exec -i trinetra-backend python -c "from seed_data import seed; import asyncio; asyncio.run(seed())"

# 3. Open in browser
open http://localhost
```

---

## 🎯 User Flow (From First Visit)

1. **Open the site** → clean search bar with auto-detect dropdown. Or just open without searching to see the default India map with national-level stats.
2. **Type `mha.gov.in`** → system detects "🌐 Domain", hits enter
3. **India map loads**, zoomed to Delhi — shows 12 assets, 3 threats
4. **Live vectors animate** — Pakistan → Delhi (Ransomware), China → Mumbai (Phishing)
5. **Hover Delhi** — tooltip shows news headlines + crime stats
6. **Click "Port Scanner"** in left sidebar → right panel shows open ports
7. **Alert:** Port 22 SSH → CVE-2024-6387 (regreSSHion) detected
8. **Click "CVE Alerts"** → full vulnerability analysis with patch recommendations
9. **Toggle crime overlay** on map → see Maharashtra: 1,245 cyber incidents in 2025
10. **Try other searches** → an email, a CVE ID, a person's name — all auto-detected

---

## 📁 Project Structure (Planned)

```
trinetra/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI entry point
│   │   ├── routers/           # API endpoints for each OSINT tool
│   │   ├── services/          # OSINT tool logic
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   └── tasks/             # Celery background tasks
│   ├── seed_data.py           # India-focused seed data
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.tsx            # Main app with search bar + layout
│   │   ├── pages/             # Dashboard, tool result pages
│   │   ├── components/        # Map, Sidebar, SearchBar, panels
│   │   └── services/          # API client
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 📄 Documents

| File | Description |
|------|-------------|
| [`TRINETRA_OSINT_PLATFORM.md`](./TRINETRA_OSINT_PLATFORM.md) | Full detailed plan with all 20 tools, map features, and phases |
| [`README.md`](./README.md) | This file — team overview |

---

---

## 📝 License

MIT — Open-source and free to use.

---

<div align="center">
  <p><strong>🇮🇳 TRINETRA — Open-Source Intelligence for India</strong></p>
  <p><em>Built with Python, React, and open data.</em></p>
</div>
