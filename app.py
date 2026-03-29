"""
ComplianceRadar - Multi-Portal Business Compliance Intelligence Platform
Built with TinyFish Web Agent API for the TinyFish $2M Pre-Accelerator Hackathon

Deploys parallel TinyFish agents across Indian government portals (MCA, GST, Income Tax, EPFO, State portals)
to deliver risk-scored compliance briefs for MSMEs.
"""

import os
import json
import time
import uuid
import threading
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, Response
import requests

app = Flask(__name__)

# ---- Configuration ----
TINYFISH_API_KEY = os.environ.get("TINYFISH_API_KEY", "YOUR_API_KEY_HERE")
TINYFISH_BASE_URL = "https://agent.tinyfish.ai/v1/automation"

# ---- In-Memory Store (replace with MongoDB in production) ----
scans = {}

# ---- Indian Government Portal Definitions ----
PORTALS = {
    "mca": {
        "name": "MCA (Ministry of Corporate Affairs)",
        "url": "https://www.mca.gov.in/mcafoportal/viewCompanyMasterData.do",
        "description": "Company registration, annual filings, director KYC, charge management",
        "icon": "🏛️",
        "goal_template": """Navigate to {url}. Search for the company with CIN or name "{company_name}". 
Extract the following information and return as JSON:
{{
    "company_name": "official registered name",
    "cin": "Corporate Identity Number",
    "registration_date": "date of incorporation",
    "status": "Active/Strike Off/Dormant/Under Process of Striking Off",
    "authorized_capital": "authorized share capital",
    "paid_up_capital": "paid up capital",
    "last_agm_date": "date of last AGM",
    "last_annual_return_date": "date of last annual return filing",
    "last_balance_sheet_date": "date of last balance sheet filing", 
    "registered_address": "registered office address",
    "directors": ["list of director names"],
    "compliance_issues": ["any visible compliance flags or issues"]
}}
If the company is not found, return {{"status": "NOT_FOUND", "company_name": "{company_name}"}}"""
    },
    "gst": {
        "name": "GST Portal",
        "url": "https://services.gst.gov.in/services/searchtp",
        "description": "GST registration status, return filing compliance, tax payment status",
        "icon": "📋",
        "goal_template": """Navigate to {url}. Search for the business using GSTIN or name "{company_name}".
Extract the following information and return as JSON:
{{
    "gstin": "GST Identification Number",
    "legal_name": "legal name of business",
    "trade_name": "trade name",
    "registration_date": "date of registration",
    "status": "Active/Cancelled/Suspended/Inactive",
    "taxpayer_type": "Regular/Composition/etc",
    "state": "state of registration",
    "last_return_filed": "date and type of last return filed",
    "return_filing_status": "up to date / overdue / not filed",
    "compliance_rating": "if visible",
    "business_nature": "nature of business activities"
}}
If the business is not found, return {{"status": "NOT_FOUND", "company_name": "{company_name}"}}"""
    },
    "incometax": {
        "name": "Income Tax Portal",
        "url": "https://www.incometax.gov.in/iec/foportal/",
        "description": "PAN verification, TAN status, ITR filing status, TDS compliance",
        "icon": "💰",
        "goal_template": """Navigate to {url}. Use the "Know Your PAN" or "Verify PAN" feature. 
Search for entity "{company_name}" or use PAN "{pan_number}" if provided.
Extract the following information and return as JSON:
{{
    "pan": "PAN number",
    "name": "name as per PAN records",
    "status": "Active/Inactive/Deactivated",
    "pan_type": "Company/Individual/Firm/Trust",
    "last_itr_filed": "assessment year of last ITR filed if visible",
    "aadhaar_linked": "Yes/No/Not Applicable",
    "tan_number": "TAN if visible",
    "jurisdiction": "assessing officer jurisdiction"
}}
If the entity is not found, return {{"status": "NOT_FOUND", "company_name": "{company_name}"}}"""
    },
    "epfo": {
        "name": "EPFO Portal", 
        "url": "https://unifiedportal-epfo.epfindia.gov.in/publicPortal/no-auth/mis498/702",
        "description": "Provident fund compliance, establishment search, EPF/EPS contribution status",
        "icon": "👥",
        "goal_template": """Navigate to {url}. Search for establishment/company "{company_name}" in the establishment search.
Extract the following information and return as JSON:
{{
    "establishment_name": "registered name",
    "establishment_code": "EPFO establishment code",
    "status": "Active/Inactive/Surrendered",
    "state": "state",
    "district": "district",
    "total_employees": "number of employees if visible",
    "last_contribution_date": "date of last PF contribution",
    "compliance_status": "compliant/non-compliant/defaulter",
    "coverage_date": "date of EPF coverage"
}}
If the establishment is not found, return {{"status": "NOT_FOUND", "company_name": "{company_name}"}}"""
    },
    "shops": {
        "name": "Shops & Establishments",
        "url": "https://labour.gov.in/",
        "description": "Shop registration, labour law compliance, state-specific registrations",
        "icon": "🏪",
        "goal_template": """Navigate to {url} or search Google for "{company_name} shops and establishments registration {state}".
Try to find information about the company's labour law compliance and shop registration.
Extract the following information and return as JSON:
{{
    "registration_number": "S&E registration number if found",
    "company_name": "{company_name}",
    "state": "{state}",
    "registration_status": "Registered/Not Found/Expired",
    "validity": "validity date if found",
    "employees_declared": "number of employees declared",
    "last_renewal": "last renewal date",
    "compliance_notes": "any notes about compliance status"
}}
If no information is found, return {{"status": "NOT_FOUND", "company_name": "{company_name}", "state": "{state}"}}"""
    }
}


