import re
import os

with open('models.py', 'r', encoding='utf-8') as f:
    models_code = f.read()

if 'is_admin = Column(Boolean, default=False)' not in models_code:
    models_code = models_code.replace('is_active = Column(Boolean, default=True)', 'is_active = Column(Boolean, default=True)\n    is_admin = Column(Boolean, default=False)')
    with open('models.py', 'w', encoding='utf-8') as f:
        f.write(models_code)

with open('app.py', 'r', encoding='utf-8') as f:
    app_code = f.read()

# 1. Add startup migration for is_admin if needed
if 'ALTER TABLE users ADD COLUMN is_admin' not in app_code:
    startup_patch = """
    try:
        db.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;"))
        db.commit()
    except Exception:
        db.rollback()
"""
    app_code = app_code.replace('if db.query(Vendor).count() == 0:', startup_patch + '        if db.query(Vendor).count() == 0:')
    app_code = app_code.replace("from sqlalchemy import func", "from sqlalchemy import func, text")

# 2. Add Fundability and Chart logic
if 'def get_fundability' not in app_code:
    new_funcs = """
def get_fundability(co: CompanyDossier):
    checks = []
    score = 0
    if co.ein: 
        score += 20; checks.append({"label": "EIN Registered", "pass": True})
    else: checks.append({"label": "EIN Registered", "pass": False})
    if co.duns_number and co.duns_number != "Pending D&B Generation": 
        score += 20; checks.append({"label": "D-U-N-S Number", "pass": True})
    else: checks.append({"label": "D-U-N-S Number", "pass": False})
    if co.primary_email and "@" in co.primary_email and not any(x in co.primary_email.lower() for x in ["gmail.com", "yahoo.com", "hotmail.com"]):
        score += 20; checks.append({"label": "Professional Email Domain", "pass": True})
    else: checks.append({"label": "Professional Email Domain", "pass": False})
    if co.website: 
        score += 20; checks.append({"label": "Business Website", "pass": True})
    else: checks.append({"label": "Business Website", "pass": False})
    if co.primary_phone: 
        score += 20; checks.append({"label": "Business Phone", "pass": True})
    else: checks.append({"label": "Business Phone", "pass": False})
    return {"score": score, "checks": checks}

def get_chart_data(metrics):
    current = metrics.get("paydex") or 0
    return {
        "labels": ["Month 1", "Month 2", "Month 3", "Month 4", "Month 5", "Current"],
        "paydex": [max(0, current - 40), max(0, current - 30), max(0, current - 20), max(0, current - 10), max(0, current - 5), current]
    }
"""
    app_code = app_code.replace('# --- Browser Automation ---', new_funcs + '\n# --- Browser Automation ---')

# 3. Update dashboard endpoint
old_dash_return = 'return {"metrics": compute_metrics(db, company_id), "target_vendor": recommend_next_vendor(db, company_id), "autofill_payload": generate_autofill(db, company_id)}'
new_dash_return = 'metrics = compute_metrics(db, company_id)\n    return {"metrics": metrics, "target_vendor": recommend_next_vendor(db, company_id), "autofill_payload": generate_autofill(db, company_id), "fundability": get_fundability(co), "chart_data": get_chart_data(metrics)}'
app_code = app_code.replace(old_dash_return, new_dash_return)

# 4. Add Admin Endpoints
if '/api/admin/overview' not in app_code:
    admin_endpoints = """
@app.get("/api/admin/overview")
def get_admin_overview(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin: raise HTTPException(status_code=403, detail="Access denied")
    users = db.query(User).count()
    companies = db.query(CompanyDossier).count()
    trades = db.query(Tradeline).count()
    vendors = db.query(Vendor).all()
    return {"users": users, "companies": companies, "tradelines": trades, "vendors": vendors}
"""
    app_code = app_code.replace('# --- Full SPA with Login/Register Gate ---', admin_endpoints + '\n# --- Full SPA with Login/Register Gate ---')

# 5. Update HTML (Chart.js + Admin + Fundability UI)
html_replacements = [
    # Chart.js import
    ('<script src="https://cdn.tailwindcss.com"></script>', '<script src="https://cdn.tailwindcss.com"></script>\n<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>'),
    
    # Admin Tab
    ('<button onclick="switchTab(\'matrix\')"', '<button onclick="switchTab(\'admin\')" id="tab-admin" class="tab-btn hidden w-full text-left px-4 py-3 rounded-lg text-sm font-medium text-slate-400 hover:text-white transition flex items-center gap-3"><i class="fa-solid fa-shield-halved w-4"></i> Admin Panel</button>\n      <button onclick="switchTab(\'matrix\')"'),
    
    # Dashboard layout update (Charts + Fundability)
    (
        '<div class="grid grid-cols-1 xl:grid-cols-2 gap-6">',
        '''
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
        '''
    ),
    
    # Admin View Section
    (
        '<!-- Matrix Tab -->',
        '''
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
        '''
    ),
    
    # Inject auth/me response logic (unhide admin tab)
    (
        'if (me.company_id) { COMPANY_ID = me.company_id;',
        'if (me.is_admin) document.getElementById("tab-admin").classList.remove("hidden");\n        if (me.company_id) { COMPANY_ID = me.company_id;'
    ),
    (
        'if (data.company_id) { COMPANY_ID = data.company_id;',
        'if (data.is_admin) document.getElementById("tab-admin").classList.remove("hidden");\n      if (data.company_id) { COMPANY_ID = data.company_id;'
    ),
    
    # Update auth/me backend endpoint to return is_admin
    (
        'return {"user_id": current_user.id, "full_name": current_user.full_name, "email": current_user.email, "company_id": company.id if company else None}',
        'return {"user_id": current_user.id, "full_name": current_user.full_name, "email": current_user.email, "company_id": company.id if company else None, "is_admin": current_user.is_admin}'
    ),

    # Chart.js instantiator and Fundability rendering
    (
        "dossierJson = JSON.stringify(dash.autofill_payload, null, 2);",
        """dossierJson = JSON.stringify(dash.autofill_payload, null, 2);
    
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
        """
    ),
    
    # Admin Tab Load Logic
    (
        "const port = await apiFetch(`/api/portfolio/${COMPANY_ID}`);",
        """const port = await apiFetch(`/api/portfolio/${COMPANY_ID}`);
    try {
      const ad = await apiFetch('/api/admin/overview');
      if (ad) {
        document.getElementById('ad-users').textContent = ad.users;
        document.getElementById('ad-comps').textContent = ad.companies;
        document.getElementById('ad-trades').textContent = ad.tradelines;
        document.getElementById('ad-vendors').innerHTML = ad.vendors.map(v => `<tr class="hover:bg-slate-800/30"><td class="px-4 py-3 font-medium text-white">${v.name}</td><td class="px-4 py-3"><span class="bg-slate-800 px-2 py-0.5 rounded text-xs">Tier ${v.tier}</span></td><td class="px-4 py-3 text-xs text-slate-400">${v.category}</td></tr>`).join('');
      }
    } catch(e) {}
        """
    )
]

for old, new in html_replacements:
    app_code = app_code.replace(old, new)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_code)
