<div align="center">
  <br/>
  <img src="https://img.shields.io/badge/version-1.0.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/OSINT-Platform-purple.svg" alt="OSINT">
  <br/><br/>
</div>

# 🛡️ TRINETRA — OSINT Intelligence Dashboard

> **An all-in-one Open Source Intelligence (OSINT) Dashboard built for India.**  
> Search any domain, IP, email, phone number, or name — get comprehensive threat intelligence in seconds.

---

## 📋 Table of Contents

- [How It Works](#-how-it-works)
- [How It Helps](#-how-it-helps)
- [Features](#-features)
- [Setup Guide](#-setup-guide)
- [Usage Guide](#-usage-guide)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [API Endpoints](#-api-endpoints)
- [Project Structure](#-project-structure)
- [Running Tests](#-running-tests)

---

## ⚙️ How It Works

TRINETRA operates as a **unified OSINT intelligence platform** with three independent but complementary systems running simultaneously:

### 1. 🔍 On-Demand OSINT Search

When you search a target (domain, IP, email, phone, or name):

```
User Query ──→ Auto-Detect Type ──→ 19 Parallel Plugins ──→ Results Stream Back
                      │                      │
                 domain / IP /          Infrastructure   (9 plugins)
                 email / phone         Threat Intel      (3 plugins)
                 / name                Person Recon      (3 plugins)
                                        Advanced Scan     (4 plugins)
```

- **Auto-detection** identifies the target type instantly
- **All matching plugins run in parallel** (asyncio.gather) — results in 5–18 seconds
- **Real-time streaming** via WebSocket shows each result as it completes
- **19 specialized OSINT plugins** each query live, free data sources (WHOIS, DNS, NVD, crt.sh, Have I Been Pwned, etc.)

### 2. 📡 Live Threat Feed (Continuous Background Loop)

Independent of user searches, a background system runs every 10 minutes:

```
ThreatFox ──┐
Feodo     ──┼──→ Fetch malicious IPs ──→ Geo-locate (ip-api.com) ──→ Build Attack Vectors
IPsum    ───┘                                                     │
                                                                   ▼
RSS News ──→ The Hacker News, BleepingComputer, Krebs, Record ──→ Broadcast via WebSocket
                                                                   │
                                                                   ▼
                                                    India Map updates every 8-12 seconds
```

- **Real IPs** from Abuse.ch ThreatFox, Feodo Tracker, and IPsum blacklists
- **Real geo-location** via ip-api.com (free tier)
- **Attack types and malware names** from actual feed metadata
- **Target cities** are statistically assigned based on NCRB crime data (we know the attack source, not the real destination)

### 3. 👁️ Watch & Monitoring (Periodic Background Checks)

```
Scheduler (every 60s) ──→ Check due watches ──→ Run plugins ──→ Compare with previous scan
                                                                       │
                                                                  Changes detected?
                                                                  ├── Yes → Create Alert
                                                                  └── No  → Skip
```

- Configure targets to be re-scanned at intervals from 5 minutes to 7 days
- Automatic change detection creates alerts when results differ
- Alerts are stored and viewable in the dashboard

---

## 🎯 How It Helps

### The Problem It Solves

Investigating a single domain traditionally requires switching between **9+ different tools**:

1. WHOIS lookup site → registrar info
2. DNS checker → A, MX, NS records
3. nmap → port scan
4. SSL checker → certificate validity
5. crt.sh → subdomains
6. Have I Been Pwned → data leaks
7. NVD → CVEs
8. The Hacker News → recent threats
9. ip-api.com → server location

**That's 15–30 minutes of manual work.** TRINETRA does it all in **one search — 10–15 seconds.**

### Who It Helps

| User | Benefit |
|------|---------|
| **Security Researchers** | Rapid threat intelligence gathering — investigate domains, IPs, emails in seconds instead of minutes |
| **CERT / SOC Teams** | Continuous monitoring of critical infrastructure via Watch system with change alerts |
| **Threat Intel Analysts** | Live threat feed showing real malicious IPs targeting India with origin intelligence |
| **Penetration Testers** | Automated recon — subdomains, ports, tech fingerprint, SSL health in one place |
| **Cybersecurity Students** | Learn OSINT techniques with real data and an interactive India-focused map |

### Key Differentiators

| Problem | TRINETRA's Solution |
|---------|-------------------|
| Global OSINT tools ignore India-specific data | Built-in NCRB 2022 cyber crime data + 70+ curated India-specific breaches (Aadhaar, IRCTC, CoWIN, etc.) |
| No unified dashboard — 19 separate tools is slow | One search triggers all 19 plugins in parallel — results stream in real-time |
| Simulated/placeholder data when APIs fail | Every plugin returns real data from live sources (WHOIS, DNS, NVD, threat feeds) |
| Global maps miss India context | India-focused map with state crime overlay, city risk markers, animated attack vectors |
| Manual re-checking wastes hours | Watch system auto-re-scans targets at configurable intervals and alerts on changes |

---

## ✨ Features

### 🔍 OSINT Search (19 Plugins)
- **One-click intelligence** — Search any domain, IP, email, phone, or name
- **Parallel execution** — All relevant plugins run simultaneously
- **Real-time streaming** — Results appear as each plugin completes
- **Auto-detect** — Automatically identifies the target type

### 🗺️ Interactive India Map
- **Animated attack vectors** — Lines showing real threats from 25+ countries targeting Indian cities
- **City risk markers** — Color-coded circles based on NCRB crime statistics
- **Crime heatmap overlay** — Toggleable state-wise NCRB 2022 cyber crime data
- **Origin intelligence** — Live summary of attacking countries and attack types
- **Threat Intelligence panel** — Severity distribution, origin breakdown, and detailed attack routes table
- **Live attack counter** — Real-time "LIVE" badge with critical/medium breakdown

### 📊 Professional Report View
- **GUI / Terminal / Split views** — Three viewing modes for plugin findings
- **Export options** — Copy to clipboard, download as .txt, print as PDF
- **Search within results** — Filter findings in real-time

### 🧠 Relationship Graph
- **Dynamic Cytoscape visualization** — Auto-generated graph connecting search results
- **Color-coded nodes** — Infrastructure, Threat, Person, Advanced categories
- **Export to PNG** — Save graphs for reports

### 👁️ Watch & Monitoring
- **Automated re-scanning** — Monitor targets at configurable intervals (5 min to 7 days)
- **Change detection** — Automatically alerts on differences
- **Alert history** — Review all past changes with summaries
- **Plugin selection** — Choose which plugins run for each watch

### 📡 Live Threat Feed
- **Real-time events** — Attack vectors and news stream via WebSocket
- **Cyber news** — Latest headlines from The Hacker News, BleepingComputer, KrebsOnSecurity, The Record
- **Filterable timeline** — Filter by Attacks, Events, or News
- **Expandable details** — Click any attack for full intelligence with report actions

### 🛡️ Data Sources Health Panel
- **Live status** — Health of ThreatFox, Feodo, IPsum, ip-api.com, RSS feeds
- **Metrics** — IP counts, geo-lookups, last fetch times
- **Error reporting** — See exactly which source is failing and why

---

## 🚀 Setup Guide

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/Mac) or Docker Engine (Linux)
- [Git](https://git-scm.com/)

### Quick Setup (2 Minutes)

```bash
# 1. Clone the repository
git clone https://github.com/K921-cyber/trinetra.git
cd trinetra

# 2. Configure environment
cp .env.example .env
# Edit .env