def calculate_risk_score(portal_key, result):
    """Calculate risk score for a single portal result"""
    if not result or result.get("status") == "NOT_FOUND":
        return {
            "score": "red",
            "score_value": 0,
            "label": "Not Found — Gap Detected",
            "detail": f"No registration found on {PORTALS[portal_key]['name']}. This may indicate a compliance gap.",
            "action": "Verify if registration is required. If yes, initiate registration immediately."
        }
    
    status = str(result.get("status", "")).lower()
    
    # Red conditions
    if any(word in status for word in ["cancelled", "struck", "strike", "inactive", "suspended", "dormant", "defaulter", "non-compliant", "deactivated"]):
        return {
            "score": "red",
            "score_value": 20,
            "label": f"Critical — Status: {result.get('status', 'Unknown')}",
            "detail": f"Entity status on {PORTALS[portal_key]['name']} is concerning and requires immediate attention.",
            "action": "Consult a CA/CS immediately. This status may affect business operations."
        }
    
    # Check for overdue filings
    last_filed = result.get("last_annual_return_date") or result.get("last_return_filed") or result.get("last_contribution_date") or result.get("last_itr_filed")
    
    if last_filed:
        # Try to detect if filing is overdue (simple heuristic)
        try:
            if "2023" in str(last_filed) or "2022" in str(last_filed) or "2021" in str(last_filed):
                return {
                    "score": "yellow",
                    "score_value": 50,
                    "label": f"Warning — Last filing appears overdue",
                    "detail": f"Last filing on {PORTALS[portal_key]['name']} was: {last_filed}. This may be overdue.",
                    "action": "Check filing deadlines and submit pending returns."
                }
        except:
            pass
    
    # Check for return filing issues on GST
    filing_status = str(result.get("return_filing_status", "")).lower()
    if "overdue" in filing_status or "not filed" in filing_status:
        return {
            "score": "red",
            "score_value": 25,
            "label": "Critical — Returns Overdue",
            "detail": f"Return filing on {PORTALS[portal_key]['name']} is overdue.",
            "action": "File pending returns immediately to avoid penalties."
        }
    
    # Green — everything looks good
    if "active" in status or status == "":
        return {
            "score": "green",
            "score_value": 90,
            "label": f"Compliant — Status: {result.get('status', 'Active')}",
            "detail": f"Entity appears compliant on {PORTALS[portal_key]['name']}.",
            "action": "No immediate action required. Continue regular filings."
        }
    
    # Default yellow
    return {
        "score": "yellow",
        "score_value": 60,
        "label": f"Review Needed — Status: {result.get('status', 'Unknown')}",
        "detail": f"Status on {PORTALS[portal_key]['name']} needs review.",
        "action": "Review the details and verify compliance status."
    }


def calculate_overall_score(portal_results):
    """Calculate overall compliance score from all portal results"""
    scores = []
    for portal_key, data in portal_results.items():
        if "risk" in data:
            scores.append(data["risk"]["score_value"])
    
    if not scores:
        return 0
    return round(sum(scores) / len(scores))


