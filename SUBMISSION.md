# ComplianceRadar — HackerEarth Submission

## X Post Link
[INSERT YOUR X POST LINK HERE]

## What ComplianceRadar Does

ComplianceRadar is an AI-powered compliance intelligence platform for Indian MSMEs. It deploys parallel TinyFish web agents across 5 Indian government portals simultaneously — MCA, GST, Income Tax, EPFO, and Shops & Establishments — and delivers a risk-scored compliance brief in minutes instead of days.

63 million Indian MSMEs face compliance obligations across multiple government portals. Each portal has a different interface, different requirements, and zero APIs. Chartered Accountants charge ₹5,000-50,000/year to navigate these portals manually. Small businesses either pay up or risk penalties, strikes from registrar, or business dissolution.

ComplianceRadar solves this by sending AI agents into these portals to discover:
- Whether your company registrations are active or lapsed
- Whether your returns and filings are up to date or overdue
- Compliance gaps — portals where you should be registered but aren't
- Approaching deadlines that need immediate attention
- An overall compliance health score (0-100) with actionable recommendations

## Why This Needs TinyFish

Indian government portals (MCA, GST, Income Tax, EPFO) are the deep web — trapped behind complex JavaScript-rendered UIs, session management, CAPTCHAs, and multi-step navigation flows. No APIs exist. No scraping tool can handle them reliably.

TinyFish's web agent infrastructure is the only way to programmatically navigate these portals. Our agents:
- Navigate to each portal's search interface
- Enter company details and handle dynamic form elements
- Extract structured compliance data from result pages
- Handle edge cases like session timeouts and portal errors
- Run all 5 portals in parallel for fast results

Without TinyFish, this product literally cannot exist.

## Technical Architecture

- **Backend:** Python Flask with threaded parallel execution
- **Agent Engine:** TinyFish Web Agent API (SSE streaming endpoint)
- **Portal Coverage:** MCA (mca.gov.in), GST (gst.gov.in), Income Tax (incometax.gov.in), EPFO (epfindia.gov.in), State Labour portals
- **Risk Engine:** Rule-based scoring with status analysis, deadline detection, and gap identification
- **Frontend:** Single-page dashboard with real-time agent activity feed, risk-scored compliance cards, gap alerts, and downloadable reports
- **Configuration:** Stealth browser profile + India proxy routing for reliable portal access

## Business Case

- **Market:** 63 million Indian MSMEs, $10B+ compliance services market
- **Current Solution:** CAs charging ₹5,000-50,000/year for manual portal navigation
- **Our Pricing:** ₹499-1,499/month for continuous compliance monitoring
- **Revenue Model:** SaaS subscription for businesses + white-label for CA firms
- **Why Now:** TinyFish makes reliable government portal automation possible for the first time. Indian MSMEs are digitizing rapidly post-GST mandate.

## Demo Video
The demo shows:
1. Entering a company name and selecting 5 government portals
2. 5 TinyFish agents launching in parallel — each navigating a different government portal
3. Real-time agent activity feed showing progress on each portal
4. Risk-scored compliance cards populating with green/yellow/red status
5. Gap detection alert — identifying a portal where registration is missing
6. Overall compliance health score
7. Downloadable compliance brief

## Screenshots
[ATTACH SCREENSHOTS OF YOUR DASHBOARD HERE]

## Links
- GitHub: [INSERT REPO LINK]
- Live Demo: [INSERT IF DEPLOYED]
- X Post: [INSERT LINK]
