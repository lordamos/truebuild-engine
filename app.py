import json
import random
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func
from playwright.async_api import async_playwright

from database import engine, Base, get_db, SessionLocal
from models import CompanyDossier, Vendor, Tradeline, PaymentRecord

app = FastAPI(title="TrueBuild Autonomous Credit Engine", version="5.0.0")

# --- Database Initialization ---
@app.on_event("startup")
def startup_event():
    # Create all tables (Works on PostgreSQL and SQLite)
    Base.metadata.create_all(bind=engine)
    
    # Seed Data
    db = SessionLocal()
    try:
        # Seed Vendors if empty
        if db.query(Vendor).count() == 0:
            vendor_seeds = [
                Vendor(name="Uline", tier=1, category="Shipping Supplies", terms="Net 30", min_invoice=50.0, reports_to="Experian, D&B", pg_required=0, application_url="https://www.uline.com/CustomerService/CreditApplication", application_type="Online", underwriting_tips="Check 'Invoice My Account'"),
                Vendor(name="Grainger", tier=1, category="Industrial/MRO", terms="Net 30", min_invoice=50.0, reports_to="D&B", pg_required=0, application_url="https://www.grainger.com/content/credit-services", application_type="Online Form", underwriting_tips="Apply online; requires active LLC."),
                Vendor(name="Quill", tier=1, category="Office Supplies", terms="Net 30", min_invoice=100.0, reports_to="D&B", pg_required=0, application_url="https://www.quill.com/account/net30terms", application_type="Online Form", underwriting_tips="Place 1-2 small pre-paid orders first."),
                Vendor(name="Nav Prime", tier=1, category="Financial Monitoring", terms="Net 30", min_invoice=49.99, reports_to="D&B, Experian, Equifax", pg_required=0, application_url="https://www.nav.com", application_type="SaaS Portal", underwriting_tips="Reports monthly to all three bureaus."),
                Vendor(name="The CEO Creative", tier=1, category="Office Supplies", terms="Net 30", min_invoice=60.0, reports_to="Equifax, CreditSafe", pg_required=0, application_url="https://theceocreative.com/net-30-application/", application_type="Online", underwriting_tips="Requires min $60 purchase."),
                Vendor(name="Home Depot Pro Commercial", tier=2, category="Hardware", terms="Revolving / Net 30", min_invoice=100.0, reports_to="Experian, D&B", pg_required=0, application_url="https://www.homedepot.com/c/Credit_Center", application_type="Online", underwriting_tips="Apply under Commercial Revolving."),
                Vendor(name="WEX Fleet Fuel Card", tier=2, category="Fuel Services", terms="Net 15 / Net 30", min_invoice=75.0, reports_to="Experian, D&B", pg_required=0, application_url="https://www.wexinc.com/solutions/fleet-cards/", application_type="Online", underwriting_tips="Fleet gas cards."),
                Vendor(name="Amazon Business American Express", tier=3, category="General Purchasing", terms="Net 60 / Revolving", min_invoice=250.0, reports_to="Experian, D&B", pg_required=0, application_url="https://www.amazon.com/businesscredit", application_type="Online", underwriting_tips="Select 'Company Liability Only'."),
                Vendor(name="Chase Ink Business Preferred", tier=4, category="Commercial Bank Card", terms="Revolving", min_invoice=500.0, reports_to="Equifax, Experian", pg_required=1, application_url="https://creditcards.chase.com/business", application_type="Bank", underwriting_tips="Requires PG.")
            ]
            db.add_all(vendor_seeds)
            db.commit()

        # Seed the User's Company if empty
        if db.query(CompanyDossier).count() == 0:
            user_co = CompanyDossier(
                legal_name="Sumthin3lse Global Solutions LLC",
                dba="Sumthin3lse Global",
                state_of_inc="FL",
                date_established="2025-12-01",
                ein="12-3456789", # Mocked
                primary_phone="321-555-0000",
                primary_email="admin@sumthin3lseglobal.com",
                physical_address="2055 Warrior ave se",
                city="Palm Bay",
                state="FL",
                zip_code="32909",
                officer_name="Managing Member"
            )
            db.add(user_co)
            db.commit()
    finally:
        db.close()


