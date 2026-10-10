import re

path = r'c:\Users\Darwin\pubkisher\truebuild\app.py'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

endpoint = """@app.get("/api/engine/funding-matches", tags=["Engine"])
async def get_funding_matches(db: Session = Depends(get_db)):
    user = db.query(User).first()
    dossier = db.query(CompanyDossier).filter(CompanyDossier.user_id == user.id).first()
    
    paydex = 0
    if dossier and dossier.duns_number:
        # Simulate paydex based on tradelines
        tradelines = db.query(Tradeline).filter(Tradeline.company_id == dossier.id).all()
        if len(tradelines) > 2:
            paydex = min(100, 40 + (len(tradelines) * 10))
    
    fundability_score = 0
    if dossier:
        if dossier.ein: fundability_score += 20
        if dossier.duns_number: fundability_score += 20
        if dossier.business_phone: fundability_score += 20
        if dossier.website: fundability_score += 20
        if dossier.business_email and not dossier.business_email.endswith('@gmail.com'): fundability_score += 20
    
    matches = []
    
    # Tier 1: Microloans
    matches.append({
        "name": "Kiva Business Microloan",
        "type": "0% Interest Crowd-Lending",
        "amount": "$15,000",
        "odds": "High" if fundability_score >= 60 else "Low",
        "requirements": "Basic Fundability (EIN, Website)",
        "icon": "fa-seedling"
    })
    
    # Tier 2: Revenue Based
    matches.append({
        "name": "Fundbox Line of Credit",
        "type": "Revolving Business Credit",
        "amount": "$50,000",
        "odds": "High" if paydex >= 60 else "Medium",
        "requirements": "PAYDEX 60+, 3+ Months Time in Business",
        "icon": "fa-money-bill-trend-up"
    })
    
    # Tier 3: SBA / Bank Term Loans
    matches.append({
        "name": "SBA 7(a) Express Loan",
        "type": "Federal Backed Term Loan",
        "amount": "$350,000",
        "odds": "High" if paydex >= 80 and fundability_score == 100 else "Low",
        "requirements": "PAYDEX 80+, Perfect Fundability",
        "icon": "fa-building-columns"
    })
    
    return {"paydex": paydex, "fundability": fundability_score, "matches": matches}

"""

# Insert right before @app.get("/api/admin/overview"
content = content.replace('@app.get("/api/admin/overview"', endpoint + '\n@app.get("/api/admin/overview"')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
