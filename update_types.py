import re

credit_types_path = r'c:\Users\Darwin\pubkisher\truebuild\credit-crm\shared\types\credit.ts'

with open(credit_types_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add to EmailStage
content = content.replace(
    "| 'POST_CARE_45DAY';",
    "| 'POST_CARE_45DAY'\n  | 'LETTERS_READY'\n  | 'DISPUTE_30DAY_FOLLOWUP';"
)

with open(credit_types_path, 'w', encoding='utf-8') as f:
    f.write(content)
