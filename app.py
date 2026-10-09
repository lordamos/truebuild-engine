import sqlite3
import random
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

DB_NAME = "truebuild_advanced.db"

app = FastAPI(title="TrueBuild Autonomous Credit Engine", version="3.0.0")

# --- Database Schema & Enhanced Vendor Matrix ---
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS company_dossier (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            legal_name TEXT NOT NULL,
            dba TEXT,
            entity_type TEXT DEFAULT 'LLC',
            state_of_inc TEXT NOT NULL,
            date_established TEXT NOT NULL,
            ein TEXT NOT NULL UNIQUE,
            duns_number TEXT,
            industry_naics TEXT,
            primary_phone TEXT NOT NULL,
            primary_email TEXT NOT NULL,
            website TEXT,
            physical_address TEXT NOT NULL,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            zip_code TEXT NOT NULL,
            officer_name TEXT NOT NULL,
            officer_title TEXT NOT NULL,
            officer_ssn_last4 TEXT,
            officer_ownership_pct REAL DEFAULT 100.0,
            bank_name TEXT,
            bank_account_type TEXT,
            compliance_score INTEGER DEFAULT 0,
            current_unlocked_tier INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            tier INTEGER NOT NULL,
            category TEXT NOT NULL,
            terms TEXT NOT NULL,
            min_invoice REAL NOT NULL,
            reports_to TEXT NOT NULL,
            pg_required INTEGER DEFAULT 0,
            application_url TEXT NOT NULL,
            application_type TEXT DEFAULT 'Online Form',
            underwriting_tips TEXT
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tradelines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL,
            vendor_id INTEGER NOT NULL,
            account_number TEXT,
            status TEXT CHECK(status IN ('pending', 'approved', 'declined', 'closed')) DEFAULT 'pending',
            credit_limit REAL DEFAULT 0.0,
            opened_date TEXT,
            FOREIGN KEY (company_id) REFERENCES company_dossier(id) ON DELETE CASCADE,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS payment_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tradeline_id INTEGER NOT NULL,
            invoice_number TEXT NOT NULL,
            invoice_amount REAL NOT NULL,
            invoice_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            paid_date TEXT NOT NULL,
            days_relative_to_due INTEGER NOT NULL,
            FOREIGN KEY (tradeline_id) REFERENCES tradelines(id) ON DELETE CASCADE
        );
        """)

        cursor.execute("SELECT COUNT(*) FROM vendors;")
        if cursor.fetchone()[0] == 0:
            vendor_seeds = [
                ("Uline", 1, "Shipping Supplies", "Net 30", 50.00, "Experian, D&B", 0, "https://www.uline.com/CustomerService/CreditApplication", "Online/Checkout", "Check 'Invoice My Account' at checkout or apply online."),
                ("Grainger", 1, "Industrial/MRO", "Net 30", 50.00, "D&B", 0, "https://www.grainger.com/content/credit-services", "Online Form", "Call or apply online; requires active state LLC registration."),
                ("Quill", 1, "Office Supplies", "Net 30", 100.00, "D&B", 0, "https://www.quill.com/account/net30terms", "Online Form", "Place 1-2 small pre-paid orders before Net-30 activates automatically."),
                ("Nav Prime", 1, "Financial Monitoring", "Net 30", 49.99, "D&B, Experian, Equifax", 0, "https://www.nav.com", "SaaS Portal", "Reports a monthly tradeline to all three major commercial bureaus."),
                ("The CEO Creative", 1, "Office & Tech Supplies", "Net 30", 60.00, "Equifax, CreditSafe", 0, "https://theceocreative.com/net-30-application/", "Online Form", "Requires min $60 store purchase for bureau reporting."),
                ("Home Depot Pro Commercial", 2, "Building & Hardware", "Revolving / Net 30", 100.00, "Experian, D&B", 0, "https://www.homedepot.com/c/Credit_Center", "Online Form", "Apply under Commercial Revolving. Keep EIN clean for instant approval."),
                ("WEX Fleet Fuel Card", 2, "Fuel & Maintenance", "Net 15 / Net 30", 75.00, "Experian, D&B", 0, "https://www.wexinc.com/solutions/fleet-cards/", "Online Form", "Provides fleet gas cards; reports invoice timeliness to Experian."),
                ("Staples Business Advantage", 2, "Commercial Supplies", "Revolving", 100.00, "D&B", 0, "https://www.staples.com/credit", "Online Form", "Requires 3+ established reporting tradelines."),
                ("Shell Fleet Plus", 2, "Fuel Services", "Net 30", 75.00, "Experian", 0, "https://www.shell.us/business-customers/commercial-fleet-cards.html", "Online Form", "Select corporate entity underwriting."),
                ("Amazon Business American Express", 3, "General Purchasing", "Net 60 / Revolving", 250.00, "Experian, D&B", 0, "https://www.amazon.com/businesscredit", "Online Portal", "Select 'Company Liability Only' option when underwriting allows."),
                ("Sam's Club Business Mastercard", 3, "Club Store / Equipment", "Revolving", 250.00, "D&B, Experian, Equifax", 0, "https://www.samsclub.com/credit", "Online Form", "Synchrony Bank underwriting. Solid Tier 2 track record needed."),
                ("Chase Ink Business Preferred", 4, "Commercial Bank Card", "Revolving", 500.00, "Equifax, Experian", 1, "https://creditcards.chase.com/business-credit-cards", "Bank Application", "Requires solid commercial bank rating and personal guarantee."),
                ("Bank of America Business Advantage", 4, "Credit Line / Card", "Revolving", 1000.00, "Experian, Equifax", 1, "https://www.bankofamerica.com/smallbusiness/credit-cards/", "Bank Application", "Established commercial deposit accounts accelerate approval.")
            ]
            cursor.executemany("""
            INSERT INTO vendors (name, tier, category, terms, min_invoice, reports_to, pg_required, application_url, application_type, underwriting_tips)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, vendor_seeds)
            conn.commit()