def run_tinyfish_agent(portal_key, company_name, pan_number="", state="", scan_id=""):
    """Run a single TinyFish agent for a specific portal"""
    portal = PORTALS[portal_key]
    
    goal = portal["goal_template"].format(
        url=portal["url"],
        company_name=company_name,
        pan_number=pan_number,
        state=state
    )
    
    # Update scan status
    if scan_id in scans:
        scans[scan_id]["portals"][portal_key]["status"] = "running"
        scans[scan_id]["portals"][portal_key]["started_at"] = datetime.now().isoformat()
    
    try:
        print(f"\n[AGENT {portal_key.upper()}] Starting TinyFish agent for {company_name}")
        print(f"[AGENT {portal_key.upper()}] URL: {portal['url']}")
        print(f"[AGENT {portal_key.upper()}] API Key set: {'Yes' if TINYFISH_API_KEY and TINYFISH_API_KEY != 'YOUR_API_KEY_HERE' else 'NO - SET YOUR API KEY!'}")
        
        # Call TinyFish SSE endpoint
        response = requests.post(
            f"{TINYFISH_BASE_URL}/run-sse",
            headers={
                "X-API-Key": TINYFISH_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "url": portal["url"],
                "goal": goal,
                "browser_profile": "stealth",
                "proxy_config": {
                    "enabled": False,
                }
            },
            stream=True,
            timeout=300
        )
        
        print(f"[AGENT {portal_key.upper()}] Response status: {response.status_code}")
        
        if response.status_code != 200:
            error_text = response.text[:500]
            print(f"[AGENT {portal_key.upper()}] ERROR: {error_text}")
            result = {"status": "API_ERROR", "error": f"TinyFish returned {response.status_code}: {error_text}"}
            
            if scan_id in scans:
                scans[scan_id]["portals"][portal_key].update({
                    "status": "failed",
                    "result": result,
                    "risk": {
                        "score": "yellow",
                        "score_value": 50,
                        "label": f"Error — API returned {response.status_code}",
                        "detail": f"TinyFish agent could not process request. Check API key and credits.",
                        "action": "Verify TinyFish API key is valid and you have sufficient credits."
                    },
                    "completed_at": datetime.now().isoformat()
                })
            return result
        
        result = None
        streaming_url = None
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode("utf-8")
                if line_str.startswith("data: "):
                    try:
                        event_data = json.loads(line_str[6:])
                        event_type = event_data.get("type", "")
                        
                        print(f"[AGENT {portal_key.upper()}] Event: {event_type}")
                        
                        # Store streaming URL for live preview
                        if event_type == "STREAMING_URL" and scan_id in scans:
                            streaming_url = event_data.get("streaming_url")
                            scans[scan_id]["portals"][portal_key]["streaming_url"] = streaming_url
                            print(f"[AGENT {portal_key.upper()}] Live preview: {streaming_url}")
                        
                        # Store progress events
                        if event_type == "PROGRESS" and scan_id in scans:
                            purpose = event_data.get("purpose", "Processing...")
                            scans[scan_id]["portals"][portal_key]["progress"] = purpose
                            print(f"[AGENT {portal_key.upper()}] Progress: {purpose}")
                        
                        # Capture completed result
                        if event_type == "COMPLETE":
                            if event_data.get("status") == "COMPLETED":
                                result = event_data.get("result", {})
                                print(f"[AGENT {portal_key.upper()}] ✅ COMPLETED with result")
                            else:
                                error_msg = event_data.get("error", {}).get("message", "Unknown error")
                                result = {"status": "FAILED", "error": error_msg}
                                print(f"[AGENT {portal_key.upper()}] ❌ FAILED: {error_msg}")
                    
                    except json.JSONDecodeError:
                        continue
        
        if result is None:
            print(f"[AGENT {portal_key.upper()}] ⏰ TIMEOUT - no result received")
            result = {"status": "TIMEOUT", "error": "Agent did not return results in time"}
        
        # Calculate risk score
        risk = calculate_risk_score(portal_key, result)
        
        # Update scan with results
        if scan_id in scans:
            scans[scan_id]["portals"][portal_key].update({
                "status": "completed",
                "result": result,
                "risk": risk,
                "completed_at": datetime.now().isoformat()
            })
            
            # Check if all portals are done
            all_done = all(
                p.get("status") in ["completed", "failed"] 
                for p in scans[scan_id]["portals"].values()
            )
            if all_done:
                scans[scan_id]["status"] = "completed"
                scans[scan_id]["overall_score"] = calculate_overall_score(scans[scan_id]["portals"])
                scans[scan_id]["completed_at"] = datetime.now().isoformat()
        
        return result
    
    except Exception as e:
        error_result = {"status": "ERROR", "error": str(e)}
        if scan_id in scans:
            scans[scan_id]["portals"][portal_key].update({
                "status": "failed",
                "result": error_result,
                "risk": {
                    "score": "yellow",
                    "score_value": 50,
                    "label": "Error — Could not reach portal",
                    "detail": f"Agent encountered an error: {str(e)}",
                    "action": "Retry the scan or check the portal manually."
                },
                "completed_at": datetime.now().isoformat()
            })
        return error_result


