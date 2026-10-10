import re

path = r'c:\Users\Darwin\pubkisher\truebuild\credit-crm\shared\types\credit.ts'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_meta = """export const EMAIL_STAGE_META: Record<EmailStage, { subject: string; trigger: string; icon: string }> = {
  WELCOME: { subject: 'Welcome to Your Credit Acceleration Program', trigger: 'On agreement signing', icon: '👋' },
  DOCS_VERIFIED: { subject: 'Status Update: Underwriting Package Approved', trigger: 'On docs verified', icon: '📄' },
  SUBMITTED: { subject: 'Applications Submitted - Real-Time Underwriting in Progress', trigger: 'On submission', icon: '🚀' },
  APPROVED: { subject: '🎉 CONGRATULATIONS! Your First Business Credit Facility is Approved!', trigger: 'On approval', icon: '💳' },
  PAYMENT_CONFIRMED: { subject: 'Payment Confirmed: Card Activation & 1% Utilization Guide', trigger: 'On payment received', icon: '✅' },
  OVERDUE_48H: { subject: 'URGENT NOTICE: Outstanding Success Fee - Action Required', trigger: '48hrs after approval if unpaid', icon: '⚠️' },
  POST_CARE_45DAY: { subject: '45-Day Check-In: Scaling Your Lines to $50,000+', trigger: '45 days after payment', icon: '📈' },
};"""

new_meta = """export const EMAIL_STAGE_META: Record<EmailStage, { subject: string; trigger: string; icon: string }> = {
  WELCOME: { subject: 'Welcome to Your Credit Acceleration Program', trigger: 'On agreement signing', icon: '👋' },
  DOCS_VERIFIED: { subject: 'Status Update: Underwriting Package Approved', trigger: 'On docs verified', icon: '📄' },
  SUBMITTED: { subject: 'Applications Submitted - Real-Time Underwriting in Progress', trigger: 'On submission', icon: '🚀' },
  APPROVED: { subject: '🎉 CONGRATULATIONS! Your First Business Credit Facility is Approved!', trigger: 'On approval', icon: '💳' },
  PAYMENT_CONFIRMED: { subject: 'Payment Confirmed: Card Activation & 1% Utilization Guide', trigger: 'On payment received', icon: '✅' },
  OVERDUE_48H: { subject: 'URGENT NOTICE: Outstanding Success Fee - Action Required', trigger: '48hrs after approval if unpaid', icon: '⚠️' },
  POST_CARE_45DAY: { subject: '45-Day Check-In: Scaling Your Lines to $50,000+', trigger: '45 days after payment', icon: '📈' },
  LETTERS_READY: { subject: 'Action Required: Your Credit Dispute Letters Are Ready!', trigger: 'On generation', icon: '✉️' },
  DISPUTE_30DAY_FOLLOWUP: { subject: 'Check-in: 30 Days Since Your Dispute Letters!', trigger: '30 days after generation', icon: '⏳' },
};"""

content = content.replace(old_meta, new_meta)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