init_db()

# --- Pydantic Data Contracts ---
class CompanyProfileCreate(BaseModel):
    legal_name: str
    dba: Optional[str] = None
    entity_type: str = "LLC"
    state_of_inc: str
    date_established: str
    ein: str
    duns_number: Optional[str] = None
    industry_naics: Optional[str] = "541611"
    primary_phone: str
    primary_email: str
    website: Optional[str] = None
    physical_address: str
    city: str
    state: str
    zip_code: str
    officer_name: str
    officer_title: str = "Managing Member"
    officer_ssn_last4: Optional[str] = None
    officer_ownership_pct: float = 100.0
    bank_name: Optional[str] = "Chase Commercial Banking"
    bank_account_type: Optional[str] = "Business Checking"

class TradelineLink(BaseModel):
    vendor_id: int
    account_number: str
    credit_limit: float = Field(default=500.0, gt=0)

# --- Core Scoring & Optimization Engine ---
def compute_metrics(company_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT p.days_relative_to_due, v.reports_to
        FROM payment_records p
        JOIN tradelines t ON p.tradeline_id = t.id
        JOIN vendors v ON t.vendor_id = v.id
        WHERE t.company_id = ? AND t.status = 'approved';
        """, (company_id,))
        records = cursor.fetchall()
        
        if not records:
            paydex = None
            experian = None
            equifax = None
        else:
            dnb_scores, exp_scores, eq_scores = [], [], []
            for (delta, reports_to) in records:
                score = 100 if delta <= -30 else (90 if delta <= -15 else (80 if delta <= 0 else (70 if delta <= 15 else (60 if delta <= 30 else 50))))
                if "D&B" in reports_to: dnb_scores.append(score)
                if "Experian" in reports_to: exp_scores.append(score)
                if "Equifax" in reports_to: eq_scores.append(score)
                
            paydex = int(sum(dnb_scores) / len(dnb_scores)) if dnb_scores else None
            experian = int(sum(exp_scores) / len(exp_scores)) if exp_scores else None
            equifax = int(sum(eq_scores) / len(eq_scores)) if eq_scores else None
            
        cursor.execute("""
        SELECT v.tier, COUNT(DISTINCT t.id)
        FROM tradelines t
        JOIN vendors v ON t.vendor_id = v.id
        JOIN payment_records p ON p.tradeline_id = t.id
        WHERE t.company_id = ? AND t.status = 'approved'
        GROUP BY v.tier;
        """, (company_id,))
        
        tier_counts = dict(cursor.fetchall())
        t1, t2, t3 = tier_counts.get(1, 0), tier_counts.get(2, 0), tier_counts.get(3, 0)
        
        unlocked = 1
        eff_score = paydex or 0
        if t1 >= 5 and eff_score >= 80: unlocked = 2
        if unlocked == 2 and t2 >= 3 and eff_score >= 80: unlocked = 3
        if unlocked == 3 and t3 >= 3 and eff_score >= 80: unlocked = 4
        
        cursor.execute("UPDATE company_dossier SET current_unlocked_tier = ? WHERE id = ?", (unlocked, company_id))
        
        cursor.execute("SELECT SUM(credit_limit) FROM tradelines WHERE company_id = ? AND status = 'approved'", (company_id,))
        total_credit = cursor.fetchone()[0] or 0.0
        conn.commit()
        
        return {
            "paydex": paydex,
            "experian": experian,
            "equifax": equifax,
            "unlocked_tier": unlocked,
            "total_credit": total_credit,
            "t1_count": t1, "t2_count": t2, "t3_count": t3
        }

def recommend_next_vendor(company_id: int) -> Optional[Dict[str, Any]]:
    metrics = compute_metrics(company_id)
    unlocked_tier = metrics["unlocked_tier"]
    
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT vendor_id FROM tradelines WHERE company_id = ?", (company_id,))
        applied = {row[0] for row in cursor.fetchall()}
        
        cursor.execute("SELECT v.reports_to FROM tradelines t JOIN vendors v ON t.vendor_id = v.id WHERE t.company_id = ?;", (company_id,))
        current_reports = " ".join([r[0] for r in cursor.fetchall()])
        needs_equifax = "Equifax" not in current_reports
        needs_experian = "Experian" not in current_reports
        needs_dnb = "D&B" not in current_reports
        
        cursor.execute("SELECT id, name, tier, category, terms, min_invoice, reports_to, pg_required, application_url, underwriting_tips FROM vendors WHERE tier <= ? ORDER BY tier ASC, min_invoice ASC;", (unlocked_tier,))
        candidates = []
        for cand in cursor.fetchall():
            cid, name, tier, cat, terms, min_inv, reps, pg, app_url, tips = cand
            if cid in applied: continue
            score = 100 - min_inv
            if tier == unlocked_tier: score += 50
            if needs_dnb and "D&B" in reps: score += 40
            if needs_experian and "Experian" in reps: score += 35
            if needs_equifax and "Equifax" in reps: score += 30
            if pg == 0: score += 20
            
            candidates.append({
                "vendor_id": cid, "vendor_name": name, "tier": tier, "category": cat,
                "terms": terms, "min_purchase": min_inv, "reports_to": reps,
                "personal_guarantee": bool(pg), "application_url": app_url,
                "underwriting_tips": tips, "score": score
            })
            
        if not candidates: return None
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[0]

def generate_autofill_dossier(company_id: int) -> Dict[str, Any]:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM company_dossier WHERE id = ?", (company_id,))
        row = cursor.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Company not found.")
        d = dict(zip([col[0] for col in cursor.description], row))
        return {
            "company_profile": {
                "LegalBusinessName": d["legal_name"], "TradeName_DBA": d["dba"] or d["legal_name"],
                "EntityType": d["entity_type"], "StateOfIncorporation": d["state_of_inc"],
                "DateEstablished": d["date_established"], "FederalTaxID_EIN": d["ein"],
                "DUNS_Number": d["duns_number"] or "Pending D&B Generation", "NAICS_Code": d["industry_naics"]
            },
            "contact_and_location": {
                "BusinessAddress": d["physical_address"], "City": d["city"],
                "State": d["state"], "ZipCode": d["zip_code"], "PrimaryPhone": d["primary_phone"],
                "PrimaryEmail": d["primary_email"]
            },
            "authorized_officer": {
                "OfficerFullName": d["officer_name"], "Title": d["officer_title"],
                "OwnershipPercentage": f"{d['officer_ownership_pct']}%", "SSN_Last4": d["officer_ssn_last4"] or "N/A"
            }
        }

# --- REST API Endpoints ---
@app.get("/api/engine/dashboard/{company_id}")
def get_dashboard(company_id: int):
    return {
        "metrics": compute_metrics(company_id),
        "target_vendor": recommend_next_vendor(company_id),
        "autofill_payload": generate_autofill_dossier(company_id)
    }

@app.get("/api/portfolio/{company_id}")
def get_portfolio(company_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.id, v.name, v.tier, t.credit_limit, t.opened_date, t.account_number, v.reports_to
            FROM tradelines t JOIN vendors v ON t.vendor_id = v.id
            WHERE t.company_id = ? ORDER BY v.tier ASC;
        """, (company_id,))
        rows = cursor.fetchall()
        tradelines = [{
            "id": r[0], "vendor": r[1], "tier": r[2], "limit": r[3], 
            "opened": r[4], "account": r[5], "reports_to": r[6]
        } for r in rows]
        
        cursor.execute("""
            SELECT p.invoice_number, p.invoice_amount, p.paid_date, p.days_relative_to_due, v.name
            FROM payment_records p JOIN tradelines t ON p.tradeline_id = t.id JOIN vendors v ON t.vendor_id = v.id
            WHERE t.company_id = ? ORDER BY p.paid_date DESC LIMIT 10;
        """, (company_id,))
        payments = [{
            "invoice": r[0], "amount": r[1], "paid_date": r[2], "early_days": abs(r[3]) if r[3]<0 else 0, "vendor": r[4]
        } for r in cursor.fetchall()]
        
    return {"tradelines": tradelines, "recent_payments": payments, "metrics": compute_metrics(company_id)}

