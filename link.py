with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

bad = '<button onclick="switchTab(\'portfolio\')" id="tab-portfolio"'
good = '<a href="http://localhost:3002" target="_blank" class="tab-btn w-full text-left px-4 py-3 rounded-lg text-sm font-medium text-emerald-400 hover:text-emerald-300 transition flex items-center gap-3 mt-8"><i class="fa-solid fa-users-viewfinder w-4"></i> Personal Credit CRM <i class="fa-solid fa-arrow-up-right-from-square text-xs ml-auto"></i></a>\n      <button onclick="switchTab(\'portfolio\')" id="tab-portfolio"'

content = content.replace(bad, good)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
