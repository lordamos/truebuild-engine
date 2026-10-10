import json
import random
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, status
from fastapi.responses import HTMLResponse, Response
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from playwright.async_api import async_playwright

from database import engine, Base, get_db, SessionLocal
from models import User, CompanyDossier, Vendor, Tradeline, PaymentRecord
from auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, get_optional_user
)

app = FastAPI(title="TrueBuild Autonomous Credit Engine", version="6.0.0")

# ---------------------------------------------------------------------------
# Startup: Create tables & seed vendor data
# ---------------------------------------------------------------------------
@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;"))
        db.commit()
    except Exception:
        db.rollback()
    
    try:
        if db.query(Vendor).count() == 0:
            seeds = [
                Vendor(name="Uline", tier=1, category="Shipping Supplies", terms="Net 30", min_invoice=50.0, reports_to="Experian, D&B", pg_required=0, application_url="https://www.uline.com/CustomerService/CreditApplication", application_type="Online", underwriting_tips="Check 'Invoice My Account' at checkout."),
                Vendor(name="Grainger", tier=1, category="Industrial/MRO", terms="Net 30", min_invoice=50.0, reports_to="D&B", pg_required=0, application_url="https://www.grainger.com/content/credit-services", application_type="Online Form", underwriting_tips="Requires active state LLC registration."),
                Vendor(name="Quill", tier=1, category="Office Supplies", terms="Net 30", min_invoice=100.0, reports_to="D&B", pg_required=0, application_url="https://www.quill.com/account/net30terms", application_type="Online Form", underwriting_tips="Place 1-2 small pre-paid orders first."),
                Vendor(name="Nav Prime", tier=1, category="Financial Monitoring", terms="Net 30", min_invoice=49.99, reports_to="D&B, Experian, Equifax", pg_required=0, application_url="https://www.nav.com", application_type="SaaS Portal", underwriting_tips="Reports monthly to all three bureaus."),
                Vendor(name="The CEO Creative", tier=1, category="Office Supplies", terms="Net 30", min_invoice=60.0, reports_to="Equifax, CreditSafe", pg_required=0, application_url="https://theceocreative.com/net-30-application/", application_type="Online", underwriting_tips="Requires min $60 purchase."),
                Vendor(name="Home Depot Pro Commercial", tier=2, category="Hardware & Building", terms="Revolving / Net 30", min_invoice=100.0, reports_to="Experian, D&B", pg_required=0, application_url="https://www.homedepot.com/c/Credit_Center", application_type="Online", underwriting_tips="Apply under Commercial Revolving."),
                Vendor(name="WEX Fleet Fuel Card", tier=2, category="Fuel Services", terms="Net 15 / Net 30", min_invoice=75.0, reports_to="Experian, D&B", pg_required=0, application_url="https://www.wexinc.com/solutions/fleet-cards/", application_type="Online", underwriting_tips="Fleet gas cards; reports invoice timeliness."),
                Vendor(name="Staples Business Advantage", tier=2, category="Commercial Supplies", terms="Revolving", min_invoice=100.0, reports_to="D&B", pg_required=0, application_url="https://www.staples.com/credit", application_type="Online Form", underwriting_tips="Requires 3+ established reporting tradelines."),
                Vendor(name="Amazon Business American Express", tier=3, category="General Purchasing", terms="Net 60 / Revolving", min_invoice=250.0, reports_to="Experian, D&B", pg_required=0, application_url="https://www.amazon.com/businesscredit", application_type="Online Portal", underwriting_tips="Select 'Company Liability Only'."),
                Vendor(name="Sam's Club Business Mastercard", tier=3, category="Club Store / Equipment", terms="Revolving", min_invoice=250.0, reports_to="D&B, Experian, Equifax", pg_required=0, application_url="https://www.samsclub.com/credit", application_type="Online Form", underwriting_tips="Synchrony Bank underwriting."),
                Vendor(name="Chase Ink Business Preferred", tier=4, category="Commercial Bank Card", terms="Revolving", min_invoice=500.0, reports_to="Equifax, Experian", pg_required=1, application_url="https://creditcards.chase.com/business", application_type="Bank Application", underwriting_tips="Requires personal guarantee."),
                Vendor(name="Bank of America Business Advantage", tier=4, category="Credit Line / Card", terms="Revolving", min_invoice=1000.0, reports_to="Experian, Equifax", pg_required=1, application_url="https://www.bankofamerica.com/smallbusiness/credit-cards/", application_type="Bank Application", underwriting_tips="Established commercial deposits help."),
            ]
            db.add_all(seeds)
            db.commit()
    finally:
        db.close()

# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str = Field(min_length=8)

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    full_name: str
    company_id: Optional[int] = None

class CompanyCreate(BaseModel):
    legal_name: str
    dba: Optional[str] = None
    entity_type: str = "LLC"
    state_of_inc: str
    date_established: str
    ein: str
    duns_number: Optional[str] = None
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

class TradelineLink(BaseModel):
    vendor_id: int
    account_number: str
    credit_limit: float = Field(default=500.0, gt=0)

