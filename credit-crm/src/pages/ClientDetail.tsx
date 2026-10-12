import React, { useEffect, useState } from 'react';
import type { Client, AgentId, PipelineStage, EmailStage } from '../types/credit';
import { PIPELINE_STAGES, AGENT_META, EMAIL_STAGE_META } from '../types/credit';
import type { Page } from '../App';
import { AutoRepairEngine } from '../components/AutoRepairEngine';
import { 
  ArrowLeft, 
  Bot, 
  FileText, 
  Mail, 
  Scale, 
  Wrench, 
  Sparkles, 
  CheckCircle2, 
  Clock, 
  Printer, 
  Copy, 
  ChevronRight, 
  ShieldCheck, 
  DollarSign, 
  Layers, 
  Send, 
  RefreshCw,
  TrendingUp,
  AlertCircle,
  FileCheck2,
  Check
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API = 'http://localhost:3002/api';

const STAGE_ORDER: PipelineStage[] = ['NEW', 'DOCS_VERIFIED', 'SUBMITTED', 'APPROVED', 'INVOICE_SENT', 'PAID', 'DISPUTE_ACTIVE', 'POST_CARE'];
const AGENT_ORDER: AgentId[] = ['COMPREHENSIVE_AUDIT', 'ROADMAP_90_DAY', 'DEBT_OPTIMIZER', 'DISPUTE_LETTER', 'GOODWILL_LETTER', 'INQUIRY_MINIMIZER', 'SECONDARY_FREEZE', 'CREDIT_GROWTH'];
const EMAIL_STAGES: EmailStage[] = ['WELCOME', 'DOCS_VERIFIED', 'SUBMITTED', 'APPROVED', 'PAYMENT_CONFIRMED', 'OVERDUE_48H', 'POST_CARE_45DAY'];

interface Props { clientId: string; navigate: (p: Page) => void; }

type Tab = 'overview' | 'repair' | 'agents' | 'emails' | 'disputes' | 'agreement';

function renderMarkdown(text: string): string {
  return text
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/^---$/gm, '<hr>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>\n?)+/g, (m) => `<ul>${m}</ul>`)
    .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/^(.+)$/gm, (line) => {
      if (line.startsWith('<')) return line;
      return `<p>${line}</p>`;
    });
}