# --- Pydantic Schemas ---
class TradelineLink(BaseModel):
    vendor_id: int
    account_number: str
    credit_limit: float = Field(default=500.0, gt=0)


# --- Core Scoring & Engine Logic ---
def compute_metrics(db: Session, company_id: int):
    # Fetch all payment records for this company
    records = db.query(PaymentRecord.days_relative_to_due, Vendor.reports_to)\
        .join(Tradeline, PaymentRecord.tradeline_id == Tradeline.id)\
        .join(Vendor, Tradeline.vendor_id == Vendor.id)\
        .filter(Tradeline.company_id == company_id, Tradeline.status == 'approved').all()

    if not records:
        paydex, experian, equifax = None, None, None
    else:
        dnb_scores, exp_scores, eq_scores = [], [], []
        for delta, reports_to in records:
            score = 100 if delta <= -30 else (90 if delta <= -15 else (80 if delta <= 0 else (70 if delta <= 15 else (60 if delta <= 30 else 50))))
            if "D&B" in reports_to: dnb_scores.append(score)
            if "Experian" in reports_to: exp_scores.append(score)
            if "Equifax" in reports_to: eq_scores.append(score)
            
        paydex = int(sum(dnb_scores) / len(dnb_scores)) if dnb_scores else None
        experian = int(sum(exp_scores) / len(exp_scores)) if exp_scores else None
        equifax = int(sum(eq_scores) / len(eq_scores)) if eq_scores else None

    # Tier unlocking logic
    tier_counts = db.query(Vendor.tier, func.count(func.distinct(Tradeline.id)))\
        .join(Tradeline, Tradeline.vendor_id == Vendor.id)\
        .join(PaymentRecord, PaymentRecord.tradeline_id == Tradeline.id)\
        .filter(Tradeline.company_id == company_id, Tradeline.status == 'approved')\
        .group_by(Vendor.tier).all()
        
    counts = {tier: count for tier, count in tier_counts}
    t1, t2, t3 = counts.get(1, 0), counts.get(2, 0), counts.get(3, 0)

    unlocked = 1
    eff_score = paydex or 0
    if t1 >= 5 and eff_score >= 80: unlocked = 2
    if unlocked == 2 and t2 >= 3 and eff_score >= 80: unlocked = 3
    if unlocked == 3 and t3 >= 3 and eff_score >= 80: unlocked = 4

    co = db.query(CompanyDossier).filter(CompanyDossier.id == company_id).first()
    if co and co.current_unlocked_tier != unlocked:
        co.current_unlocked_tier = unlocked
        db.commit()

    total_credit = db.query(func.sum(Tradeline.credit_limit))\
        .filter(Tradeline.company_id == company_id, Tradeline.status == 'approved').scalar() or 0.0

    return {
        "paydex": paydex, "experian": experian, "equifax": equifax,
        "unlocked_tier": unlocked, "total_credit": total_credit,
        "t1_count": t1, "t2_count": t2, "t3_count": t3
    }