# ---- Flask Routes ----

@app.route("/favicon.ico")
def favicon():
    return "", 204

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/scan", methods=["POST"])
def start_scan():
    """Start a compliance scan"""
    data = request.json
    company_name = data.get("company_name", "").strip()
    pan_number = data.get("pan_number", "").strip()
    gstin = data.get("gstin", "").strip()
    state = data.get("state", "").strip()
    selected_portals = data.get("portals", list(PORTALS.keys()))
    
    if not company_name:
        return jsonify({"error": "Company name is required"}), 400
    
    # Create scan record
    scan_id = str(uuid.uuid4())[:8]
    scans[scan_id] = {
        "id": scan_id,
        "company_name": company_name,
        "pan_number": pan_number,
        "gstin": gstin,
        "state": state,
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "overall_score": None,
        "portals": {}
    }
    
    # Initialize portal entries
    for portal_key in selected_portals:
        if portal_key in PORTALS:
            scans[scan_id]["portals"][portal_key] = {
                "name": PORTALS[portal_key]["name"],
                "icon": PORTALS[portal_key]["icon"],
                "status": "queued",
                "progress": "Waiting to start...",
                "streaming_url": None,
                "result": None,
                "risk": None,
                "started_at": None,
                "completed_at": None
            }
    
    # Launch agents in parallel threads
    for portal_key in selected_portals:
        if portal_key in PORTALS:
            thread = threading.Thread(
                target=run_tinyfish_agent,
                args=(portal_key, company_name, pan_number, state, scan_id)
            )
            thread.daemon = True
            thread.start()
    
    return jsonify({"scan_id": scan_id, "status": "running"})


@app.route("/api/scan/<scan_id>")
def get_scan(scan_id):
    """Get scan status and results"""
    if scan_id not in scans:
        return jsonify({"error": "Scan not found"}), 404
    return jsonify(scans[scan_id])


@app.route("/api/scan/<scan_id>/stream")
def stream_scan(scan_id):
    """SSE endpoint for real-time scan updates"""
    def generate():
        last_state = None
        timeout = time.time() + 300  # 5 minute timeout
        
        while time.time() < timeout:
            if scan_id not in scans:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Scan not found'})}\n\n"
                break
            
            current_state = json.dumps(scans[scan_id], default=str)
            
            if current_state != last_state:
                yield f"data: {current_state}\n\n"
                last_state = current_state
            
            if scans[scan_id]["status"] == "completed":
                yield f"data: {json.dumps({'type': 'complete', 'scan': scans[scan_id]}, default=str)}\n\n"
                break
            
            time.sleep(1)
    
    return Response(generate(), mimetype="text/event-stream")


@app.route("/api/portals")
def get_portals():
    """Get available portal definitions"""
    portal_list = {}
    for key, portal in PORTALS.items():
        portal_list[key] = {
            "name": portal["name"],
            "description": portal["description"],
            "icon": portal["icon"]
        }
    return jsonify(portal_list)