function buildAgreement(client: Client): string {
  const today = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
  const planA = client.plan === 'A';
  return `
    <div style="font-family: Georgia, serif; max-width:740px; margin:0 auto; padding:40px; color:#1a1a2e; line-height:1.7; background:#fff;">
      <div style="text-align:center; border-bottom:3px solid #1d4ed8; padding-bottom:24px; margin-bottom:32px;">
        <h1 style="font-size:22px; margin:0; color:#1d4ed8; letter-spacing:-0.5px;">PERSONAL GUARANTOR & CREDIT CONSULTING SERVICES AGREEMENT</h1>
        <p style="margin:8px 0 0; color:#666; font-size:14px;">Credit Acceleration Services · Palm Bay, Brevard County, Florida</p>
      </div>
      <p><strong>Effective Date:</strong> ${today}</p>
      <p><strong>SERVICE PROVIDER / GUARANTOR:</strong> Credit Acceleration Services, Palm Bay, Brevard County, Florida</p>
      <p><strong>CLIENT / COMPANY:</strong> ${client.firstName} ${client.lastName}${client.companyName ? ` / ${client.companyName}` : ''} · ${client.email} · ${client.phone}</p>
      <hr style="border:none;border-top:1px solid #ddd;margin:24px 0;">
      <h2 style="font-size:16px; color:#1d4ed8;">1. SCOPE OF SERVICES</h2>
      <p>Provider agrees to provide personal credit profile authorization, co-signing support, and business credit consulting services required to facilitate commercial credit card and/or credit facility applications.</p>
      <h2 style="font-size:16px; color:#1d4ed8;">2. FEE STRUCTURE (SELECTED PLAN)</h2>
      ${planA
    ? `<div style="background:#f0f7ff;border-left:4px solid #1d4ed8;padding:16px;border-radius:4px;">
           <strong>OPTION A – STANDARD PLAN</strong><br>
           Upfront Retainer: <strong>$250.00 USD</strong> (non-refundable, due upon signing)<br>
           Success Fee: <strong>$1,000.00 USD</strong> upon first credit approval<br>
           <strong>Total: $1,250.00 USD</strong>
         </div>`
    : `<div style="background:#f5f0ff;border-left:4px solid #7c3aed;padding:16px;border-radius:4px;">
           <strong>OPTION B – DEFERRED PLAN</strong><br>
           Upfront Retainer: <strong>$0.00 USD</strong><br>
           Success Fee: <strong>$1,500.00 USD</strong> upon first credit approval<br>
           <strong>Total: $1,500.00 USD</strong>
         </div>`}
      <h2 style="font-size:16px; color:#1d4ed8; margin-top:24px;">3. PAYMENT TERMS</h2>
      <p>Success Fee becomes due immediately upon receipt of credit approval notification and must be remitted within three business days.</p>
      <h2 style="font-size:16px; color:#1d4ed8;">4. JURISDICTION & GOVERNING LAW</h2>
      <p>This Agreement is governed by the laws of the State of Florida with exclusive venue in Brevard County, Florida.</p>
      <hr style="border:none;border-top:1px solid #ddd;margin:32px 0;">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:40px;">
        <div>
          <p><strong>PROVIDER / GUARANTOR:</strong></p>
          <p style="border-bottom:1px solid #333;padding-bottom:8px;margin-bottom:4px;">&nbsp;</p>
          <p style="font-size:12px;color:#666;">Authorized Officer</p>
          <p>Credit Acceleration Services<br>Palm Bay, FL 32905</p>
        </div>
        <div>
          <p><strong>CLIENT / GUARANTOR:</strong></p>
          <p style="border-bottom:1px solid #333;padding-bottom:8px;margin-bottom:4px;">&nbsp;</p>
          <p style="font-size:12px;color:#666;">Signature / Date</p>
          <p>${client.firstName} ${client.lastName}<br>${client.companyName || ''}</p>
        </div>
      </div>
    </div>`;
}

