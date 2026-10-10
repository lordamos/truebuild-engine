import re
import os

target_file = r'c:\Users\Darwin\pubkisher\truebuild\credit-crm\server\core\agentRunner.ts'

with open(target_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Using regex to replace the function
pattern = r"function runInquiryMinimizer\(client: Client, profile: CreditProfile\): AgentResult \{[\s\S]*?return \{\s*agentId: 'INQUIRY_MINIMIZER',[\s\S]*?\}\s*\;\s*\}"

new_func = """function runInquiryMinimizer(client: Client, profile: CreditProfile): AgentResult {
  const inquiries = profile.negativeItems.filter(i => i.type === 'INQUIRY');
  
  // Find accounts attached to these inquiries
  const accountCreditors = new Set([
    ...profile.debtAccounts.map(d => d.creditor.toLowerCase()),
    ...profile.negativeItems.filter(n => n.type !== 'INQUIRY').map(n => n.creditor.toLowerCase())
  ]);

  const unattachedInquiries = inquiries.filter(i => {
    return !Array.from(accountCreditors).some(ac => ac.includes(i.creditor.toLowerCase()) || i.creditor.toLowerCase().includes(ac));
  });

  const attachedInquiries = inquiries.filter(i => !unattachedInquiries.includes(i));

  const letters: DisputeLetter[] = unattachedInquiries.map(inq => ({
    id: uuidv4(),
    clientId: client.id,
    type: 'FCRA_FORMAL_DISPUTE',
    bureau: inq.bureau as any,
    creditor: inq.creditor,
    status: 'DRAFT',
    createdAt: new Date().toISOString(),
    content: `[Your Name]\\n[Your Address]\\n[City, State, Zip]\\n\\nDate: ${new Date().toLocaleDateString()}\\n\\nTo: ${inq.bureau} Credit Bureau\\n\\nSubject: Dispute of Unauthorized Hard Inquiry - FCRA Section 604 Violation\\n\\nTo Whom It May Concern,\\n\\nI am writing to formally dispute a hard inquiry on my credit report from ${inq.creditor} dated ${inq.dateOpened || 'Unknown Date'}. I have no open or closed account with this institution, nor did I apply for credit or provide permissible purpose under Section 604 of the Fair Credit Reporting Act (FCRA).\\n\\nPlease provide proof of signed authorization bearing my physical signature. If you cannot produce this documentation within 30 days, as required by law, this inquiry must be permanently removed from my credit file.\\n\\nThank you,\\n\\n${client.firstName} ${client.lastName}`
  }));

  const output = `# 🕵️ Hard Inquiry Minimizer & Smart Application Strategy
**Total Inquiries Found:** ${inquiries.length}
**Unattached Inquiries (Disputable):** ${unattachedInquiries.length}

---

## 🚨 Unattached Inquiries Detected
*The following inquiries do not match any open or closed accounts on your profile. Under FCRA §604, inquiries without a permissible purpose or an associated account application are highly disputable and must be removed if the creditor cannot prove authorization.*

${unattachedInquiries.length === 0 ? '✅ Excellent. No unattached inquiries found.' : unattachedInquiries.map(i => `- **${i.creditor}** (${i.bureau}) - ${i.dateOpened ?? 'Date unknown'} 🛑 **FLAGGED FOR DISPUTE**`).join('\\n')}

---

## 📎 Attached Inquiries
*These inquiries correspond to existing accounts on your file. Disputing them is generally unsuccessful and could risk the associated account being closed.*

${attachedInquiries.length === 0 ? '*None.*' : attachedInquiries.map(i => `- **${i.creditor}** (${i.bureau}) - ${i.dateOpened ?? 'Date unknown'}`).join('\\n')}

---

## ⚖️ Dispute Unauthorized Inquiries
We have automatically generated **${letters.length} FCRA §604 Dispute Letter(s)** for your unattached inquiries. 
These are available in your Letters tab and demand proof of signed authorization.

---

## Future Application Strategy (Rate Shopping Protection)
### The 14-45 Day Rate Shopping Window
- When shopping for a mortgage, auto loan, or student loan - apply to ALL lenders within a **14-day window**.
- FICO 8 and VantageScore 3.0/4.0 will count these as **1 inquiry** instead of multiple.
- For credit cards, each application IS a separate inquiry (no bundling).

### The Application Pre-Qualification Hack
- ALWAYS use lenders' pre-qualification tools (soft pull only) before formally applying.
- Pre-qualifications are NOT hard inquiries and show you your likely approval odds risk-free.
`;

  return {
    agentId: 'INQUIRY_MINIMIZER',
    status: 'COMPLETE',
    title: 'Inquiry Minimizer & Disputer',
    output,
    generatedAt: new Date().toISOString(),
    letters: letters.length > 0 ? letters : undefined
  };
}"""

content = re.sub(pattern, new_func, content)

with open(target_file, 'w', encoding='utf-8') as f:
    f.write(content)
