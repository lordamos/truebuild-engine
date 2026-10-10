import re

target_file = r'c:\Users\Darwin\pubkisher\truebuild\credit-crm\server\core\agentRunner.ts'

with open(target_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the dispute items filter
old_filter = r"const disputeItems = profile\.negativeItems\.filter\(i =>\s*i\.disputeStrategy === 'FORMAL_FCRA' \|\| i\.disputeStrategy === 'DEBT_VALIDATION'\s*\);"
new_filter = r"const disputeItems = profile.negativeItems.filter(i => i.type !== 'INQUIRY');"

content = re.sub(old_filter, new_filter, content)

with open(target_file, 'w', encoding='utf-8') as f:
    f.write(content)
