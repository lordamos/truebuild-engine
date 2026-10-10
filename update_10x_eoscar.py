import re

path = r'c:\Users\Darwin\pubkisher\truebuild\credit-crm\server\core\agentRunner.ts'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace runDisputeLetterFactory
pattern = r"function runDisputeLetterFactory\(client: Client, profile: CreditProfile\): AgentResult \{[\s\S]*?return \{\s*agentId: 'DISPUTE_LETTER',[\s\S]*?\}\s*\;\s*\}"

new_func = """function runDisputeLetterFactory(client: Client, profile: CreditProfile): AgentResult {
  const today = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
  const disputeItems = profile.negativeItems.filter(i => i.type !== 'INQUIRY');

  const letters: DisputeLetter[] = [];

  // e-OSCAR OCR Bypass Spintax Engine
  const introVariations = [
    "I am writing to formally dispute the following item(s) appearing on my consumer credit file, which I have reviewed and determined to be inaccurate, unverifiable, and/or reported in violation of the Fair Credit Reporting Act.",
    "After reviewing my credit report, I have identified the following accounts as inaccurate or unverified. I am requesting an immediate reinvestigation pursuant to my rights under the FCRA.",
    "This letter serves as a formal dispute regarding erroneous and unverifiable trade lines currently reporting on my credit file. I demand a full investigation into these inaccuracies.",
    "I have recently pulled my credit report and found severely inaccurate information. Please investigate the following items immediately as required by federal law."
  ];

  const demandVariations = [
    "Under FCRA §611(a), you are required to conduct a reasonable reinvestigation of this item. I demand you provide the complete METHOD OF VERIFICATION.",
    "I require that you investigate this item under 15 U.S.C. §1681i. If this account cannot be 100% verified with the original furnisher, it must be deleted.",
    "Pursuant to the Fair Credit Reporting Act, I demand proof of this alleged debt and the complete method used to verify it. If unverified, delete it immediately.",
    "By law, you must verify the accuracy of this account. Failure to provide strict proof of verification will require permanent removal from my credit report."
  ];

  const signoffVariations = [
    "I will not accept an unverified 're-verification' as satisfactory resolution.",
    "Govern yourself accordingly. I expect a response within 30 days.",
    "Failure to comply with these federal guidelines will result in complaints to the CFPB.",
    "I look forward to receiving an updated copy of my credit report showing these deletions."
  ];

  // Group by bureau
  const bureaus = ['Equifax', 'Experian', 'TransUnion'] as const;
  for (const bureau of bureaus) {
    const bureauItems = disputeItems.filter(i => i.bureau.includes(bureau));
    if (bureauItems.length === 0) continue;

    const deadline = new Date();
    deadline.setDate(deadline.getDate() + 37); // 30 days + 7 days for mail delivery

    // Randomize per bureau to defeat e-OSCAR cross-referencing
    const rIntro = introVariations[Math.floor(Math.random() * introVariations.length)];
    const rSignoff = signoffVariations[Math.floor(Math.random() * signoffVariations.length)];

    const letterContent = `${today}

${client.firstName} ${client.lastName}
${client.address}, ${client.city}, ${client.state} ${client.zip}
SSN: XXX-XX-XXXX (Last 4: XXXX)
Date of Birth: XX/XX/XXXX

${bureau} Information Services
${bureau === 'Equifax' ? 'P.O. Box 740256\\nAtlanta, GA 30374' :
  bureau === 'Experian' ? 'P.O. Box 4500\\nAllen, TX 75013' :
  'P.O. Box 2000\\nChester, PA 19016'}

Re: Formal Request to Investigate & Remove Inaccurate / Unverifiable Credit Information
Pursuant to: Fair Credit Reporting Act (FCRA) 15 U.S.C. § 1681 et seq., § 611, § 623

To Whom It May Concern at ${bureau}:

${rIntro}

DISPUTED ITEMS:

${bureauItems.map((item, i) => {
   const rDemand = demandVariations[Math.floor(Math.random() * demandVariations.length)];
   return `${i + 1}. CREDITOR/FURNISHER: ${item.creditor}
   Account Number: ${item.accountNumber ?? 'Unknown'}
   Type: ${item.type.replace(/_/g, ' ')}
   
   BASIS FOR DISPUTE: This account is disputed as inaccurate, incomplete, and/or unverifiable. The reported information contains material errors and/or cannot be verified to comply with Metro 2 reporting standards. Specifically, I dispute the accuracy of the payment history, high balance, and Date of First Delinquency.
   
   LEGAL DEMAND: ${rDemand}`;
}).join('\\n\\n')}

LEGAL NOTICE & DEMAND FOR ACTION:

Pursuant to the Fair Credit Reporting Act, 15 U.S.C. § 1681i, you are hereby required to:
1. Conduct a REASONABLE REINVESTIGATION of the above-listed disputed information within THIRTY (30) DAYS.
2. If you are UNABLE TO FULLY VERIFY each element, you are LEGALLY REQUIRED to PERMANENTLY DELETE the disputed item(s) under FCRA § 611(a)(5)(A).

PLEASE BE ADVISED that I am aware of my rights under FCRA § 611, § 623, § 616, and § 617.
${rSignoff}

Sincerely,

________________________________
${client.firstName} ${client.lastName}

Enclosures:
- Copy of Government-Issued Photo ID
- Copy of Social Security Card
- Copy of Proof of Address`;

    letters.push({
      id: uuidv4(),
      clientId: client.id,
      type: 'FCRA_FORMAL_DISPUTE',
      bureau,
      content: letterContent,
      status: 'DRAFT',
      deadline: deadline.toISOString(),
      createdAt: new Date().toISOString(),
    });
  }

  const output = `# ⚖️ e-OSCAR Bypass Dispute Engine
**Generated:** ${new Date().toLocaleDateString()}
**Letters Created:** ${letters.length} (AI Spintax Applied)
**30-Day FCRA Deadline:** ~${new Date(Date.now() + 37 * 24 * 60 * 60 * 1000).toLocaleDateString()}

${letters.length === 0 ? '✅ No items requiring formal FCRA dispute identified.' : `
## Letters Generated:
${letters.map((l, i) => `${i + 1}. **${l.bureau}** - ${disputeItems.filter(i => i.bureau.includes(l.bureau!)).length} item(s) disputed (100% Unique OCR Hash)`).join('\\n')}

## Critical Mailing Instructions:

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

*Note: Your 30-day countdown begins the day the tracking number shows "Delivered" at the credit bureau. We will automatically send you a 30-Day Follow-Up email!*`}
`;

  return {
    agentId: 'DISPUTE_LETTER',
    status: 'COMPLETE',
    title: 'e-OSCAR Bypass Dispute Engine',
    output,
    generatedAt: new Date().toISOString(),
    letters: letters.length > 0 ? letters : undefined
  };
}"""

content = re.sub(pattern, new_func, content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