@app.get("/api/vendors/matrix/{company_id}")
def get_vendor_matrix(company_id: int):
    metrics = compute_metrics(company_id)
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT vendor_id FROM tradelines WHERE company_id = ?", (company_id,))
        applied = {row[0] for row in cursor.fetchall()}
        
        cursor.execute("SELECT * FROM vendors ORDER BY tier ASC, name ASC;")
        vendors = []
        for r in cursor.fetchall():
            d = dict(zip([col[0] for col in cursor.description], r))
            d["applied"] = d["id"] in applied
            d["locked"] = d["tier"] > metrics["unlocked_tier"]
            vendors.append(d)
    return {"vendors": vendors, "unlocked_tier": metrics["unlocked_tier"]}

@app.post("/api/tradelines/link/{company_id}")
def link_tradeline(company_id: int, payload: TradelineLink):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tradelines (company_id, vendor_id, account_number, credit_limit, opened_date) VALUES (?, ?, ?, ?, ?);",
                       (company_id, payload.vendor_id, payload.account_number, payload.credit_limit, now))
        conn.commit()
    return {"status": "Tradeline Linked Successfully"}

@app.post("/api/engine/simulate-month/{company_id}")
def simulate_month(company_id: int):
    """Time Machine: Generates random invoices for all active tradelines and pays them early to boost scores rapidly."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT t.id, v.min_invoice FROM tradelines t JOIN vendors v ON t.vendor_id = v.id WHERE t.company_id = ?;", (company_id,))
        tradelines = cursor.fetchall()
        
        count = 0
        now = datetime.now(timezone.utc)
        for tid, min_inv in tradelines:
            inv_amt = round(min_inv + random.uniform(10.0, 50.0), 2)
            inv_date = now - timedelta(days=random.randint(15, 30))
            due_date = inv_date + timedelta(days=30)
            # Pay 10-20 days early for perfect 80+ PAYDEX
            paid_date = due_date - timedelta(days=random.randint(10, 20))
            delta = (paid_date - due_date).days
            
            cursor.execute("""
            INSERT INTO payment_records (tradeline_id, invoice_number, invoice_amount, invoice_date, due_date, paid_date, days_relative_to_due)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (tid, f"INV-{random.randint(10000,99999)}", inv_amt, inv_date.strftime("%Y-%m-%d"), due_date.strftime("%Y-%m-%d"), paid_date.strftime("%Y-%m-%d"), delta))
            count += 1
        conn.commit()
    return {"status": "Simulation Complete", "invoices_generated": count, "new_metrics": compute_metrics(company_id)}

