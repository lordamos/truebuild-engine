import re

path = r'c:\Users\Darwin\pubkisher\truebuild\credit-crm\server\routes\clients.ts'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# For the manual run-agents route
old_route1 = """  const newDisputes = Object.values(outputs)
    .flatMap((r) => r?.letters ?? []);

  client.agentOutputs = { ...client.agentOutputs, ...outputs };
  client.disputes = [...client.disputes, ...newDisputes];
  client.stage = 'DOCS_VERIFIED';
  saveClient(client);"""

new_route1 = """  const newDisputes = Object.values(outputs)
    .flatMap((r) => r?.letters ?? []);

  client.agentOutputs = { ...client.agentOutputs, ...outputs };
  client.disputes = [...client.disputes, ...newDisputes];
  client.stage = 'DOCS_VERIFIED';
  
  if (newDisputes.length > 0) {
    const entry = await dispatchEmail(client, 'LETTERS_READY');
    client.emailLog.push(entry);
  }
  
  saveClient(client);"""

content = content.replace(old_route1, new_route1)

# For the auto-run block
old_route2 = """    runAllAgents(client).then(outputs => {
    const updated = getClientById(client.id);
    if (!updated) return;
    const newDisputes = Object.values(outputs).flatMap(r => r?.letters ?? []);
    updated.agentOutputs = { ...updated.agentOutputs, ...outputs };
    updated.disputes = [...updated.disputes, ...newDisputes];
    updated.stage = 'DOCS_VERIFIED';
    saveClient(updated);
    console.log(`[AutoAgent] ✨ All 8 agents completed for ${client.firstName} ${client.lastName}`);
  }).catch(e => console.error('[AutoAgent] Error:', e.message));"""

new_route2 = """    runAllAgents(client).then(async outputs => {
    const updated = getClientById(client.id);
    if (!updated) return;
    const newDisputes = Object.values(outputs).flatMap(r => r?.letters ?? []);
    updated.agentOutputs = { ...updated.agentOutputs, ...outputs };
    updated.disputes = [...updated.disputes, ...newDisputes];
    updated.stage = 'DOCS_VERIFIED';
    
    if (newDisputes.length > 0) {
      const entry = await dispatchEmail(updated, 'LETTERS_READY');
      updated.emailLog.push(entry);
    }
    
    saveClient(updated);
    console.log(`[AutoAgent] ✨ All 8 agents completed for ${client.firstName} ${client.lastName}`);
  }).catch(e => console.error('[AutoAgent] Error:', e.message));"""

content = content.replace(old_route2, new_route2)

# For auto-parse report
old_route3 = """  const outputs = await runAllAgents(client);
  const newDisputes = Object.values(outputs).flatMap(r => r?.letters ?? []);
  client.agentOutputs = { ...client.agentOutputs, ...outputs };
  client.disputes = [...(client.disputes ?? []), ...newDisputes];
  if (client.stage === 'NEW') client.stage = 'DOCS_VERIFIED';
  saveClient(client);"""

new_route3 = """  const outputs = await runAllAgents(client);
  const newDisputes = Object.values(outputs).flatMap(r => r?.letters ?? []);
  client.agentOutputs = { ...client.agentOutputs, ...outputs };
  client.disputes = [...(client.disputes ?? []), ...newDisputes];
  if (client.stage === 'NEW') client.stage = 'DOCS_VERIFIED';
  
  if (newDisputes.length > 0) {
    const entry = await dispatchEmail(client, 'LETTERS_READY');
    client.emailLog.push(entry);
  }
  
  saveClient(client);"""

content = content.replace(old_route3, new_route3)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
