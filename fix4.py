with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

bad = "    try:\n        \n    try:"
content = content.replace(bad, "    try:")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
