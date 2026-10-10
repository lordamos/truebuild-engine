import re

path = r'c:\Users\Darwin\pubkisher\truebuild\credit-crm\server\core\agentRunner.ts'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add online mailing string to dispute letter factory output
old_output = """  const output = `# ⚖️ FCRA Dispute Letter Factory
**Generated:** ${new Date().toLocaleDateString()}
**Disputed Items:** ${disputeItems.length}

---

## 🖨️ Instructions for Mailing
1. Print each letter on standard 8.5x11 paper.
2. Attach a copy of your State ID and Social Security Card.
3. Attach a copy of a recent utility bill (proof of address).
4. Mail via **USPS Certified Mail - Return Receipt Requested**.
5. Keep the green tracking card for your records."""

new_output = """  const output = `# ⚖️ FCRA Dispute Letter Factory
**Generated:** ${new Date().toLocaleDateString()}
**Disputed Items:** ${disputeItems.length}

---

## 🖨️ Instructions for Mailing

**✅ Option A: Online Overnight Mailing (RECOMMENDED)**
Skip the post office entirely. You can upload the PDFs of these letters directly to online mailrooms like [Mailform.io](https://www.mailform.io) or [Click2Mail](https://click2mail.com).
1. Upload the PDF.
2. Select **USPS Certified Mail**.
3. Select **Return Receipt Electronic (RRE)** or **Overnight Delivery**.
4. They will print, stuff, and mail the letters for you!

**📫 Option B: Traditional USPS Mailing**
1. Print each letter on standard 8.5x11 paper.
2. Attach a copy of your State ID, SSN Card, and utility bill.
3. Take it to the post office and request **USPS Certified Mail - Return Receipt Requested**.
4. Keep the green tracking card for your legal records.

---

*Note: Your 30-day countdown begins the day the tracking number shows "Delivered" at the credit bureau. We will automatically send you a 30-Day Follow-Up email!*"""

content = content.replace(old_output, new_output)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