def recommend_next_vendor(db: Session, company_id: int):
    metrics = compute_metrics(db, company_id)
    unlocked_tier = metrics["unlocked_tier"]

    applied_ids = {t.vendor_id for t in db.query(Tradeline.vendor_id).filter(Tradeline.company_id == company_id).all()}
    
    current_reports = db.query(Vendor.reports_to).join(Tradeline).filter(Tradeline.company_id == company_id).all()
    all_reports = " ".join([r[0] for r in current_reports])
    needs_equifax = "Equifax" not in all_reports
    needs_experian = "Experian" not in all_reports
    needs_dnb = "D&B" not in all_reports

    vendors = db.query(Vendor).filter(Vendor.tier <= unlocked_tier).all()
    candidates = []
    for v in vendors:
        if v.id in applied_ids: continue
        score = 100 - v.min_invoice
        if v.tier == unlocked_tier: score += 50
        if needs_dnb and "D&B" in v.reports_to: score += 40
        if needs_experian and "Experian" in v.reports_to: score += 35
        if needs_equifax and "Equifax" in v.reports_to: score += 30
        if v.pg_required == 0: score += 20
        
        candidates.append({
            "vendor_id": v.id, "vendor_name": v.name, "tier": v.tier, "category": v.category,
            "terms": v.terms, "min_purchase": v.min_invoice, "reports_to": v.reports_to,
            "personal_guarantee": bool(v.pg_required), "application_url": v.application_url,
            "underwriting_tips": v.underwriting_tips, "score": score
        })

    if not candidates: return None
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[0]

def generate_autofill_dossier(db: Session, company_id: int):
    co = db.query(CompanyDossier).filter(CompanyDossier.id == company_id).first()
    if not co: raise HTTPException(status_code=404, detail="Company not found.")
    return {
        "company_profile": {
            "LegalBusinessName": co.legal_name, "TradeName_DBA": co.dba or co.legal_name,
            "EntityType": co.entity_type, "StateOfIncorporation": co.state_of_inc,
            "DateEstablished": co.date_established, "FederalTaxID_EIN": co.ein,
            "DUNS_Number": co.duns_number or "Pending D&B Generation", "NAICS_Code": co.industry_naics
        },
        "contact_and_location": {
            "BusinessAddress": co.physical_address, "City": co.city,
            "State": co.state, "ZipCode": co.zip_code, "PrimaryPhone": co.primary_phone,
            "PrimaryEmail": co.primary_email
        },
        "authorized_officer": {
            "OfficerFullName": co.officer_name, "Title": co.officer_title,
            "OwnershipPercentage": f"{co.officer_ownership_pct}%", "SSN_Last4": co.officer_ssn_last4 or "N/A"
        }
    }

# --- Playwright Worker ---
async def browser_autofill_worker(company_id: int, vendor_id: int):
    db = SessionLocal()
    try:
        v = db.query(Vendor).filter(Vendor.id == vendor_id).first()
        if not v: return
        url = v.application_url
        dossier = generate_autofill_dossier(db, company_id)
    finally:
        db.close()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(url, timeout=60000)
        
        js_code = f"""
        (function() {{
            const data = {json.dumps(dossier)};
            function fillInput(keywords, value) {{
                if (!value) return;
                const inputs = document.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="button"]), textarea');
                for (let input of inputs) {{
                    const name = (input.name || '').toLowerCase();
                    const id = (input.id || '').toLowerCase();
                    const placeholder = (input.placeholder || '').toLowerCase();
                    if (keywords.some(k => name.includes(k) || id.includes(k) || placeholder.includes(k))) {{
                        if (input.dataset.autofilled) continue;
                        input.value = value;
                        input.dataset.autofilled = 'true';
                        input.style.border = '2px solid #10b981';
                        input.style.backgroundColor = '#ecfdf5';
                        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    }}
                }}
            }}
            setTimeout(() => {{
                fillInput(['company', 'business', 'legal'], data.company_profile.LegalBusinessName);
                fillInput(['ein', 'tax', 'fein', 'federal'], data.company_profile.FederalTaxID_EIN);
                fillInput(['address', 'street', 'line1'], data.contact_and_location.BusinessAddress);
                fillInput(['city'], data.contact_and_location.City);
                fillInput(['zip', 'postal'], data.contact_and_location.ZipCode);
                fillInput(['phone', 'mobile'], data.contact_and_location.PrimaryPhone);
                fillInput(['email'], data.contact_and_location.PrimaryEmail);
                fillInput(['first', 'officer', 'name', 'applicant'], data.authorized_officer.OfficerFullName);
                fillInput(['title', 'role'], data.authorized_officer.Title);
            }}, 2000);
        }})();
        """
        try:
            await page.evaluate(js_code)
        except Exception:
            pass
        try:
            await page.wait_for_event("close", timeout=0)
        except Exception:
            pass

