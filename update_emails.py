import re

path = r'c:\Users\Darwin\pubkisher\truebuild\credit-crm\server\core\emailScheduler.ts'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add to the switch statement
switch_replacement = """case 'OVERDUE_48H': emailContent = buildOverdueAlertEmail(client); break;
    case 'POST_CARE_45DAY': emailContent = buildPostCareEmail(client); break;
    case 'LETTERS_READY': emailContent = buildLettersReadyEmail(client); break;
    case 'DISPUTE_30DAY_FOLLOWUP': emailContent = buildDispute30DayEmail(client); break;"""

content = re.sub(
    r"case 'OVERDUE_48H': emailContent = buildOverdueAlertEmail\(client\); break;\s*case 'POST_CARE_45DAY': emailContent = buildPostCareEmail\(client\); break;",
    switch_replacement,
    content
)

# 2. Add the builder functions and the 30-day getter
functions = """export function buildLettersReadyEmail(client: Client): { subject: string; html: string } {
  return {
    subject: `Action Required: Your Credit Dispute Letters Are Ready!`,
    html: wrapEmailHtml(`
      <span class="badge" style="background:#2563eb;">Letters Generated ✉️</span>
      <h2>Your personalized dispute letters are ready, ${client.firstName}!</h2>
      <p>Our AI engines have successfully audited your credit profile and generated legally-binding FCRA dispute letters tailored to your negative items.</p>
      
      <div class="info-box">
        <strong>📬 How to Mail Your Letters:</strong><br>
        <strong>Option A (Traditional):</strong> Log into your portal, download the letters, print them, and mail them via USPS Certified Mail (Return Receipt Requested).<br><br>
        <strong>Option B (Online/Overnight - Recommended!):</strong> You don't have to leave your house! You can upload your PDF letters directly to an online mailing platform like <strong>Mailform.io</strong> or <strong>Click2Mail</strong> to have them printed and shipped Certified Mail overnight with tracking automatically.
      </div>

      <div class="step"><strong>⏱ Next Steps:</strong><br>Please log into your portal to download your letters and mail them out. The 30-day dispute clock begins as soon as the bureaus receive them!</div>
    `, client.firstName),
  };
}

export function buildDispute30DayEmail(client: Client): { subject: string; html: string } {
  return {
    subject: `Check-in: 30 Days Since Your Dispute Letters!`,
    html: wrapEmailHtml(`
      <span class="badge yellow">30-Day Checkpoint ⏳</span>
      <h2>It's time to check your results, ${client.firstName}!</h2>
      <p>It has been roughly 30 days since your dispute letters were generated. By law (FCRA §611), the credit bureaus have 30 days to conduct their reinvestigation.</p>
      
      <div class="step"><strong>✅ What you need to do:</strong><br>You should have received responses from Equifax, Experian, and TransUnion in the mail. <strong>Please log back into your portal</strong> to update your account, or reply directly to this email with photos of the bureau responses.</div>
      
      <p>If negative items were verified instead of deleted, don't worry! We will generate your aggressive <strong>Round 2 Method of Verification</strong> letters immediately once you log back in.</p>
    `, client.firstName),
  };
}

export function getClientsNeeding30DayFollowup(clients: Client[]): Client[] {
  const now = Date.now();
  const THIRTY_DAYS = 30 * 24 * 60 * 60 * 1000;
  return clients.filter((client) => {
    // If they already got it, skip
    if (client.emailLog.some(log => log.stage === 'DISPUTE_30DAY_FOLLOWUP')) return false;

    // We check if they have a DISPUTE_LETTER agent result generated > 30 days ago
    const agentResults = client.agentResults;
    if (!agentResults) return false;
    
    // Check DISPUTE_LETTER or INQUIRY_MINIMIZER
    const disputeRes = agentResults['DISPUTE_LETTER'];
    const inquiryRes = agentResults['INQUIRY_MINIMIZER'];
    
    let earliestLetterTime = 0;
    
    if (disputeRes && disputeRes.generatedAt) {
      earliestLetterTime = new Date(disputeRes.generatedAt).getTime();
    }
    if (inquiryRes && inquiryRes.generatedAt) {
      const inqTime = new Date(inquiryRes.generatedAt).getTime();
      if (earliestLetterTime === 0 || inqTime < earliestLetterTime) earliestLetterTime = inqTime;
    }

    if (earliestLetterTime > 0 && (now - earliestLetterTime) >= THIRTY_DAYS) {
      return true;
    }
    return false;
  });
}
"""

content += "\n" + functions

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
