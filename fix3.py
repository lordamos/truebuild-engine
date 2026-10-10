with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

bad = """    try:
        db.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;"))
        db.commit()
    except Exception:
        db.rollback()
        if db.query(Vendor).count() == 0:"""

good = """    try:
        db.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;"))
        db.commit()
    except Exception:
        db.rollback()
    
    if db.query(Vendor).count() == 0:"""

content = content.replace(bad, good)
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