export function ClientDetail({ clientId, navigate }: Props) {
  const [client, setClient] = useState<Client | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<Tab>('overview');
  const [runningAgents, setRunningAgents] = useState(false);
  const [advancingStage, setAdvancingStage] = useState(false);
  const [sendingEmail, setSendingEmail] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<AgentId | null>(null);
  const [copiedLink, setCopiedLink] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/clients/${clientId}`);
      const json = await res.json();
      setClient(json.data);
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [clientId]);

  const runAgents = async () => {
    setRunningAgents(true);
    await fetch(`${API}/clients/${clientId}/run-agents`, { method: 'POST' });
    await load();
    setRunningAgents(false);
    setTab('agents');
  };

  const advanceStage = async () => {
    setAdvancingStage(true);
    await fetch(`${API}/clients/${clientId}/advance`, { 
      method: 'POST', 
      headers: { 'Content-Type': 'application/json' }, 
      body: JSON.stringify({}) 
    });
    await load();
    setAdvancingStage(false);
  };

  const sendEmail = async (stage: EmailStage) => {
    setSendingEmail(stage);
    await fetch(`${API}/clients/${clientId}/send-email`, { 
      method: 'POST', 
      headers: { 'Content-Type': 'application/json' }, 
      body: JSON.stringify({ stage }) 
    });
    await load();
    setSendingEmail(null);
  };

  const copyIntakeLink = () => {
    if (!client) return;
    const url = `${window.location.origin}/#/intake/${client.intakeToken}`;
    navigator.clipboard.writeText(url);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  };

  const printAgreement = () => {
    if (!client) return;
    const win = window.open('', '_blank');
    if (!win) return;
    win.document.write(`<!DOCTYPE html><html><head><title>Agreement – ${client.firstName} ${client.lastName}</title></head><body>${buildAgreement(client)}<script>window.print();<\/script></body></html>`);
    win.document.close();
  };

  const printLetter = (content: string, title: string) => {
    const win = window.open('', '_blank');
    if (!win) return;
    win.document.write(`<!DOCTYPE html><html><head><title>${title}</title><style>body{font-family:Georgia,serif;max-width:700px;margin:40px auto;padding:40px;line-height:1.6;white-space:pre-wrap;}</style></head><body>${content}</body><script>window.print();<\/script></html>`);
    win.document.close();
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-slate-400 gap-3">
        <RefreshCw className="w-6 h-6 animate-spin text-indigo-500" />
        <span className="text-xs font-semibold uppercase tracking-wider">Synchronizing client docket...</span>
      </div>
    );
  }

  if (!client) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-rose-400 gap-3">
        <AlertCircle className="w-8 h-8" />
        <span className="text-sm font-bold">Client record not found.</span>
        <button onClick={() => navigate({ name: 'dashboard' })} className="text-xs text-slate-400 underline mt-2">
          Return to dashboard
        </button>
      </div>
    );
  }

  const currentStageIdx = STAGE_ORDER.indexOf(client.stage);
  const nextStage = STAGE_ORDER[currentStageIdx + 1];
  const agentsDone = Object.keys(client.agentOutputs).length;
  const stageInfo = PIPELINE_STAGES[client.stage];
  const intakeUrl = `${window.location.origin}/#/intake/${client.intakeToken}`;

  const tabs: { id: Tab; label: string; icon: any; count?: number }[] = [
    { id: 'overview', label: 'Overview', icon: FileText },
    { id: 'repair', label: 'Auto Repair', icon: Wrench },
    { id: 'agents', label: 'AI Agents', icon: Bot, count: agentsDone },
    { id: 'emails', label: 'Emails', icon: Mail, count: client.emailLog.length },
    { id: 'disputes', label: 'Dispute Letters', icon: Scale, count: client.disputes.length },
    { id: 'agreement', label: 'Legal Agreement', icon: FileCheck2 },
  ];

  return (
    <div className="max-w-7xl mx-auto p-6 md:p-8 space-y-8">
      
      {/* Top Header & Breadcrumb */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 glass-panel p-6 rounded-2xl border border-slate-800/80">
        <div>
          <button 
            onClick={() => navigate({ name: 'dashboard' })} 
            className="inline-flex items-center gap-1.5 text-slate-400 hover:text-white text-xs font-semibold mb-3 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Overseer Dashboard</span>
          </button>
          
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-extrabold tracking-tight text-white">
              {client.firstName} {client.lastName}
            </h1>
            <span className="text-xs px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider bg-indigo-500/10 text-indigo-300 border border-indigo-500/30">
              Plan {client.plan}
            </span>
          </div>
          <p className="text-slate-400 text-xs mt-1">
            {client.companyName ? `${client.companyName} · ` : ''}{client.email} · {client.phone}
          </p>
        </div>

        {/* Stage Progression Action */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-slate-900/80 border border-slate-800 px-3.5 py-2 rounded-xl text-xs font-bold text-white">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>{stageInfo.label}</span>
          </div>

          {nextStage && (
            <button 
              onClick={advanceStage} 
              disabled={advancingStage}
              className="flex items-center gap-2 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 disabled:opacity-50 text-white px-4 py-2 rounded-xl text-xs font-bold shadow-lg shadow-indigo-600/25 transition-all hover:scale-[1.02] active:scale-[0.98]"
            >
              {advancingStage ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <ChevronRight className="w-3.5 h-3.5" />}
              <span>{advancingStage ? 'Advancing...' : `Advance to ${PIPELINE_STAGES[nextStage].label}`}</span>
            </button>
          )}
        </div>
      </div>

      {/* Quick Metrics Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass-card rounded-2xl p-4.5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Plan Structure</span>
            <Layers className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-xl font-extrabold text-white">Tier {client.plan}</div>
          <div className="text-[11px] text-slate-500 mt-1">${client.plan === 'A' ? '1,250' : '1,500'} engagement value</div>
        </div>

        <div className="glass-card rounded-2xl p-4.5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Success Fee Status</span>
            <DollarSign className="w-4 h-4 text-emerald-400" />
          </div>
          <div className={`text-xl font-extrabold ${client.invoice?.status === 'PAID' ? 'text-emerald-400' : client.invoice?.status === 'OVERDUE' ? 'text-rose-400' : 'text-amber-400'}`}>
            ${(client.invoice?.amount ?? 0).toLocaleString()}
          </div>
          <div className="text-[11px] text-slate-500 mt-1 uppercase font-semibold">{client.invoice?.status ?? 'Pending'}</div>
        </div>

        <div className="glass-card rounded-2xl p-4.5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">AI Agents Executed</span>
            <Bot className="w-4 h-4 text-violet-400" />
          </div>
          <div className="text-xl font-extrabold text-white">{agentsDone} / 8</div>
          <div className="text-[11px] text-slate-500 mt-1">{client.disputes.length} legal letters drafted</div>
        </div>

        <div className="glass-card rounded-2xl p-4.5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Email Dispatches</span>
            <Mail className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-xl font-extrabold text-white">
            {client.emailLog.filter(e => e.status === 'SENT').length} / {client.emailLog.length}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Audit log tracking active</div>
        </div>
      </div>

      {/* Executive Suite Tri-Merge Bureau Scores Card */}
      <div className="relative overflow-hidden rounded-2xl bg-surface-subtle/80 backdrop-blur-lux border border-border-hairline p-6 shadow-lux-md transition-all duration-300 hover:border-border-gold hover:shadow-glow-gold">
        {/* Subtle ambient top gradient */}
        <div className="pointer-events-none absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-white/[0.03] to-transparent"></div>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[10px] font-bold uppercase tracking-widest text-lux-gold">
                Executive Suite Audit
              </span>
              <span className="px-2 py-0.5 rounded-full text-[9px] font-extrabold uppercase bg-lux-gold/10 text-lux-gold border border-border-gold">
                Tri-Merge Verified
              </span>
            </div>
            <div className="text-lg font-bold text-lux-primary">Live Institutional Bureau Metrics</div>
            <p className="text-xs text-lux-secondary mt-0.5">Real-time credit profile verification across national credit repositories.</p>
          </div>

          <div className="flex items-center gap-4 sm:gap-6">
            {[
              { bureau: 'Equifax', score: client.creditProfile.currentScores.equifax, color: 'text-rose-400', border: 'border-rose-500/30' },
              { bureau: 'Experian', score: client.creditProfile.currentScores.experian, color: 'text-blue-400', border: 'border-blue-500/30' },
              { bureau: 'TransUnion', score: client.creditProfile.currentScores.transunion, color: 'text-violet-400', border: 'border-violet-500/30' },
            ].map(b => (
              <div key={b.bureau} className={`text-center p-3 rounded-xl bg-surface-elevated/70 border ${b.border} min-w-[85px] shadow-sm`}>
                <div className={`text-2xl font-black ${b.color}`}>{b.score ?? '—'}</div>
                <div className="text-[10px] font-bold uppercase tracking-wider text-lux-secondary mt-0.5">{b.bureau}</div>
              </div>
            ))}

            <div className="text-center p-3 rounded-xl bg-lux-gold/10 border border-border-gold min-w-[85px] shadow-sm">
              <div className="text-2xl font-black text-lux-gold">{client.creditProfile.targetScore}</div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-lux-gold mt-0.5">Target</div>
            </div>
          </div>

          <button 
            onClick={runAgents} 
            disabled={runningAgents}
            className="flex items-center gap-2 rounded-xl border border-border-gold bg-lux-gold/10 px-5 py-3 text-xs font-bold text-lux-gold shadow-lux-sm transition-all hover:bg-lux-gold hover:text-canvas-base disabled:opacity-50"
          >
            {runningAgents ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            <span>{runningAgents ? 'Executing 8 Engines...' : 'Execute 8 AI Agents'}</span>
          </button>
        </div>
      </div>

      {/* Client Intake Share Banner */}
      <div className="glass-panel p-4.5 rounded-2xl flex flex-col sm:flex-row items-center justify-between gap-4 border border-slate-800">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 shrink-0">
            <Copy className="w-4 h-4" />
          </div>
          <div className="min-w-0">
            <div className="text-xs font-bold text-white">Client Self-Service Intake Portal</div>
            <div className="text-[11px] text-slate-400 font-mono truncate mt-0.5">{intakeUrl}</div>
          </div>
        </div>

        <button 
          onClick={copyIntakeLink}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold transition-all shrink-0 border border-slate-700"
        >
          {copiedLink ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          <span>{copiedLink ? 'Copied to Clipboard!' : 'Copy Portal URL'}</span>
        </button>
      </div>

      {/* Floating Glassmorphic Tabs Navigation */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-thin">
        {tabs.map((t) => {
          const Icon = t.icon;
          const isActive = tab === t.id;
          return (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`relative px-4 py-2.5 rounded-xl text-xs font-bold flex items-center gap-2 transition-all whitespace-nowrap ${
                isActive
                  ? 'text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
              }`}
            >
              {isActive && (
                <motion.div
                  layoutId="activeClientTab"
                  className="absolute inset-0 bg-gradient-to-r from-indigo-600 to-violet-600 rounded-xl shadow-md shadow-indigo-600/30"
                  transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                />
              )}
              <span className="relative z-10 flex items-center gap-2">
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                <span>{t.label}</span>
                {t.count !== undefined && (
                  <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-extrabold ${isActive ? 'bg-white/20 text-white' : 'bg-slate-800 text-slate-400'}`}>
                    {t.count}
                  </span>
                )}
              </span>
            </button>
          );
        })}
      </div>

      {/* Tab Panels with AnimatePresence */}
      <AnimatePresence mode="wait">
        <motion.div
          key={tab}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.18 }}
        >
          {/* Tab: Auto Repair */}
          {tab === 'repair' && (
            <div className="glass-card rounded-2xl p-6">
              <AutoRepairEngine client={client} onComplete={(updated) => setClient(updated)} />
            </div>
          )}

          {/* Tab: Overview */}
          {tab === 'overview' && (
            <div className="grid md:grid-cols-2 gap-6">
              {/* Pipeline Timeline */}
              <div className="glass-card rounded-2xl p-6">
                <h3 className="text-xs font-bold uppercase tracking-wider text-white mb-4 flex items-center gap-2">
                  <Clock className="w-4 h-4 text-indigo-400" />
                  <span>Pipeline Milestone Progression</span>
                </h3>
                <div className="space-y-4">
                  {STAGE_ORDER.map((stage, i) => {
                    const done = i <= currentStageIdx;
                    const current = i === currentStageIdx;
                    const meta = PIPELINE_STAGES[stage];
                    return (
                      <div key={stage} className="flex items-start gap-3">
                        <div className={`w-7 h-7 rounded-xl flex items-center justify-center text-xs font-bold shrink-0 mt-0.5 ${
                          current 
                            ? 'bg-gradient-to-tr from-indigo-600 to-violet-600 text-white shadow-md shadow-indigo-600/40 ring-2 ring-indigo-400/40' 
                            : done 
                              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' 
                              : 'bg-slate-900 border border-slate-800 text-slate-500'
                        }`}>
                          {done && !current ? <Check className="w-3.5 h-3.5" /> : i + 1}
                        </div>
                        <div className="flex-1">
                          <div className={`text-xs font-bold ${current ? 'text-indigo-300' : done ? 'text-white' : 'text-slate-500'}`}>
                            {meta.label}
                          </div>
                          <div className="text-[11px] text-slate-400 mt-0.5">{meta.description}</div>
                        </div>
                        {current && (
                          <span className="text-[10px] font-extrabold uppercase tracking-wider bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded-full border border-indigo-500/30">
                            Current
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Notes & Negative Items */}
              <div className="space-y-6">
                <div className="glass-card rounded-2xl p-6">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-white mb-3 flex items-center gap-2">
                    <FileText className="w-4 h-4 text-violet-400" />
                    <span>Case Consultant Notes</span>
                  </h3>
                  <p className="text-slate-400 text-xs whitespace-pre-wrap leading-relaxed">
                    {client.notes || 'No specialized underwriting or audit notes registered for this profile.'}
                  </p>
                </div>

                <div className="glass-card rounded-2xl p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-white flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 text-rose-400" />
                      <span>Audited Derogatory Trade Lines ({client.creditProfile.negativeItems.length})</span>
                    </h3>
                  </div>
                  
                  {client.creditProfile.negativeItems.length === 0 ? (
                    <p className="text-slate-500 text-xs">No derogatory items detected on file. Upload credit report text to execute parser.</p>
                  ) : (
                    <div className="space-y-2.5">
                      {client.creditProfile.negativeItems.slice(0, 5).map(item => (
                        <div key={item.id} className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between gap-4">
                          <div>
                            <div className="text-xs font-bold text-white">{item.creditor}</div>
                            <div className="text-[10px] text-slate-400 uppercase font-semibold mt-0.5">{item.type.replace(/_/g, ' ')} · {item.bureau}</div>
                          </div>
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/20">
                            Score Impact: {item.impactScore}/5
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Tab: AI Agents */}
          {tab === 'agents' && (
            <div className="grid md:grid-cols-2 gap-4">
              {AGENT_ORDER.map(agentId => {
                const meta = AGENT_META[agentId];
                const result = client.agentOutputs[agentId];
                const isSelected = selectedAgent === agentId;
                return (
                  <motion.div 
                    key={agentId} 
                    onClick={() => setSelectedAgent(isSelected ? null : agentId)}
                    className={`cursor-pointer glass-card rounded-2xl p-5 transition-all ${
                      isSelected 
                        ? 'border-indigo-500 md:col-span-2 shadow-xl shadow-indigo-600/15' 
                        : result 
                          ? 'glass-card-hover border-slate-800' 
                          : 'opacity-60 border-slate-800/60'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-3 mb-2">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 text-xs font-bold">
                          <Bot className="w-4 h-4" />
                        </div>
                        <div>
                          <div className="font-bold text-xs text-white">{meta.title}</div>
                          <div className="text-[11px] text-slate-400">{meta.description}</div>
                        </div>
                      </div>
                      <span className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider ${
                        result?.status === 'COMPLETE' 
                          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' 
                          : result?.status === 'RUNNING' 
                            ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' 
                            : 'bg-slate-800 text-slate-500'
                      }`}>
                        {result?.status ?? 'PENDING'}
                      </span>
                    </div>

                    {isSelected && result && (
                      <div className="mt-4 pt-4 border-t border-slate-800 space-y-4">
                        <div className="prose-crm max-h-[500px] overflow-y-auto scrollbar-thin p-3 rounded-xl bg-slate-950/70 border border-slate-800" dangerouslySetInnerHTML={{ __html: renderMarkdown(result.output) }} />
                        
                        {(result.letters?.length ?? 0) > 0 && (
                          <div className="flex flex-wrap gap-2 pt-2">
                            {result.letters!.map(l => (
                              <button 
                                key={l.id} 
                                onClick={(e) => { 
                                  e.stopPropagation(); 
                                  printLetter(l.content, `${l.type} – ${l.bureau || l.creditor}`); 
                                }}
                                className="flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs px-3.5 py-2 rounded-xl font-bold transition-all shadow-md"
                              >
                                <Printer className="w-3.5 h-3.5" />
                                <span>Print {l.bureau || l.creditor} Notice</span>
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </motion.div>
                );
              })}
            </div>
          )}

          {/* Tab: Emails */}
          {tab === 'emails' && (
            <div className="glass-card rounded-2xl p-6 space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-white">Automated Compliance Email Dispatches</h3>
                  <p className="text-slate-400 text-xs mt-0.5">Automated Mailjet triggers based on pipeline stage triggers.</p>
                </div>
              </div>

              <div className="space-y-3">
                {EMAIL_STAGES.map(stage => {
                  const meta = EMAIL_STAGE_META[stage];
                  const sent = client.emailLog.find(e => e.stage === stage && e.status === 'SENT');
                  const isSending = sendingEmail === stage;
                  return (
                    <div key={stage} className={`p-4 rounded-xl border flex items-center justify-between gap-4 transition-all ${
                      sent ? 'bg-emerald-500/5 border-emerald-500/30' : 'bg-slate-900/60 border-slate-800'
                    }`}>
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-indigo-400">
                          <Mail className="w-4 h-4" />
                        </div>
                        <div className="min-w-0">
                          <div className="text-xs font-bold text-white truncate">{meta.subject}</div>
                          <div className="text-[11px] text-slate-400 mt-0.5">{meta.trigger}</div>
                          {sent && (
                            <div className="text-[10px] text-emerald-400 font-semibold mt-1 flex items-center gap-1">
                              <CheckCircle2 className="w-3 h-3" />
                              <span>Delivered {new Date(sent.sentAt!).toLocaleDateString()}</span>
                            </div>
                          )}
                        </div>
                      </div>

                      <button 
                        onClick={() => sendEmail(stage)} 
                        disabled={isSending}
                        className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold transition-all shrink-0 ${
                          sent 
                            ? 'bg-slate-800 hover:bg-slate-700 text-slate-300' 
                            : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/25'
                        } disabled:opacity-50`}
                      >
                        {isSending ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                        <span>{isSending ? 'Sending...' : sent ? 'Resend Copy' : 'Dispatch Email'}</span>
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Tab: Dispute Letters */}
          {tab === 'disputes' && (
            <div className="glass-card rounded-2xl p-6 space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-white">Generated FCRA & Goodwill Letters</h3>
                  <p className="text-slate-400 text-xs mt-0.5">Ready for Certified Mail or online overnight dispatch.</p>
                </div>
              </div>

              {client.disputes.length === 0 ? (
                <div className="text-center py-12 text-slate-500">
                  <Scale className="w-10 h-10 mx-auto mb-3 opacity-40" />
                  <p className="text-xs">No dispute letters generated yet. Execute the AI Agents tab to produce letters.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {client.disputes.map(letter => (
                    <div key={letter.id} className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2.5">
                          <Scale className="w-4 h-4 text-indigo-400" />
                          <span className="text-xs font-bold text-white uppercase tracking-wider">
                            {letter.type.replace(/_/g, ' ')} — {letter.bureau || 'Creditor Target'}
                          </span>
                        </div>
                        <button 
                          onClick={() => printLetter(letter.content, `${letter.type} – ${letter.bureau || ''}`)}
                          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-all shadow-md"
                        >
                          <Printer className="w-3.5 h-3.5" />
                          <span>Print Certified PDF</span>
                        </button>
                      </div>

                      <pre className="p-4 rounded-xl bg-slate-950 font-mono text-[11px] text-slate-300 leading-relaxed max-h-60 overflow-y-auto whitespace-pre-wrap border border-slate-900">
                        {letter.content}
                      </pre>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Tab: Legal Agreement */}
          {tab === 'agreement' && (
            <div className="relative overflow-hidden rounded-2xl bg-surface-subtle/80 backdrop-blur-lux border border-border-hairline p-6 md:p-8 shadow-lux-md transition-all duration-300 hover:border-border-gold hover:shadow-glow-gold space-y-6">
              {/* Ambient top gradient */}
              <div className="pointer-events-none absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-white/[0.03] to-transparent"></div>

              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 relative z-10">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-lux-gold">
                      Executive Protocol
                    </span>
                    <span className="px-2 py-0.5 rounded-full text-[9px] font-extrabold uppercase bg-lux-gold/10 text-lux-gold border border-border-gold">
                      Binding Accord
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-lux-primary">Personal Guarantor Consulting Agreement</h3>
                  <p className="text-xs text-lux-secondary mt-0.5">Florida Chapter 687 Compliant Statutory Retainer & Success Fee Agreement</p>
                </div>
                <button 
                  onClick={printAgreement}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-xl border border-border-gold bg-lux-gold/10 hover:bg-lux-gold hover:text-canvas-base text-lux-gold text-xs font-bold shadow-lux-sm transition-all shrink-0"
                >
                  <Printer className="w-3.5 h-3.5" />
                  <span>Print Formal Sovereign Copy</span>
                </button>
              </div>

              <div className="rounded-2xl overflow-hidden border border-border-gold/30 shadow-2xl relative z-10" dangerouslySetInnerHTML={{ __html: buildAgreement(client) }} />
            </div>
          )}
        </motion.div>
      </AnimatePresence>

    </div>
  );
}