@app.route("/api/demo")
def demo_results():
    """Return pre-computed demo results for reliable demo recording"""
    demo_scan = {
        "id": "demo-001",
        "company_name": "Infosys Technologies Limited",
        "status": "completed",
        "started_at": datetime.now().isoformat(),
        "completed_at": datetime.now().isoformat(),
        "overall_score": 72,
        "portals": {
            "mca": {
                "name": "MCA (Ministry of Corporate Affairs)",
                "icon": "🏛️",
                "status": "completed",
                "result": {
                    "company_name": "INFOSYS LIMITED",
                    "cin": "L85110KA1981PLC013115",
                    "registration_date": "02-07-1981",
                    "status": "Active",
                    "authorized_capital": "₹2,400,00,00,000",
                    "paid_up_capital": "₹2,072,00,00,000",
                    "last_agm_date": "26-06-2025",
                    "last_annual_return_date": "26-07-2025",
                    "last_balance_sheet_date": "31-03-2025",
                    "registered_address": "Electronics City, Hosur Road, Bangalore - 560100",
                    "directors": ["Nandan M. Nilekani", "Salil Parekh", "Bobby Parikh"]
                },
                "risk": {
                    "score": "green",
                    "score_value": 95,
                    "label": "Compliant — Status: Active",
                    "detail": "Entity is active and all filings appear current on MCA portal.",
                    "action": "No immediate action required. Continue regular filings."
                }
            },
            "gst": {
                "name": "GST Portal",
                "icon": "📋",
                "status": "completed",
                "result": {
                    "gstin": "29AABCI1234A1Z5",
                    "legal_name": "INFOSYS LIMITED",
                    "trade_name": "INFOSYS",
                    "registration_date": "01-07-2017",
                    "status": "Active",
                    "taxpayer_type": "Regular",
                    "state": "Karnataka",
                    "last_return_filed": "GSTR-3B - February 2026",
                    "return_filing_status": "up to date"
                },
                "risk": {
                    "score": "green",
                    "score_value": 90,
                    "label": "Compliant — Status: Active",
                    "detail": "GST registration is active and returns are filed up to date.",
                    "action": "No immediate action required."
                }
            },
            "incometax": {
                "name": "Income Tax Portal",
                "icon": "💰",
                "status": "completed",
                "result": {
                    "pan": "AABCI1234A",
                    "name": "INFOSYS LIMITED",
                    "status": "Active",
                    "pan_type": "Company",
                    "last_itr_filed": "AY 2025-26",
                    "aadhaar_linked": "Not Applicable",
                    "jurisdiction": "CIT (LTU) Bangalore"
                },
                "risk": {
                    "score": "green",
                    "score_value": 92,
                    "label": "Compliant — Status: Active",
                    "detail": "PAN is active and ITR filing appears current.",
                    "action": "No immediate action required."
                }
            },
            "epfo": {
                "name": "EPFO Portal",
                "icon": "👥",
                "status": "completed",
                "result": {
                    "establishment_name": "INFOSYS LIMITED",
                    "establishment_code": "KN/BNG/12345",
                    "status": "Active",
                    "state": "Karnataka",
                    "district": "Bangalore Urban",
                    "last_contribution_date": "February 2026",
                    "compliance_status": "compliant"
                },
                "risk": {
                    "score": "green",
                    "score_value": 88,
                    "label": "Compliant — Status: Active",
                    "detail": "EPFO establishment is active with recent contributions.",
                    "action": "No immediate action required."
                }
            },
            "shops": {
                "name": "Shops & Establishments",
                "icon": "🏪",
                "status": "completed",
                "result": {
                    "status": "NOT_FOUND",
                    "company_name": "INFOSYS LIMITED",
                    "state": "Maharashtra"
                },
                "risk": {
                    "score": "red",
                    "score_value": 0,
                    "label": "Not Found — Gap Detected",
                    "detail": "No Shops & Establishments registration found in Maharashtra. If the company operates offices in Maharashtra, this may be a compliance gap.",
                    "action": "Verify if S&E registration is required in Maharashtra. If yes, apply for registration through the state labour department portal."
                }
            }
        }
    }
    return jsonify(demo_scan)


if __name__ == "__main__":
    # Check API key on startup
    if not TINYFISH_API_KEY or TINYFISH_API_KEY == "YOUR_API_KEY_HERE":
        print("\n" + "="*60)
        print("⚠️  WARNING: TINYFISH_API_KEY is not set!")
        print("Set it with: $env:TINYFISH_API_KEY=\"sk-tinyfish-your-key\"")
        print("Get your key at: https://agent.tinyfish.ai/api-keys")
        print("="*60)
        print("\nApp will start but scans will fail without a valid API key.")
        print("Demo mode (loadDemo) will still work.\n")
    else:
        print(f"\n✅ TinyFish API key is set (starts with {TINYFISH_API_KEY[:15]}...)")
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)