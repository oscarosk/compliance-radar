# ComplianceRadar 🔍

**Multi-Portal Indian MSME Compliance Intelligence Platform**

Built for the TinyFish $2M Pre-Accelerator Hackathon.

## What It Does

ComplianceRadar deploys parallel TinyFish web agents across 5 Indian government portals to deliver a risk-scored compliance brief for any business — in minutes, not days.

### Portals Scanned
- 🏛️ **MCA** — Company registration, annual filings, director KYC
- 📋 **GST Portal** — GST return filing status, compliance
- 💰 **Income Tax** — PAN verification, ITR filing status
- 👥 **EPFO** — Provident fund compliance, establishment status
- 🏪 **Shops & Establishments** — State labour law compliance

### Features
- ⚡ 5 parallel TinyFish agents scanning simultaneously
- 🔴🟡🟢 Risk-scored compliance cards per portal
- 🕳️ Gap detection — finds missing registrations
- 📊 Overall compliance health score (0-100)
- 📋 Live agent activity feed with real-time progress
- 📄 Downloadable compliance brief
- 🎯 Actionable recommendations per portal

## Quick Start

### 1. Clone and install
```bash
git clone https://github.com/YOUR_USERNAME/compliance-radar.git
cd compliance-radar
pip install -r requirements.txt
```

### 2. Set your TinyFish API key
```bash
export TINYFISH_API_KEY=sk-tinyfish-your-key-here
```

### 3. Run
```bash
python app.py
```

Open http://localhost:5000

### 4. Demo Mode
To see pre-computed results without using API credits, open browser console and run:
```javascript
loadDemo()
```

## Architecture

```
User Input (Company Name, PAN, GSTIN, State)
    │
    ▼
Flask Backend (app.py)
    │
    ├── Agent 1 → MCA Portal (mca.gov.in)
    ├── Agent 2 → GST Portal (gst.gov.in)
    ├── Agent 3 → Income Tax (incometax.gov.in)
    ├── Agent 4 → EPFO (epfindia.gov.in)
    └── Agent 5 → Shops & Establishments (state portal)
    │
    ▼ (parallel execution via TinyFish SSE API)
    │
Risk Scoring Engine
    │
    ▼
Compliance Dashboard (real-time updates via polling)
    │
    ▼
Downloadable Compliance Brief
```

## Tech Stack
- **Backend:** Python Flask + TinyFish Web Agent API
- **Frontend:** Vanilla HTML/CSS/JS (single-page app)
- **Agent Execution:** TinyFish SSE streaming with parallel threads
- **Risk Engine:** Rule-based scoring with gap detection

## The Problem

63 million Indian MSMEs face compliance obligations across multiple government portals — MCA, GST, Income Tax, EPFO, and state-level registrations. Each portal has a different interface, different requirements, and zero APIs.

Chartered Accountants charge ₹5,000-50,000/year to navigate these portals manually. Small businesses either pay up or risk penalties, strikes from registrar, or business dissolution.

## The Solution

ComplianceRadar replaces hours of manual government portal navigation with parallel AI agents. Enter your company name once — get a complete compliance picture across all portals in minutes.

## Why TinyFish

Indian government portals are the deep web — behind complex UIs, JavaScript rendering, CAPTCHAs, and session management. No APIs exist. Browser automation via TinyFish is the only way to access this data programmatically.

## Built by

Oscar — CS graduate, solo developer, hackathon builder.

For the TinyFish $2M Pre-Accelerator Hackathon.

#TinyFishAccelerator #BuildInPublic
