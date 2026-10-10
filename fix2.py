import os

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

bad_block = """    try:
        
    try:
        db.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;"))
        db.commit()
    except Exception:
        db.rollback()
        if db.query(Vendor).count() == 0:"""

good_block = """    try:
        db.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;"))
        db.commit()
    except Exception:
        db.rollback()
    
    try:
        if db.query(Vendor).count() == 0:"""

content = content.replace(bad_block, good_block)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
