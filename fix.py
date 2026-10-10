with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.strip() == 'try:':
        new_lines.append('    try:\n')
    elif line.strip() == 'db.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;"))':
        new_lines.append('        db.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;"))\n')
    elif line.strip() == 'db.commit()':
        new_lines.append('        db.commit()\n')
    elif line.strip() == 'except Exception:':
        new_lines.append('    except Exception:\n')
    elif line.strip() == 'db.rollback()':
        new_lines.append('        db.rollback()\n')
    else:
        new_lines.append(line)

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
