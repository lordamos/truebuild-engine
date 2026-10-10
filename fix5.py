with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

bad = """    if db.query(Vendor).count() == 0:"""
good = """    try:
        if db.query(Vendor).count() == 0:"""

content = content.replace(bad, good)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