# ---------------------------------------------------------------------------
# Auth Endpoints
# ---------------------------------------------------------------------------
@app.post("/api/auth/register", response_model=LoginResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="An account with this email already exists.")
    user = User(full_name=payload.full_name, email=payload.email, hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": str(user.id)})
    return LoginResponse(access_token=token, user_id=user.id, full_name=user.full_name)

@app.post("/api/auth/login", response_model=LoginResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    token = create_access_token({"sub": str(user.id)})
    company = db.query(CompanyDossier).filter(CompanyDossier.owner_id == user.id).first()
    return LoginResponse(access_token=token, user_id=user.id, full_name=user.full_name, company_id=company.id if company else None)

@app.get("/api/auth/me")
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    company = db.query(CompanyDossier).filter(CompanyDossier.owner_id == current_user.id).first()
    return {"user_id": current_user.id, "full_name": current_user.full_name, "email": current_user.email, "company_id": company.id if company else None, "is_admin": current_user.is_admin}

# ---------------------------------------------------------------------------
# Company Management
# ---------------------------------------------------------------------------
@app.post("/api/company/create")
def create_company(payload: CompanyCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.query(CompanyDossier).filter(CompanyDossier.owner_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="You already have a company. Update it instead.")
    if db.query(CompanyDossier).filter(CompanyDossier.ein == payload.ein).first():
        raise HTTPException(status_code=400, detail="A company with this EIN is already registered.")
    co = CompanyDossier(owner_id=current_user.id, **payload.dict())
    db.add(co)
    db.commit()
    db.refresh(co)
    return {"status": "Company created", "company_id": co.id}

# ---------------------------------------------------------------------------
# Core Scoring Engine
# ---------------------------------------------------------------------------
def compute_metrics(db: Session, company_id: int):
    records = db.query(PaymentRecord.days_relative_to_due, Vendor.reports_to)\
        .join(Tradeline, PaymentRecord.tradeline_id == Tradeline.id)\
        .join(Vendor, Tradeline.vendor_id == Vendor.id)\
        .filter(Tradeline.company_id == company_id, Tradeline.status == 'approved').all()

    if not records:
        paydex, experian, equifax = None, None, None
    else:
        dnb, exp, eq = [], [], []
        for delta, rpts in records:
            s = 100 if delta <= -30 else (90 if delta <= -15 else (80 if delta <= 0 else (70 if delta <= 15 else (60 if delta <= 30 else 50))))
            if "D&B" in rpts: dnb.append(s)
            if "Experian" in rpts: exp.append(s)
            if "Equifax" in rpts: eq.append(s)
        paydex = int(sum(dnb)/len(dnb)) if dnb else None
        experian = int(sum(exp)/len(exp)) if exp else None
        equifax = int(sum(eq)/len(eq)) if eq else None

    tier_counts = db.query(Vendor.tier, func.count(func.distinct(Tradeline.id)))\
        .join(Tradeline, Tradeline.vendor_id == Vendor.id)\
        .join(PaymentRecord, PaymentRecord.tradeline_id == Tradeline.id)\
        .filter(Tradeline.company_id == company_id, Tradeline.status == 'approved')\
        .group_by(Vendor.tier).all()

    counts = {t: c for t, c in tier_counts}
    t1, t2, t3 = counts.get(1, 0), counts.get(2, 0), counts.get(3, 0)
    unlocked, eff = 1, paydex or 0
    if t1 >= 5 and eff >= 80: unlocked = 2
    if unlocked == 2 and t2 >= 3 and eff >= 80: unlocked = 3
    if unlocked == 3 and t3 >= 3 and eff >= 80: unlocked = 4

    co = db.query(CompanyDossier).filter(CompanyDossier.id == company_id).first()
    if co and co.current_unlocked_tier != unlocked:
        co.current_unlocked_tier = unlocked
        db.commit()

    total = db.query(func.sum(Tradeline.credit_limit))\
        .filter(Tradeline.company_id == company_id, Tradeline.status == 'approved').scalar() or 0.0
    return {"paydex": paydex, "experian": experian, "equifax": equifax, "unlocked_tier": unlocked, "total_credit": total, "t1_count": t1, "t2_count": t2, "t3_count": t3}

def recommend_next_vendor(db: Session, company_id: int):
    metrics = compute_metrics(db, company_id)
    unlocked = metrics["unlocked_tier"]
    applied = {t.vendor_id for t in db.query(Tradeline.vendor_id).filter(Tradeline.company_id == company_id).all()}
    current_reports = " ".join([r[0] for r in db.query(Vendor.reports_to).join(Tradeline).filter(Tradeline.company_id == company_id).all()])
    
    candidates = []
    for v in db.query(Vendor).filter(Vendor.tier <= unlocked).all():
        if v.id in applied: continue
        score = 100 - v.min_invoice
        if v.tier == unlocked: score += 50
        if "D&B" not in current_reports and "D&B" in v.reports_to: score += 40
        if "Experian" not in current_reports and "Experian" in v.reports_to: score += 35
        if "Equifax" not in current_reports and "Equifax" in v.reports_to: score += 30
        if v.pg_required == 0: score += 20
        candidates.append({"vendor_id": v.id, "vendor_name": v.name, "tier": v.tier, "category": v.category, "terms": v.terms, "min_purchase": v.min_invoice, "reports_to": v.reports_to, "personal_guarantee": bool(v.pg_required), "application_url": v.application_url, "underwriting_tips": v.underwriting_tips, "score": score})

    if not candidates: return None
    return sorted(candidates, key=lambda x: x["score"], reverse=True)[0]

def generate_autofill(db: Session, company_id: int):
    co = db.query(CompanyDossier).filter(CompanyDossier.id == company_id).first()
    if not co: raise HTTPException(status_code=404, detail="Company not found.")
    return {
        "company_profile": {"LegalBusinessName": co.legal_name, "TradeName_DBA": co.dba or co.legal_name, "EntityType": co.entity_type, "StateOfIncorporation": co.state_of_inc, "DateEstablished": co.date_established, "FederalTaxID_EIN": co.ein, "DUNS_Number": co.duns_number or "Pending D&B Generation"},
        "contact_and_location": {"BusinessAddress": co.physical_address, "City": co.city, "State": co.state, "ZipCode": co.zip_code, "PrimaryPhone": co.primary_phone, "PrimaryEmail": co.primary_email},
        "authorized_officer": {"OfficerFullName": co.officer_name, "Title": co.officer_title, "OwnershipPercentage": f"{co.officer_ownership_pct}%"}
    }

# ---------------------------------------------------------------------------
# Browser Automation
# ---------------------------------------------------------------------------
async def browser_autofill_worker(company_id: int, vendor_id: int):
    db = SessionLocal()
    try:
        v = db.query(Vendor).filter(Vendor.id == vendor_id).first()
        if not v: return
        dossier = generate_autofill(db, company_id)
        url = v.application_url
    finally:
        db.close()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await (await browser.new_context()).new_page()
        await page.goto(url, timeout=60000)
        try:
            await page.evaluate(f"""
            (function() {{
                const d = {json.dumps(dossier)};
                function fill(keys, val) {{
                    if (!val) return;
                    document.querySelectorAll('input:not([type=hidden]):not([type=submit]),textarea').forEach(el => {{
                        const t = (el.name+el.id+el.placeholder).toLowerCase();
                        if (keys.some(k => t.includes(k)) && !el.dataset.af) {{
                            el.value = val; el.dataset.af = 1;
                            el.style.cssText = 'border:2px solid #10b981!important;background:#ecfdf5!important';
                            el.dispatchEvent(new Event('input',{{bubbles:true}}));
                            el.dispatchEvent(new Event('change',{{bubbles:true}}));
                        }}
                    }});
                }}
                setTimeout(() => {{
                    fill(['company','business','legal'], d.company_profile.LegalBusinessName);
                    fill(['ein','tax','fein','federal'], d.company_profile.FederalTaxID_EIN);
                    fill(['address','street','line1'], d.contact_and_location.BusinessAddress);
                    fill(['city'], d.contact_and_location.City);
                    fill(['zip','postal'], d.contact_and_location.ZipCode);
                    fill(['phone','mobile'], d.contact_and_location.PrimaryPhone);
                    fill(['email'], d.contact_and_location.PrimaryEmail);
                    fill(['name','officer','applicant'], d.authorized_officer.OfficerFullName);
                }}, 2000);
            }})();
            """)
        except: pass
        try:
            await page.wait_for_event("close", timeout=0)
        except: pass

# ---------------------------------------------------------------------------
# Protected API Endpoints
# ---------------------------------------------------------------------------
@app.post("/api/engine/launch-autofill/{company_id}/{vendor_id}")
async def launch_autofill(company_id: int, vendor_id: int, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    co = db.query(CompanyDossier).filter(CompanyDossier.id == company_id, CompanyDossier.owner_id == current_user.id).first()
    if not co: raise HTTPException(status_code=403, detail="Access denied.")
    background_tasks.add_task(browser_autofill_worker, company_id, vendor_id)
    return {"status": "Browser Launched"}


@app.get("/api/engine/generate-invoice/{payment_id}")
async def generate_invoice_pdf(payment_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    payment = db.query(PaymentRecord).filter(PaymentRecord.id == payment_id).first()
    if not payment: raise HTTPException(status_code=404, detail="Payment not found")
    
    tradeline = db.query(Tradeline).filter(Tradeline.id == payment.tradeline_id).first()
    co = db.query(CompanyDossier).filter(CompanyDossier.id == tradeline.company_id, CompanyDossier.owner_id == current_user.id).first()
    if not co: raise HTTPException(status_code=403, detail="Access denied")
    
    vendor = db.query(Vendor).filter(Vendor.id == tradeline.vendor_id).first()

    html = f'''
    <!DOCTYPE html>
    <html>
    <head><script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script></head>
    <body class="p-12 font-sans bg-white text-slate-800">
        <div class="max-w-4xl mx-auto border border-slate-200 p-10 rounded-xl shadow-sm">
            <div class="flex justify-between items-start mb-12 border-b border-slate-200 pb-8">
                <div>
                    <h1 class="text-4xl font-black text-slate-900 tracking-tight mb-2">{vendor.name.upper()}</h1>
                    <p class="text-sm text-slate-500 font-medium">Commercial Account / Net-30 Terms</p>
                    <p class="text-xs text-slate-400 mt-1">Vendor ID: {vendor.id} | Tier {vendor.tier}</p>
                </div>
                <div class="text-right">
                    <h2 class="text-3xl font-bold text-slate-300 uppercase tracking-widest">INVOICE</h2>
                    <p class="font-bold text-lg mt-2 text-slate-700">#{payment.invoice_number}</p>
                    <p class="text-sm text-slate-500 mt-1">Issue Date: {payment.invoice_date}</p>
                    <p class="text-sm text-slate-500 font-bold text-emerald-600">Paid Date: {payment.paid_date}</p>
                </div>
            </div>
            
            <div class="flex justify-between mb-12">
                <div class="w-1/2">
                    <h3 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Billed To</h3>
                    <p class="font-bold text-lg text-slate-800">{co.legal_name}</p>
                    <p class="text-sm text-slate-600">{co.physical_address}</p>
                    <p class="text-sm text-slate-600">{co.city}, {co.state} {co.zip_code}</p>
                    <p class="text-sm text-slate-600 mt-2">EIN: {co.ein}</p>
                </div>
                <div class="w-1/3 bg-slate-50 p-4 rounded-lg border border-slate-100">
                    <div class="flex justify-between mb-2"><span class="text-sm text-slate-500">Account #</span><span class="font-medium">{tradeline.account_number}</span></div>
                    <div class="flex justify-between mb-2"><span class="text-sm text-slate-500">Credit Limit</span><span class="font-medium">${tradeline.credit_limit:,.2f}</span></div>
                    <div class="flex justify-between font-bold text-emerald-600 pt-2 border-t border-slate-200"><span class="text-sm">Status</span><span>PAID IN FULL</span></div>
                </div>
            </div>

            <table class="w-full text-left mb-12">
                <thead>
                    <tr class="border-b-2 border-slate-800 text-slate-600 text-sm">
                        <th class="py-3 font-bold uppercase tracking-wider">Description</th>
                        <th class="py-3 font-bold uppercase tracking-wider text-right">Amount</th>
                    </tr>
                </thead>
                <tbody>
                    <tr class="border-b border-slate-200">
                        <td class="py-4 text-slate-700">{vendor.category} - Commercial Purchase</td>
                        <td class="py-4 text-right font-medium text-slate-800">${payment.invoice_amount:,.2f}</td>
                    </tr>
                </tbody>
            </table>
            
            <div class="flex justify-end mb-16">
                <div class="w-1/3">
                    <div class="flex justify-between font-bold text-xl py-3 border-t-2 border-slate-800">
                        <span>Total Paid</span>
                        <span>${payment.invoice_amount:,.2f}</span>
                    </div>
                </div>
            </div>

            <div class="text-center text-xs text-slate-400 mt-16 pt-8 border-t border-slate-200">
                <p>This invoice is electronically generated and serves as proof of commercial payment.</p>
                <p>Reported to: {vendor.reports_to}</p>
            </div>
        </div>
    </body>
    </html>
    '''
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(html)
        pdf_bytes = await page.pdf(format="Letter", print_background=True, margin={"top": "0.5in", "bottom": "0.5in", "left": "0.5in", "right": "0.5in"})
        await browser.close()
        
    safe_name = vendor.name.replace(" ", "_").replace("/", "_")
    return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{safe_name}_Invoice_{payment.invoice_number}.pdf"'})


@app.get("/api/engine/dashboard/{company_id}")
def get_dashboard(company_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    co = db.query(CompanyDossier).filter(CompanyDossier.id == company_id, CompanyDossier.owner_id == current_user.id).first()
    if not co: raise HTTPException(status_code=403, detail="Access denied.")
    metrics = compute_metrics(db, company_id)
    return {"metrics": metrics, "target_vendor": recommend_next_vendor(db, company_id), "autofill_payload": generate_autofill(db, company_id), "fundability": get_fundability(co), "chart_data": get_chart_data(metrics)}

@app.get("/api/portfolio/{company_id}")
def get_portfolio(company_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    co = db.query(CompanyDossier).filter(CompanyDossier.id == company_id, CompanyDossier.owner_id == current_user.id).first()
    if not co: raise HTTPException(status_code=403, detail="Access denied.")
    tls = db.query(Tradeline, Vendor).join(Vendor).filter(Tradeline.company_id == company_id).order_by(Vendor.tier).all()
    t_list = [{"id": t.id, "vendor": v.name, "tier": v.tier, "limit": t.credit_limit, "opened": t.opened_date, "account": t.account_number, "reports_to": v.reports_to} for t, v in tls]
    pmts = db.query(PaymentRecord, Tradeline, Vendor).join(Tradeline).join(Vendor).filter(Tradeline.company_id == company_id).order_by(PaymentRecord.paid_date.desc()).limit(10).all()
    p_list = [{"id": p.id, "invoice": p.invoice_number, "amount": p.invoice_amount, "paid_date": p.paid_date, "early_days": abs(p.days_relative_to_due) if p.days_relative_to_due < 0 else 0, "vendor": v.name} for p, t, v in pmts]
    return {"tradelines": t_list, "recent_payments": p_list, "metrics": compute_metrics(db, company_id)}

@app.get("/api/vendors/matrix/{company_id}")
def get_vendor_matrix(company_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    metrics = compute_metrics(db, company_id)
    applied = {t.vendor_id for t in db.query(Tradeline.vendor_id).filter(Tradeline.company_id == company_id).all()}
    vendors = db.query(Vendor).order_by(Vendor.tier, Vendor.name).all()
    return {"vendors": [{"id": v.id, "name": v.name, "tier": v.tier, "category": v.category, "terms": v.terms, "min_invoice": v.min_invoice, "reports_to": v.reports_to, "pg_required": v.pg_required, "application_url": v.application_url, "applied": v.id in applied, "locked": v.tier > metrics["unlocked_tier"]} for v in vendors], "unlocked_tier": metrics["unlocked_tier"]}

@app.post("/api/tradelines/link/{company_id}")
def link_tradeline(company_id: int, payload: TradelineLink, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    co = db.query(CompanyDossier).filter(CompanyDossier.id == company_id, CompanyDossier.owner_id == current_user.id).first()
    if not co: raise HTTPException(status_code=403, detail="Access denied.")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    db.add(Tradeline(company_id=company_id, vendor_id=payload.vendor_id, account_number=payload.account_number, credit_limit=payload.credit_limit, opened_date=now, status="approved"))
    db.commit()
    return {"status": "Tradeline Linked"}

@app.post("/api/engine/simulate-month/{company_id}")
def simulate_month(company_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    co = db.query(CompanyDossier).filter(CompanyDossier.id == company_id, CompanyDossier.owner_id == current_user.id).first()
    if not co: raise HTTPException(status_code=403, detail="Access denied.")
    now, count = datetime.now(timezone.utc), 0
    for t, v in db.query(Tradeline, Vendor).join(Vendor).filter(Tradeline.company_id == company_id).all():
        amt = round(v.min_invoice + random.uniform(10, 50), 2)
        inv = now - timedelta(days=random.randint(15, 30))
        due = inv + timedelta(days=30)
        paid = due - timedelta(days=random.randint(10, 20))
        db.add(PaymentRecord(tradeline_id=t.id, invoice_number=f"INV-{random.randint(10000,99999)}", invoice_amount=amt, invoice_date=inv.strftime("%Y-%m-%d"), due_date=due.strftime("%Y-%m-%d"), paid_date=paid.strftime("%Y-%m-%d"), days_relative_to_due=(paid-due).days))
        count += 1
    db.commit()
    return {"status": "Simulation Complete", "invoices_generated": count}

# ---------------------------------------------------------------------------
# Full SPA with Login/Register Gate
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TrueBuild | Corporate Credit Engine</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
  .tab-btn.active{background-color:#0f172a;color:#10b981;border-left:3px solid #10b981}
  .view-section{display:none}.view-section.active{display:block;animation:fadeIn .3s}
  @keyframes fadeIn{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:translateY(0)}}
  .modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,.75);display:flex;align-items:center;justify-content:center;z-index:50}
  .modal-box{background:#0f172a;border:1px solid #1e293b;border-radius:1rem;padding:2rem;width:100%;max-width:420px}
</style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen font-sans">

<!-- ===== AUTH GATE ===== -->
<div id="auth-gate" class="modal-overlay">
  <div class="modal-box">
    <div class="text-center mb-6">
      <i class="fa-solid fa-robot text-3xl text-sky-400 mb-2 block"></i>
      <h1 class="text-2xl font-bold text-white">TrueBuild V6.0</h1>
      <p class="text-slate-400 text-sm mt-1">Autonomous Corporate Credit Engine</p>
    </div>
    <div class="flex gap-2 mb-6">
      <button onclick="authTab('login')" id="atab-login" class="flex-1 py-2 rounded-lg text-sm font-bold bg-sky-600 text-white transition">Sign In</button>
      <button onclick="authTab('register')" id="atab-register" class="flex-1 py-2 rounded-lg text-sm font-bold bg-slate-800 text-slate-400 transition">Register</button>
    </div>

    <!-- Login Form -->
    <div id="form-login">
      <div class="space-y-3">
        <input id="l-email" type="email" placeholder="Email address" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-sky-500">
        <input id="l-pass" type="password" placeholder="Password" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-sky-500">
        <button onclick="doLogin()" class="w-full bg-sky-600 hover:bg-sky-500 text-white font-bold py-2.5 rounded-lg transition">Sign In <i class="fa-solid fa-arrow-right ml-1"></i></button>
        <p id="l-err" class="text-red-400 text-xs text-center hidden"></p>
      </div>
    </div>

    <!-- Register Form -->
    <div id="form-register" class="hidden">
      <div class="space-y-3">
        <input id="r-name" type="text" placeholder="Full name" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-emerald-500">
        <input id="r-email" type="email" placeholder="Business email" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-emerald-500">
        <input id="r-pass" type="password" placeholder="Password (min 8 characters)" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-emerald-500">
        <button onclick="doRegister()" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-2.5 rounded-lg transition">Create Account <i class="fa-solid fa-arrow-right ml-1"></i></button>
        <p id="r-err" class="text-red-400 text-xs text-center hidden"></p>
      </div>
    </div>
  </div>
</div>

<!-- ===== COMPANY SETUP MODAL ===== -->
<div id="setup-gate" class="modal-overlay hidden">
  <div class="modal-box" style="max-width:560px;max-height:90vh;overflow-y:auto">
    <h2 class="text-xl font-bold mb-1"><i class="fa-solid fa-building text-emerald-400 mr-2"></i>Company Profile Setup</h2>
    <p class="text-slate-400 text-sm mb-5">Enter your business details to begin building corporate credit.</p>
    <div class="grid grid-cols-2 gap-3 text-sm">
      <div class="col-span-2"><label class="text-slate-400 text-xs">Legal Business Name *</label><input id="s-legal" class="w-full mt-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 focus:outline-none focus:border-emerald-500"></div>
      <div><label class="text-slate-400 text-xs">DBA / Trade Name</label><input id="s-dba" class="w-full mt-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 focus:outline-none focus:border-emerald-500"></div>
      <div><label class="text-slate-400 text-xs">State of Inc *</label><input id="s-state-inc" placeholder="FL" class="w-full mt-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 focus:outline-none focus:border-emerald-500"></div>
      <div><label class="text-slate-400 text-xs">Date Established *</label><input id="s-date" type="date" class="w-full mt-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 focus:outline-none focus:border-emerald-500"></div>
      <div><label class="text-slate-400 text-xs">EIN *</label><input id="s-ein" placeholder="XX-XXXXXXX" class="w-full mt-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 focus:outline-none focus:border-emerald-500"></div>
      <div><label class="text-slate-400 text-xs">Business Phone *</label><input id="s-phone" class="w-full mt-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 focus:outline-none focus:border-emerald-500"></div>
      <div><label class="text-slate-400 text-xs">Business Email *</label><input id="s-email" class="w-full mt-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 focus:outline-none focus:border-emerald-500"></div>
      <div class="col-span-2"><label class="text-slate-400 text-xs">Street Address *</label><input id="s-addr" class="w-full mt-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 focus:outline-none focus:border-emerald-500"></div>
      <div><label class="text-slate-400 text-xs">City *</label><input id="s-city" class="w-full mt-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 focus:outline-none focus:border-emerald-500"></div>
      <div><label class="text-slate-400 text-xs">State *</label><input id="s-state" placeholder="FL" class="w-full mt-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 focus:outline-none focus:border-emerald-500"></div>
      <div><label class="text-slate-400 text-xs">Zip Code *</label><input id="s-zip" class="w-full mt-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 focus:outline-none focus:border-emerald-500"></div>
      <div><label class="text-slate-400 text-xs">Officer Name *</label><input id="s-officer" class="w-full mt-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 focus:outline-none focus:border-emerald-500"></div>
    </div>
    <button onclick="doSetupCompany()" class="w-full mt-5 bg-emerald-600 hover:bg-emerald-500 font-bold py-3 rounded-lg transition">Save & Launch Dashboard <i class="fa-solid fa-rocket ml-1"></i></button>
    <p id="s-err" class="text-red-400 text-xs text-center mt-2 hidden"></p>
  </div>
</div>

<!-- ===== MAIN APP ===== -->
<div id="main-app" class="hidden flex min-h-screen">
  <aside class="w-64 bg-slate-900 border-r border-slate-800 flex flex-col hidden md:flex">
    <div class="p-6 border-b border-slate-800">
      <h1 class="text-xl font-bold text-white flex items-center gap-2"><i class="fa-solid fa-robot text-sky-400"></i> TrueBuild V6</h1>
      <p id="nav-user" class="text-xs text-slate-500 mt-1 truncate"></p>
    </div>
    <nav class="flex-1 p-4 space-y-1">
      <button onclick="switchTab('dashboard')" id="tab-dashboard" class="tab-btn active w-full text-left px-4 py-3 rounded-lg text-sm font-medium text-slate-400 hover:text-white transition flex items-center gap-3"><i class="fa-solid fa-rocket w-4"></i> Auto-Fill Engine</button>
      <button onclick="switchTab('portfolio')" id="tab-portfolio" class="tab-btn w-full text-left px-4 py-3 rounded-lg text-sm font-medium text-slate-400 hover:text-white transition flex items-center gap-3"><i class="fa-solid fa-wallet w-4"></i> Credit Portfolio</button>
      <button onclick="switchTab('admin')" id="tab-admin" class="tab-btn hidden w-full text-left px-4 py-3 rounded-lg text-sm font-medium text-slate-400 hover:text-white transition flex items-center gap-3"><i class="fa-solid fa-shield-halved w-4"></i> Admin Panel</button>
      <button onclick="switchTab('matrix')" id="tab-matrix" class="tab-btn w-full text-left px-4 py-3 rounded-lg text-sm font-medium text-slate-400 hover:text-white transition flex items-center gap-3"><i class="fa-solid fa-sitemap w-4"></i> Vendor Matrix</button>
    </nav>
    <div class="p-4 border-t border-slate-800">
      <button onclick="doLogout()" class="w-full text-slate-500 hover:text-red-400 text-sm py-2 transition flex items-center gap-2"><i class="fa-solid fa-right-from-bracket"></i> Sign Out</button>
    </div>
  </aside>

  <main class="flex-1 p-8 overflow-y-auto max-h-screen">
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-4"><p class="text-xs text-slate-400">D&B PAYDEX</p><h2 id="m-paydex" class="text-2xl font-bold text-emerald-400 mt-1">--</h2></div>
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-4"><p class="text-xs text-slate-400">Experian Score</p><h2 id="m-experian" class="text-2xl font-bold text-blue-400 mt-1">--</h2></div>
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-4"><p class="text-xs text-slate-400">Equifax Score</p><h2 id="m-equifax" class="text-2xl font-bold text-red-400 mt-1">--</h2></div>
      <div class="bg-slate-900 border border-emerald-900/50 rounded-xl p-4"><p class="text-xs text-slate-400">Total Corporate Credit</p><h2 id="m-credit" class="text-2xl font-bold text-white mt-1">--</h2></div>
    </div>

    <!-- Dashboard Tab -->
    <div id="view-dashboard" class="view-section active space-y-6">
      
        <!-- Top row: Charts and Fundability -->
        <div class="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
            <div class="bg-slate-900 border border-slate-800 rounded-xl p-6">
                <h3 class="text-lg font-bold mb-4"><i class="fa-solid fa-chart-line text-sky-400 mr-2"></i> Credit Growth</h3>
                <canvas id="creditChart" height="200"></canvas>
            </div>
            <div class="bg-slate-900 border border-slate-800 rounded-xl p-6">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-lg font-bold"><i class="fa-solid fa-shield-check text-emerald-400 mr-2"></i> Fundability Score</h3>
                    <span id="fund-score" class="text-2xl font-black text-emerald-400">0/100</span>
                </div>
                <div id="fund-checks" class="space-y-3 mt-4"></div>
            </div>
        </div>
        <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
        
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div class="flex justify-between items-start mb-4">
            <h3 class="text-lg font-bold"><i class="fa-solid fa-crosshairs text-sky-400 mr-2"></i> Next Target Application</h3>
            <span id="target-tier" class="bg-slate-800 text-xs px-2 py-1 rounded">--</span>
          </div>
          <h4 id="target-name" class="text-3xl font-extrabold text-white mb-2">Loading...</h4>
          <p class="text-sm text-slate-400 mb-4" id="target-desc">--</p>
          <div class="space-y-2 text-sm bg-slate-950 p-4 rounded-lg border border-slate-800 mb-6">
            <div class="flex justify-between"><span class="text-slate-500">Reports To:</span><span id="target-reports" class="text-emerald-400">--</span></div>
            <div class="flex justify-between"><span class="text-slate-500">Min Invoice:</span><span id="target-min">--</span></div>
            <div class="flex justify-between"><span class="text-slate-500">PG Required:</span><span id="target-pg">--</span></div>
            <div class="flex justify-between"><span class="text-slate-500">Tips:</span><span id="target-tips" class="text-xs text-slate-400 text-right max-w-48">--</span></div>
          </div>
          <div class="flex flex-col gap-3">
            <button onclick="launchBot()" id="btn-bot" class="w-full bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 text-white py-3 rounded-lg font-bold text-lg flex items-center justify-center gap-2"><i class="fa-solid fa-robot"></i> Launch Browser Auto-Fill Bot</button>
            <div class="flex gap-3">
              <a id="btn-apply" href="#" target="_blank" class="flex-1 bg-slate-800 hover:bg-slate-700 text-center py-2.5 rounded-lg font-medium text-sm transition">Open Portal Manually</a>
              <button onclick="markApplied()" class="flex-1 border border-slate-700 hover:bg-slate-800 rounded-lg font-medium text-sm transition">Mark as Applied</button>
            </div>
          </div>
        </div>
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col">
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg font-bold"><i class="fa-solid fa-clipboard text-emerald-400 mr-2"></i> Dossier Payload</h3>
            <button onclick="copyDossier()" class="text-xs bg-emerald-600 hover:bg-emerald-500 px-3 py-1.5 rounded transition">Copy JSON</button>
          </div>
          <pre id="autofill-box" class="bg-slate-950 text-emerald-400 p-4 rounded-lg text-xs font-mono overflow-auto flex-1 border border-slate-800"></pre>
        </div>
      </div>
    </div>

    <!-- Portfolio Tab -->
    <div id="view-portfolio" class="view-section space-y-6">
      <div class="bg-indigo-950/30 border border-indigo-900/50 rounded-xl p-6 flex justify-between items-center">
        <div><h3 class="text-lg font-bold text-indigo-400"><i class="fa-solid fa-clock-rotate-left mr-2"></i> Time Machine Simulator</h3><p class="text-sm text-slate-400">Generate 30 days of mock invoices & early payments to build scores instantly.</p></div>
        <button onclick="simulateMonth()" class="bg-indigo-600 hover:bg-indigo-500 text-white px-6 py-3 rounded-lg font-bold transition">Simulate 30 Days</button>
      </div>
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h3 class="text-lg font-bold mb-4">Active Tradelines</h3>
          <table class="w-full text-sm"><thead class="text-xs text-slate-500 bg-slate-950 border-b border-slate-800"><tr><th class="px-4 py-3 text-left">Vendor</th><th class="px-4 py-3 text-left">Tier</th><th class="px-4 py-3 text-left">Credit Limit</th><th class="px-4 py-3 text-left">Reports To</th></tr></thead><tbody id="tradelines-table" class="divide-y divide-slate-800/50 text-slate-300"></tbody></table>
        </div>
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-6"><h3 class="text-lg font-bold mb-4">Recent Payments</h3><div id="payments-list" class="space-y-3"></div></div>
      </div>
    </div>

    
    <!-- Admin Tab -->
    <div id="view-admin" class="view-section space-y-6">
      <div class="grid grid-cols-3 gap-4 mb-6">
        <div class="bg-indigo-950/30 border border-indigo-900/50 rounded-xl p-4"><p class="text-xs text-indigo-300">Total Users</p><h2 id="ad-users" class="text-2xl font-bold text-white mt-1">--</h2></div>
        <div class="bg-emerald-950/30 border border-emerald-900/50 rounded-xl p-4"><p class="text-xs text-emerald-300">Companies</p><h2 id="ad-comps" class="text-2xl font-bold text-white mt-1">--</h2></div>
        <div class="bg-sky-950/30 border border-sky-900/50 rounded-xl p-4"><p class="text-xs text-sky-300">Active Tradelines</p><h2 id="ad-trades" class="text-2xl font-bold text-white mt-1">--</h2></div>
      </div>
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h3 class="text-lg font-bold mb-4">Vendor Database</h3>
        <table class="w-full text-sm"><thead class="text-xs text-slate-500 bg-slate-950 border-b border-slate-800"><tr><th class="px-4 py-3 text-left">Vendor Name</th><th class="px-4 py-3 text-left">Tier</th><th class="px-4 py-3 text-left">Category</th></tr></thead><tbody id="ad-vendors" class="divide-y divide-slate-800/50 text-slate-300"></tbody></table>
      </div>
    </div>
    <!-- Matrix Tab -->
        
    <div id="view-matrix" class="view-section">
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h3 class="text-lg font-bold mb-6"><i class="fa-solid fa-network-wired text-sky-400 mr-2"></i> Full Vendor Ladder Matrix</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" id="matrix-grid"></div>
      </div>
    </div>
  </main>
</div>

<script>
  let TOKEN = localStorage.getItem('tb_token');
  let COMPANY_ID = localStorage.getItem('tb_company_id');
  let currentTargetId = null;
  let dossierJson = '';

  // --- Boot ---
  window.onload = async () => {
    if (TOKEN) {
      try {
        const me = await apiFetch('/api/auth/me');
        if (me.is_admin) document.getElementById("tab-admin").classList.remove("hidden");
        if (me.company_id) { COMPANY_ID = me.company_id; localStorage.setItem('tb_company_id', COMPANY_ID); showApp(me); }
        else { hideAll(); document.getElementById('setup-gate').classList.remove('hidden'); }
      } catch { showAuthGate(); }
    } else { showAuthGate(); }
  };

  function showAuthGate() { hideAll(); document.getElementById('auth-gate').style.display='flex'; }
  function showApp(me) { hideAll(); document.getElementById('main-app').classList.remove('hidden'); document.getElementById('nav-user').textContent = me.full_name + ' · Co. #' + COMPANY_ID; loadAllData(); }
  function hideAll() { document.getElementById('auth-gate').style.display='none'; document.getElementById('setup-gate').classList.add('hidden'); document.getElementById('main-app').classList.add('hidden'); }

  function authTab(tab) {
    document.getElementById('form-login').classList.toggle('hidden', tab !== 'login');
    document.getElementById('form-register').classList.toggle('hidden', tab !== 'register');
    document.getElementById('atab-login').className = 'flex-1 py-2 rounded-lg text-sm font-bold transition ' + (tab==='login' ? 'bg-sky-600 text-white' : 'bg-slate-800 text-slate-400');
    document.getElementById('atab-register').className = 'flex-1 py-2 rounded-lg text-sm font-bold transition ' + (tab==='register' ? 'bg-emerald-600 text-white' : 'bg-slate-800 text-slate-400');
  }

  async function doLogin() {
    const email = document.getElementById('l-email').value;
    const pass = document.getElementById('l-pass').value;
    const errEl = document.getElementById('l-err');
    try {
      const form = new URLSearchParams({ username: email, password: pass });
      const res = await fetch('/api/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: form });
      if (!res.ok) { 
        const e = await res.json(); 
        errEl.textContent = Array.isArray(e.detail) ? e.detail[0].msg : e.detail; 
        errEl.classList.remove('hidden'); 
        return; 
      }
      const data = await res.json();
      TOKEN = data.access_token; localStorage.setItem('tb_token', TOKEN);
      if (data.is_admin) document.getElementById("tab-admin").classList.remove("hidden");
      if (data.company_id) { COMPANY_ID = data.company_id; localStorage.setItem('tb_company_id', COMPANY_ID); showApp(data); }
      else { hideAll(); document.getElementById('setup-gate').classList.remove('hidden'); }
    } catch(e) { errEl.textContent = 'Network error. Is the server running?'; errEl.classList.remove('hidden'); }
  }

  async function doRegister() {
    const errEl = document.getElementById('r-err');
    const payload = { full_name: document.getElementById('r-name').value, email: document.getElementById('r-email').value, password: document.getElementById('r-pass').value };
    try {
      const res = await fetch('/api/auth/register', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      if (!res.ok) { 
        const e = await res.json(); 
        errEl.textContent = Array.isArray(e.detail) ? e.detail[0].msg : e.detail; 
        errEl.classList.remove('hidden'); 
        return; 
      }
      const data = await res.json();
      TOKEN = data.access_token; localStorage.setItem('tb_token', TOKEN);
      hideAll(); document.getElementById('setup-gate').classList.remove('hidden');
    } catch(e) { errEl.textContent = 'Network error.'; errEl.classList.remove('hidden'); }
  }

  async function doSetupCompany() {
    const errEl = document.getElementById('s-err');
    const payload = { legal_name: document.getElementById('s-legal').value, dba: document.getElementById('s-dba').value, state_of_inc: document.getElementById('s-state-inc').value, date_established: document.getElementById('s-date').value, ein: document.getElementById('s-ein').value, primary_phone: document.getElementById('s-phone').value, primary_email: document.getElementById('s-email').value, physical_address: document.getElementById('s-addr').value, city: document.getElementById('s-city').value, state: document.getElementById('s-state').value, zip_code: document.getElementById('s-zip').value, officer_name: document.getElementById('s-officer').value };
    try {
      const res = await apiFetch('/api/company/create', { method: 'POST', body: JSON.stringify(payload) });
      COMPANY_ID = res.company_id; localStorage.setItem('tb_company_id', COMPANY_ID);
      const me = await apiFetch('/api/auth/me');
      showApp(me);
    } catch(e) { errEl.textContent = e.message || 'Error creating company.'; errEl.classList.remove('hidden'); }
  }

  function doLogout() { TOKEN = null; COMPANY_ID = null; localStorage.clear(); showAuthGate(); }

  async function apiFetch(url, opts={}) {
    const res = await fetch(url, { ...opts, headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${TOKEN}`, ...(opts.headers||{}) } });
    if (!res.ok) { 
        const e = await res.json(); 
        const msg = Array.isArray(e.detail) ? e.detail[0].msg : (e.detail || 'Request failed');
        throw new Error(msg); 
    }
    return res.json();
  }

  function switchTab(t) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.view-section').forEach(v => v.classList.remove('active'));
    document.getElementById(`tab-${t}`).classList.add('active');
    document.getElementById(`view-${t}`).classList.add('active');
  }

  async function loadAllData() {
    if (!COMPANY_ID) return;
    const dash = await apiFetch(`/api/engine/dashboard/${COMPANY_ID}`);
    const m = dash.metrics;
    document.getElementById('m-paydex').textContent = m.paydex || 'N/A';
    document.getElementById('m-experian').textContent = m.experian || 'N/A';
    document.getElementById('m-equifax').textContent = m.equifax || 'N/A';
    document.getElementById('m-credit').textContent = '$' + m.total_credit.toLocaleString();

    const t = dash.target_vendor;
    currentTargetId = t?.vendor_id || null;
    if (t) {
      document.getElementById('target-name').textContent = t.vendor_name;
      document.getElementById('target-tier').textContent = `Tier ${t.tier}`;
      document.getElementById('target-desc').textContent = t.category;
      document.getElementById('target-reports').textContent = t.reports_to;
      document.getElementById('target-min').textContent = '$' + t.min_purchase.toFixed(2);
      document.getElementById('target-pg').textContent = t.personal_guarantee ? '⚠️ Yes' : '✅ No';
      document.getElementById('target-tips').textContent = t.underwriting_tips;
      document.getElementById('btn-apply').href = t.application_url;
    }
    dossierJson = JSON.stringify(dash.autofill_payload, null, 2);
    
    // Render Fundability
    if(dash.fundability) {
        document.getElementById('fund-score').textContent = dash.fundability.score + '/100';
        document.getElementById('fund-checks').innerHTML = dash.fundability.checks.map(c => 
            `<div class="flex items-center gap-3"><i class="fa-solid ${c.pass ? 'fa-circle-check text-emerald-500' : 'fa-circle-xmark text-red-500'}"></i> <span class="text-sm ${c.pass ? 'text-slate-300' : 'text-slate-500'}">${c.label}</span></div>`
        ).join('');
    }

    // Render Chart
    if(dash.chart_data && !window.paydexChart) {
        const ctx = document.getElementById('creditChart').getContext('2d');
        window.paydexChart = new Chart(ctx, {
            type: 'line',
            data: { labels: dash.chart_data.labels, datasets: [{ label: 'PAYDEX Score', data: dash.chart_data.paydex, borderColor: '#38bdf8', backgroundColor: 'rgba(56, 189, 248, 0.1)', tension: 0.4, fill: true, borderWidth: 3 }] },
            options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { min: 0, max: 100, grid: { color: '#1e293b' } }, x: { grid: { display: false } } } }
        });
    } else if(window.paydexChart) {
        window.paydexChart.data.datasets[0].data = dash.chart_data.paydex;
        window.paydexChart.update();
    }
        
    document.getElementById('autofill-box').textContent = dossierJson;

    const port = await apiFetch(`/api/portfolio/${COMPANY_ID}`);
    try {
      const ad = await apiFetch('/api/admin/overview');
      if (ad) {
        document.getElementById('ad-users').textContent = ad.users;
        document.getElementById('ad-comps').textContent = ad.companies;
        document.getElementById('ad-trades').textContent = ad.tradelines;
        document.getElementById('ad-vendors').innerHTML = ad.vendors.map(v => `<tr class="hover:bg-slate-800/30"><td class="px-4 py-3 font-medium text-white">${v.name}</td><td class="px-4 py-3"><span class="bg-slate-800 px-2 py-0.5 rounded text-xs">Tier ${v.tier}</span></td><td class="px-4 py-3 text-xs text-slate-400">${v.category}</td></tr>`).join('');
      }
    } catch(e) {}
        
    document.getElementById('tradelines-table').innerHTML = port.tradelines.map(tr => `<tr class="hover:bg-slate-800/30"><td class="px-4 py-3 font-medium text-white">${tr.vendor}</td><td class="px-4 py-3"><span class="bg-slate-800 px-2 py-0.5 rounded text-xs">Tier ${tr.tier}</span></td><td class="px-4 py-3 text-emerald-400">$${tr.limit.toLocaleString()}</td><td class="px-4 py-3 text-xs text-slate-400">${tr.reports_to}</td></tr>`).join('');
    
document.getElementById('payments-list').innerHTML = port.recent_payments.map(p => `
    <div class="flex justify-between items-center p-3 bg-slate-950 rounded border border-slate-800">
        <div>
            <p class="text-sm font-bold text-white">${p.vendor}</p>
            <p class="text-xs text-slate-500">${p.invoice}</p>
        </div>
        <div class="text-right flex items-center gap-4">
            <div>
                <p class="text-sm text-emerald-400">$${p.amount.toFixed(2)}</p>
                <p class="text-xs text-sky-400">${p.early_days}d early</p>
            </div>
            <button onclick="downloadInvoice(${p.id})" title="Download PDF Invoice" class="text-slate-400 hover:text-indigo-400 transition"><i class="fa-solid fa-file-pdf text-xl"></i></button>
        </div>
    </div>`).join('');


    const mx = await apiFetch(`/api/vendors/matrix/${COMPANY_ID}`);
    document.getElementById('matrix-grid').innerHTML = mx.vendors.map(v => `<div class="p-4 rounded-xl border relative overflow-hidden ${v.applied ? 'bg-emerald-950/20 border-emerald-900/50' : v.locked ? 'bg-slate-950 border-slate-800 opacity-50' : 'bg-slate-900 border-slate-700'}">${v.locked ? '<div class="absolute inset-0 flex items-center justify-center z-10 backdrop-blur-[1px]"><i class="fa-solid fa-lock text-3xl text-slate-700"></i></div>' : ''}${v.applied ? '<div class="absolute top-3 right-3 text-emerald-500"><i class="fa-solid fa-circle-check"></i></div>' : ''}<span class="text-[10px] uppercase font-bold text-slate-500">Tier ${v.tier}</span><h4 class="font-bold text-white mt-1">${v.name}</h4><p class="text-xs text-slate-400 mt-1">${v.category}</p><div class="mt-3 flex flex-wrap gap-1">${v.reports_to.split(',').map(r => `<span class="px-2 py-0.5 bg-slate-800 text-[10px] rounded text-slate-300">${r.trim()}</span>`).join('')}</div></div>`).join('');
  }

  async function launchBot() {
    if (!currentTargetId) return;
    const btn = document.getElementById('btn-bot');
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Spawning Bot...';
    try { await apiFetch(`/api/engine/launch-autofill/${COMPANY_ID}/${currentTargetId}`, { method: 'POST' }); btn.innerHTML = '<i class="fa-solid fa-check"></i> Browser Launched!'; }
    catch(e) { btn.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> Error'; }
    setTimeout(() => { btn.innerHTML = '<i class="fa-solid fa-robot"></i> Launch Browser Auto-Fill Bot'; }, 3000);
  }

  async function markApplied() {
    if (!currentTargetId) return;
    await apiFetch(`/api/tradelines/link/${COMPANY_ID}`, { method: 'POST', body: JSON.stringify({ vendor_id: currentTargetId, account_number: 'APPLIED-' + Date.now(), credit_limit: 500 }) });
    loadAllData();
  }

  
  async function downloadInvoice(pid) {
    try {
      const res = await fetch(`/api/engine/generate-invoice/${pid}`, { headers: { 'Authorization': `Bearer ${TOKEN}` } });
      if (!res.ok) throw new Error('Failed to generate PDF');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const cd = res.headers.get('content-disposition');
      a.download = cd ? cd.split('filename="')[1].split('"')[0] : `Invoice_${pid}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch(e) { alert(e.message); }
  }

  function copyDossier() { navigator.clipboard.writeText(dossierJson); alert('Copied!'); }

  async function simulateMonth() {
    await apiFetch(`/api/engine/simulate-month/${COMPANY_ID}`, { method: 'POST' });
    setTimeout(loadAllData, 500);
  }
</script>
</body>
</html>"""
