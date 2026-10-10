import re

path = r'c:\Users\Darwin\pubkisher\truebuild\credit-crm\server\index.ts'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update imports
old_import = "import { getClientsNeedingOverdueAlert, getClientsNeedingPostCare, dispatchEmail } from './core/emailScheduler.js';"
new_import = "import { getClientsNeedingOverdueAlert, getClientsNeedingPostCare, getClientsNeeding30DayFollowup, dispatchEmail } from './core/emailScheduler.js';"
content = content.replace(old_import, new_import)

# 2. Update setInterval
old_interval = """      const clients = getAllClients();
      const overdue = getClientsNeedingOverdueAlert(clients);
      const postCare = getClientsNeedingPostCare(clients);"""

new_interval = """      const clients = getAllClients();
      const overdue = getClientsNeedingOverdueAlert(clients);
      const postCare = getClientsNeedingPostCare(clients);
      const followUp30 = getClientsNeeding30DayFollowup(clients);"""
content = content.replace(old_interval, new_interval)

# 3. Add loop
old_post_loop = """      for (const client of postCare) {
        const entry = await dispatchEmail(client, 'POST_CARE_45DAY');
        client.emailLog.push(entry);
        saveClient(client);
        console.log(`[Scheduler] ✉️ Post-care email sent -> ${client.email}`);
      }"""

new_post_loop = """      for (const client of postCare) {
        const entry = await dispatchEmail(client, 'POST_CARE_45DAY');
        client.emailLog.push(entry);
        saveClient(client);
        console.log(`[Scheduler] ✉️ Post-care email sent -> ${client.email}`);
      }
      for (const client of followUp30) {
        const entry = await dispatchEmail(client, 'DISPUTE_30DAY_FOLLOWUP');
        client.emailLog.push(entry);
        saveClient(client);
        console.log(`[Scheduler] ✉️ 30-Day Follow-Up email sent -> ${client.email}`);
      }"""
content = content.replace(old_post_loop, new_post_loop)


with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