# --- API Endpoints ---
@app.post("/api/engine/launch-autofill/{company_id}/{vendor_id}")
async def launch_autofill(company_id: int, vendor_id: int, background_tasks: BackgroundTasks):
    background_tasks.add_task(browser_autofill_worker, company_id, vendor_id)
    return {"status": "Browser Launched"}

@app.get("/api/engine/dashboard/{company_id}")
def get_dashboard(company_id: int, db: Session = Depends(get_db)):
    return {
        "metrics": compute_metrics(db, company_id),
        "target_vendor": recommend_next_vendor(db, company_id),
        "autofill_payload": generate_autofill_dossier(db, company_id)
    }

@app.get("/api/portfolio/{company_id}")
def get_portfolio(company_id: int, db: Session = Depends(get_db)):
    tradelines = db.query(Tradeline, Vendor).join(Vendor).filter(Tradeline.company_id == company_id).order_by(Vendor.tier.asc()).all()
    t_list = [{
        "id": t.id, "vendor": v.name, "tier": v.tier, "limit": t.credit_limit, 
        "opened": t.opened_date, "account": t.account_number, "reports_to": v.reports_to
    } for t, v in tradelines]

    payments = db.query(PaymentRecord, Tradeline, Vendor).join(Tradeline).join(Vendor)\
        .filter(Tradeline.company_id == company_id).order_by(PaymentRecord.paid_date.desc()).limit(10).all()
    
    p_list = [{
        "invoice": p.invoice_number, "amount": p.invoice_amount, "paid_date": p.paid_date, 
        "early_days": abs(p.days_relative_to_due) if p.days_relative_to_due < 0 else 0, "vendor": v.name
    } for p, t, v in payments]
    
    return {"tradelines": t_list, "recent_payments": p_list, "metrics": compute_metrics(db, company_id)}

@app.get("/api/vendors/matrix/{company_id}")
def get_vendor_matrix(company_id: int, db: Session = Depends(get_db)):
    metrics = compute_metrics(db, company_id)
    applied = {t.vendor_id for t in db.query(Tradeline.vendor_id).filter(Tradeline.company_id == company_id).all()}
    
    vendors = db.query(Vendor).order_by(Vendor.tier.asc(), Vendor.name.asc()).all()
    v_list = []
    for v in vendors:
        v_list.append({
            "id": v.id, "name": v.name, "tier": v.tier, "category": v.category,
            "terms": v.terms, "min_invoice": v.min_invoice, "reports_to": v.reports_to,
            "pg_required": v.pg_required, "application_url": v.application_url,
            "applied": v.id in applied, "locked": v.tier > metrics["unlocked_tier"]
        })
    return {"vendors": v_list, "unlocked_tier": metrics["unlocked_tier"]}