# --- Full SPA Dashboard ---
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
                    <i class="fa-solid fa-building-columns text-emerald-400"></i> TrueBuild V3
                </h1>
                <p class="text-[10px] text-slate-500 mt-1 uppercase tracking-wider">Automated Credit Engine</p>
            </div>
            <nav class="flex-1 p-4 space-y-2">
                <button onclick="switchTab('dashboard')" id="tab-dashboard" class="tab-btn active w-full text-left px-4 py-3 rounded-lg text-sm font-medium text-slate-400 hover:text-white transition flex items-center gap-3">
                    <i class="fa-solid fa-chart-line w-4"></i> Control Center
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
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
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
                            <div class="mt-6 flex gap-3">
                                <a id="btn-apply" href="#" target="_blank" class="flex-1 bg-emerald-600 hover:bg-emerald-500 text-center py-2 rounded font-medium transition">Open Portal <i class="fa-solid fa-external-link-alt text-xs ml-1"></i></a>
                                <button onclick="markApplied()" class="flex-1 border border-slate-700 hover:bg-slate-800 rounded font-medium transition">Mark Applied</button>
                            </div>
                        </div>
                    </div>
                    <!-- Autofill -->
                    <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col">
                        <div class="flex justify-between items-center mb-4">
                            <h3 class="text-lg font-bold"><i class="fa-solid fa-clipboard text-sky-400 mr-2"></i> Autofill Dossier</h3>
                            <button onclick="copyAutofill()" class="text-xs bg-sky-600 hover:bg-sky-500 px-3 py-1.5 rounded transition">Copy JSON</button>
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
                
                // Dashboard
                const dashRes = await fetch(`/api/engine/dashboard/${cid}`);
                const dash = await dashRes.json();
                
                // Update Metrics
                const m = dash.metrics;
                document.getElementById('m-paydex').innerText = m.paydex || 'N/A';
                document.getElementById('m-experian').innerText = m.experian || 'N/A';
                document.getElementById('m-equifax').innerText = m.equifax || 'N/A';
                document.getElementById('m-credit').innerText = `$${m.total_credit.toLocaleString()}`;
                
                // Update Target
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

                // Portfolio
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

                // Matrix
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
