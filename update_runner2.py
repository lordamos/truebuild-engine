import re

path = r'c:\Users\Darwin\pubkisher\truebuild\credit-crm\server\core\agentRunner.ts'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_text = r"""## Critical Mailing Instructions:
  1. **Print** each letter and sign by hand.
  2. **Mail via USPS Certified Mail with Return Receipt Requested** (green card).
  3. **Keep the USPS tracking number** - this is your legal proof of delivery.
  4. **Start your 30-day countdown** from the date the bureau receives the letter (check tracking).
  5. **Attach enclosures** - ID, SSN doc, proof of address."""

new_text = r"""## Critical Mailing Instructions:

**✅ Option A: Online Overnight Mailing (RECOMMENDED)**
Skip the post office entirely. You can upload the PDFs of these letters directly to online mailrooms like [Mailform.io](https://www.mailform.io) or [Click2Mail](https://click2mail.com).
1. Upload the PDF.
2. Select **USPS Certified Mail**.
3. Select **Return Receipt Electronic (RRE)** or **Overnight Delivery**.
4. They will print, stuff, and mail the letters for you!

**📫 Option B: Traditional USPS Mailing**
1. **Print** each letter and sign by hand.
2. **Mail via USPS Certified Mail with Return Receipt Requested** (green card).
3. **Keep the USPS tracking number** - this is your legal proof of delivery.
4. **Attach enclosures** - ID, SSN doc, proof of address.

*Note: Your 30-day countdown begins the day the tracking number shows "Delivered" at the credit bureau. We will automatically send you a 30-Day Follow-Up email!*"""

content = content.replace(old_text, new_text)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