@app.post("/api/tradelines/link/{company_id}")
def link_tradeline(company_id: int, payload: TradelineLink, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    tl = Tradeline(company_id=company_id, vendor_id=payload.vendor_id, account_number=payload.account_number, credit_limit=payload.credit_limit, opened_date=now, status="approved")
    db.add(tl)
    db.commit()
    return {"status": "Tradeline Linked"}

@app.post("/api/engine/simulate-month/{company_id}")
def simulate_month(company_id: int, db: Session = Depends(get_db)):
    tradelines = db.query(Tradeline, Vendor).join(Vendor).filter(Tradeline.company_id == company_id).all()
    now = datetime.now(timezone.utc)
    count = 0
    
    for t, v in tradelines:
        inv_amt = round(v.min_invoice + random.uniform(10.0, 50.0), 2)
        inv_date = now - timedelta(days=random.randint(15, 30))
        due_date = inv_date + timedelta(days=30)
        paid_date = due_date - timedelta(days=random.randint(10, 20))
        delta = (paid_date - due_date).days
        
        pr = PaymentRecord(tradeline_id=t.id, invoice_number=f"INV-{random.randint(10000,99999)}", invoice_amount=inv_amt, invoice_date=inv_date.strftime("%Y-%m-%d"), due_date=due_date.strftime("%Y-%m-%d"), paid_date=paid_date.strftime("%Y-%m-%d"), days_relative_to_due=delta)
        db.add(pr)
        count += 1
    db.commit()
    return {"status": "Simulation Complete", "invoices_generated": count}

# --- Frontend ---
@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    # Identical HTML string from V4.0 (omitted inline, reads from disk if we used templating, 
    # but I'll write the raw HTML string again to keep it a single copy/paste run).
    # I'll just load the HTML I used previously by reading the old app.py and extracting the string.
    # Wait, instead of appending HTML manually again, I'll just write it.
    pass

# I will append the HTML manually to app.py





@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TrueBuild Autonomous Corporate Credit</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            .tab-btn.active { background-color: #0f172a; color: #10b981; border-left: 3px solid #10b981; }
            .view-section { display: none; }
            .view-section.active { display: block; animation: fadeIn 0.3s; }
            @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
        </style>
    </head>
    <body class="bg-slate-950 text-slate-100 min-h-screen font-sans flex">
        
        <!-- Sidebar Navigation -->
        <aside class="w-64 bg-slate-900 border-r border-slate-800 flex flex-col hidden md:flex">
            <div class="p-6 border-b border-slate-800">
                <h1 class="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                    <i class="fa-solid fa-robot text-sky-400"></i> TrueBuild V4.0
                </h1>
                <p class="text-[10px] text-slate-500 mt-1 uppercase tracking-wider">With Browser Auto-Fill</p>
            </div>
            <nav class="flex-1 p-4 space-y-2">
                <button onclick="switchTab('dashboard')" id="tab-dashboard" class="tab-btn active w-full text-left px-4 py-3 rounded-lg text-sm font-medium text-slate-400 hover:text-white transition flex items-center gap-3">
                    <i class="fa-solid fa-rocket w-4"></i> Auto-Fill Engine
                </button>
                <button onclick="switchTab('portfolio')" id="tab-portfolio" class="tab-btn w-full text-left px-4 py-3 rounded-lg text-sm font-medium text-slate-400 hover:text-white transition flex items-center gap-3">
                    <i class="fa-solid fa-wallet w-4"></i> Credit Portfolio
                </button>
                <button onclick="switchTab('matrix')" id="tab-matrix" class="tab-btn w-full text-left px-4 py-3 rounded-lg text-sm font-medium text-slate-400 hover:text-white transition flex items-center gap-3">
                    <i class="fa-solid fa-sitemap w-4"></i> Vendor Matrix
                </button>
            </nav>
            <div class="p-4 border-t border-slate-800">
                <label class="text-xs text-slate-500 block mb-1">Active Company ID</label>
                <div class="flex gap-2">
                    <input id="cid" type="number" value="1" class="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-sm text-center">
                    <button onclick="loadAllData()" class="bg-slate-800 hover:bg-slate-700 px-3 rounded text-sm"><i class="fa-solid fa-rotate"></i></button>
                </div>
            </div>
        </aside>

        <!-- Main Content -->
        <main class="flex-1 p-8 overflow-y-auto max-h-screen">
            
            <!-- Global Metrics Bar -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                <div class="bg-slate-900 border border-slate-800 rounded-xl p-4">
                    <p class="text-xs text-slate-400">D&B PAYDEX</p>
                    <h2 id="m-paydex" class="text-2xl font-bold text-emerald-400 mt-1">--</h2>
                </div>
                <div class="bg-slate-900 border border-slate-800 rounded-xl p-4">
                    <p class="text-xs text-slate-400">Experian Intelliscore</p>
                    <h2 id="m-experian" class="text-2xl font-bold text-blue-400 mt-1">--</h2>
                </div>
                <div class="bg-slate-900 border border-slate-800 rounded-xl p-4">
                    <p class="text-xs text-slate-400">Equifax Risk Score</p>
                    <h2 id="m-equifax" class="text-2xl font-bold text-red-400 mt-1">--</h2>
                </div>
                <div class="bg-slate-900 border border-emerald-900/50 rounded-xl p-4 shadow-[0_0_15px_rgba(16,185,129,0.1)]">
                    <p class="text-xs text-slate-400">Total Corporate Credit</p>
                    <h2 id="m-credit" class="text-2xl font-bold text-white mt-1">--</h2>
                </div>
            </div>

            <!-- VIEW: DASHBOARD -->
            <div id="view-dashboard" class="view-section active space-y-6">
                <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
                    <!-- Action Engine -->
                    <div class="bg-slate-900 border border-slate-800 rounded-xl p-6">
                        <div class="flex justify-between items-start mb-4">
                            <h3 class="text-lg font-bold"><i class="fa-solid fa-crosshairs text-sky-400 mr-2"></i> Next Target Application</h3>
                            <span id="target-tier" class="bg-slate-800 text-xs px-2 py-1 rounded">--</span>
                        </div>
                        <div id="target-content">
                            <h4 id="target-name" class="text-3xl font-extrabold text-white mb-2">Loading...</h4>
                            <p class="text-sm text-slate-400 mb-4" id="target-desc">--</p>
                            <div class="space-y-2 text-sm text-slate-300 bg-slate-950 p-4 rounded-lg border border-slate-800">
                                <div class="flex justify-between"><span class="text-slate-500">Reports To:</span><span id="target-reports" class="text-emerald-400">--</span></div>
                                <div class="flex justify-between"><span class="text-slate-500">Min Invoice:</span><span id="target-min">--</span></div>
                                <div class="flex justify-between"><span class="text-slate-500">PG Required:</span><span id="target-pg">--</span></div>
                            </div>
                            
                            <!-- BROWSER AUTOMATION CTA -->
                            <div class="mt-6 flex flex-col gap-3">
                                <button onclick="launchBrowserBot()" id="btn-bot" class="w-full bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 text-white shadow-lg text-center py-3 rounded-lg font-bold text-lg transition flex items-center justify-center gap-2">
                                    <i class="fa-solid fa-robot"></i> Launch Browser Auto-Fill Bot
                                </button>
                                <div class="flex gap-3">
                                    <a id="btn-apply" href="#" target="_blank" class="flex-1 bg-slate-800 hover:bg-slate-700 text-center py-2.5 rounded-lg font-medium text-sm transition">Manual Open Portal</a>
                                    <button onclick="markApplied()" class="flex-1 border border-slate-700 hover:bg-slate-800 rounded-lg font-medium text-sm transition">Mark Applied</button>
                                </div>
                            </div>
                        </div>
                    </div>
                    <!-- Autofill -->
                    <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col">
                        <div class="flex justify-between items-center mb-4">
                            <h3 class="text-lg font-bold"><i class="fa-solid fa-clipboard text-emerald-400 mr-2"></i> Dossier Payload</h3>
                            <button onclick="copyAutofill()" class="text-xs bg-emerald-600 hover:bg-emerald-500 px-3 py-1.5 rounded transition">Copy JSON</button>
                        </div>
                        <pre id="autofill-box" class="bg-slate-950 text-emerald-400 p-4 rounded-lg text-xs font-mono overflow-auto flex-1 border border-slate-800">{}</pre>
                    </div>
                </div>
            </div>

            <!-- VIEW: PORTFOLIO -->
            <div id="view-portfolio" class="view-section space-y-6">
                <div class="bg-indigo-950/30 border border-indigo-900/50 rounded-xl p-6 flex justify-between items-center">
                    <div>
                        <h3 class="text-lg font-bold text-indigo-400"><i class="fa-solid fa-clock-rotate-left mr-2"></i> Time Machine Simulator</h3>
                        <p class="text-sm text-slate-400">Generate 30 days of mock invoices & early payments to instantly build your scores.</p>
                    </div>
                    <button onclick="simulateMonth()" class="bg-indigo-600 hover:bg-indigo-500 text-white px-6 py-3 rounded-lg font-bold shadow-lg transition">Simulate 30 Days</button>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div class="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-6">
                        <h3 class="text-lg font-bold mb-4">Active Tradelines</h3>
                        <div class="overflow-x-auto">
                            <table class="w-full text-sm text-left">
                                <thead class="text-xs text-slate-500 bg-slate-950 border-b border-slate-800">
                                    <tr><th class="px-4 py-3">Vendor</th><th class="px-4 py-3">Tier</th><th class="px-4 py-3">Credit Limit</th><th class="px-4 py-3">Reports To</th></tr>
                                </thead>
                                <tbody id="tradelines-table" class="divide-y divide-slate-800/50 text-slate-300">
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <div class="bg-slate-900 border border-slate-800 rounded-xl p-6">
                        <h3 class="text-lg font-bold mb-4">Recent Payments</h3>
                        <div id="payments-list" class="space-y-3"></div>
                    </div>
                </div>
            </div>

            <!-- VIEW: MATRIX -->
            <div id="view-matrix" class="view-section">
                <div class="bg-slate-900 border border-slate-800 rounded-xl p-6">
                    <h3 class="text-lg font-bold mb-6"><i class="fa-solid fa-network-wired text-sky-400 mr-2"></i> Full Vendor Matrix & Ladder</h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" id="matrix-grid">
                        <!-- Populated by JS -->
                    </div>
                </div>
            </div>

        </main>
        
        <script>
            let autofillData = "";
            let currentTarget = null;

            function switchTab(tabId) {
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.view-section').forEach(v => v.classList.remove('active'));
                document.getElementById(`tab-${tabId}`).classList.add('active');
                document.getElementById(`view-${tabId}`).classList.add('active');
            }

            async function loadAllData() {
                const cid = document.getElementById('cid').value;
                
                const dashRes = await fetch(`/api/engine/dashboard/${cid}`);
                const dash = await dashRes.json();
                
                const m = dash.metrics;
                document.getElementById('m-paydex').innerText = m.paydex || 'N/A';
                document.getElementById('m-experian').innerText = m.experian || 'N/A';
                document.getElementById('m-equifax').innerText = m.equifax || 'N/A';
                document.getElementById('m-credit').innerText = `$${m.total_credit.toLocaleString()}`;
                
                const t = dash.target_vendor;
                currentTarget = t ? t.vendor_id : null;
                if(t) {
                    document.getElementById('target-content').style.display = 'block';
                    document.getElementById('target-name').innerText = t.vendor_name;
                    document.getElementById('target-tier').innerText = `Tier ${t.tier}`;
                    document.getElementById('target-desc').innerText = t.category;
                    document.getElementById('target-reports').innerText = t.reports_to;
                    document.getElementById('target-min').innerText = `$${t.min_purchase.toFixed(2)}`;
                    document.getElementById('target-pg').innerText = t.personal_guarantee ? 'Yes' : 'No';
                    document.getElementById('btn-apply').href = t.application_url;
                } else {
                    document.getElementById('target-content').style.display = 'none';
                    document.getElementById('target-tier').innerText = 'Max Tier Reached';
                }

                autofillData = JSON.stringify(dash.autofill_payload, null, 2);
                document.getElementById('autofill-box').innerText = autofillData;

                const portRes = await fetch(`/api/portfolio/${cid}`);
                const port = await portRes.json();
                
                const tbody = document.getElementById('tradelines-table');
                tbody.innerHTML = port.tradelines.map(tr => `
                    <tr class="hover:bg-slate-800/30">
                        <td class="px-4 py-3 font-medium text-white">${tr.vendor}</td>
                        <td class="px-4 py-3"><span class="bg-slate-800 px-2 py-0.5 rounded text-xs">Tier ${tr.tier}</span></td>
                        <td class="px-4 py-3 text-emerald-400">$${tr.limit.toLocaleString()}</td>
                        <td class="px-4 py-3 text-xs text-slate-400">${tr.reports_to}</td>
                    </tr>
                `).join('');

                const plist = document.getElementById('payments-list');
                plist.innerHTML = port.recent_payments.map(p => `
                    <div class="flex justify-between items-center p-3 bg-slate-950 rounded border border-slate-800">
                        <div>
                            <p class="text-sm font-bold text-white">${p.vendor}</p>
                            <p class="text-xs text-slate-500">${p.invoice}</p>
                        </div>
                        <div class="text-right">
                            <p class="text-sm text-emerald-400">$${p.amount.toFixed(2)}</p>
                            <p class="text-xs text-sky-400">${p.early_days} days early</p>
                        </div>
                    </div>
                `).join('');

                const mxRes = await fetch(`/api/vendors/matrix/${cid}`);
                const mx = await mxRes.json();
                
                document.getElementById('matrix-grid').innerHTML = mx.vendors.map(v => `
                    <div class="p-4 rounded-xl border ${v.applied ? 'bg-emerald-950/20 border-emerald-900/50' : (v.locked ? 'bg-slate-950 border-slate-800 opacity-60' : 'bg-slate-900 border-slate-700')} relative overflow-hidden">
                        ${v.locked ? '<div class="absolute inset-0 bg-slate-950/80 backdrop-blur-[1px] flex items-center justify-center z-10"><i class="fa-solid fa-lock text-3xl text-slate-700"></i></div>' : ''}
                        ${v.applied ? '<div class="absolute top-3 right-3 text-emerald-500"><i class="fa-solid fa-circle-check"></i></div>' : ''}
                        <span class="text-[10px] uppercase font-bold text-slate-500">Tier ${v.tier}</span>
                        <h4 class="font-bold text-white mt-1">${v.name}</h4>
                        <p class="text-xs text-slate-400 mt-1">${v.category}</p>
                        <div class="mt-4 flex flex-wrap gap-1">
                            ${v.reports_to.split(',').map(r => `<span class="px-2 py-0.5 bg-slate-800 text-[10px] rounded text-slate-300">${r.trim()}</span>`).join('')}
                        </div>
                    </div>
                `).join('');
            }

            function copyAutofill() {
                navigator.clipboard.writeText(autofillData);
                alert("Copied standardized JSON payload to clipboard!");
            }

            async function markApplied() {
                if(!currentTarget) return;
                const cid = document.getElementById('cid').value;
                await fetch(`/api/tradelines/link/${cid}`, {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ vendor_id: currentTarget, account_number: "AUTO-"+Date.now(), credit_limit: 500 })
                });
                loadAllData();
            }

            async function launchBrowserBot() {
                if(!currentTarget) return;
                const cid = document.getElementById('cid').value;
                const btn = document.getElementById('btn-bot');
                const origHtml = btn.innerHTML;
                
                btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Spawning Playwright Bot...';
                
                try {
                    const res = await fetch(`/api/engine/launch-autofill/${cid}/${currentTarget}`, {method: 'POST'});
                    const data = await res.json();
                    btn.innerHTML = '<i class="fa-solid fa-check"></i> Browser Launched!';
                    setTimeout(() => { btn.innerHTML = origHtml; }, 3000);
                } catch(e) {
                    btn.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> Error launching';
                    setTimeout(() => { btn.innerHTML = origHtml; }, 3000);
                }
            }

            async function simulateMonth() {
                const cid = document.getElementById('cid').value;
                const btn = event.target;
                btn.innerText = "Simulating...";
                await fetch(`/api/engine/simulate-month/${cid}`, {method: 'POST'});
                setTimeout(() => {
                    btn.innerText = "Simulate 30 Days";
                    loadAllData();
                }, 800);
            }

            window.onload = loadAllData;
        </script>
    </body>
    </html>
    """
