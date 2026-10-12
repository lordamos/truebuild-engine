import React, { useEffect, useState } from 'react';
import type { Client, PipelineStage } from '../types/credit';
import { PIPELINE_STAGES } from '../types/credit';
import type { Page } from '../App';
import { motion } from 'framer-motion';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { 
  Users, 
  CheckCircle2, 
  DollarSign, 
  Clock, 
  UserPlus, 
  Search, 
  RefreshCw, 
  AlertTriangle,
  TrendingUp,
  ChevronRight,
  Filter,
  Sparkles,
  ArrowUpRight
} from 'lucide-react';

const API = 'http://localhost:3002/api';

const STAGE_ORDER: PipelineStage[] = ['NEW', 'DOCS_VERIFIED', 'SUBMITTED', 'APPROVED', 'INVOICE_SENT', 'PAID', 'DISPUTE_ACTIVE', 'POST_CARE'];

const STAGE_COLOR: Record<string, string> = {
  blue: 'border-blue-500/30 bg-blue-500/5',
  indigo: 'border-indigo-500/30 bg-indigo-500/5',
  purple: 'border-purple-500/30 bg-purple-500/5',
  emerald: 'border-emerald-500/30 bg-emerald-500/5',
  yellow: 'border-amber-500/30 bg-amber-500/5',
  green: 'border-emerald-500/30 bg-emerald-500/5',
  orange: 'border-orange-500/30 bg-orange-500/5',
  teal: 'border-teal-500/30 bg-teal-500/5',
  gray: 'border-slate-700/60 bg-slate-900/40',
};

const STAGE_BADGE: Record<string, string> = {
  blue: 'bg-blue-500/15 text-blue-300 border-blue-500/30',
  indigo: 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30',
  purple: 'bg-purple-500/15 text-purple-300 border-purple-500/30',
  emerald: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  yellow: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  green: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  orange: 'bg-orange-500/15 text-orange-300 border-orange-500/30',
  teal: 'bg-teal-500/15 text-teal-300 border-teal-500/30',
  gray: 'bg-slate-800 text-slate-300 border-slate-700',
};

const CHART_COLORS = ['#6366f1', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#14b8a6', '#f97316', '#3b82f6'];

interface Props { navigate: (p: Page) => void; }

export function Dashboard({ navigate }: Props) {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [stageFilter, setStageFilter] = useState<PipelineStage | 'ALL'>('ALL');

  const load = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/clients`);
      const json = await res.json();
      setClients(json.data ?? []);
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const filtered = clients.filter(c => {
    const matchSearch = search === '' || `${c.firstName} ${c.lastName} ${c.companyName} ${c.email}`.toLowerCase().includes(search.toLowerCase());
    const matchStage = stageFilter === 'ALL' || c.stage === stageFilter;
    return matchSearch && matchStage;
  });

  // KPIs
  const totalRevenue = clients.filter(c => c.invoice?.status === 'PAID').reduce((s, c) => s + (c.invoice?.amount ?? 0), 0);
  const pendingRevenue = clients.filter(c => c.invoice?.status === 'PENDING').reduce((s, c) => s + (c.invoice?.amount ?? 0), 0);
  const approved = clients.filter(c => ['APPROVED', 'INVOICE_SENT', 'PAID', 'POST_CARE'].includes(c.stage)).length;
  const overdue = clients.filter(c => c.invoice?.status === 'OVERDUE').length;

  // Group by stage for Kanban
  const grouped = STAGE_ORDER.reduce((acc, stage) => {
    acc[stage] = clients.filter(c => c.stage === stage);
    return acc;
  }, {} as Record<PipelineStage, Client[]>);

  // Chart Data
  const pipelineData = STAGE_ORDER.map(stage => ({
    name: PIPELINE_STAGES[stage].label,
    count: grouped[stage]?.length || 0
  }));

  const planData = [
    { name: 'Plan A ($1,250)', value: clients.filter(c => c.plan === 'A').length },
    { name: 'Plan B ($1,500)', value: clients.filter(c => c.plan === 'B').length },
  ];

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      
      {/* Modern Hero Header Banner */}
      <div className="relative overflow-hidden rounded-2xl glass-panel p-8 border border-slate-800/80 shadow-2xl">
        <div className="absolute top-0 right-0 -mt-12 -mr-12 w-96 h-96 rounded-full bg-gradient-to-br from-indigo-600/20 to-violet-600/10 blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-semibold mb-3">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Autonomous Credit Repair Intelligence</span>
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
              Overseer Operations
            </h1>
            <p className="text-slate-400 text-sm mt-1 max-w-xl">
              Live tracking of underwriting pipelines, automated FCRA dispute engines, and client personal guarantor portfolios.
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            <button 
              onClick={load}
              className="p-3 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700/80 transition-all hover:scale-105 active:scale-95"
              title="Refresh Pipeline"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button 
              onClick={() => navigate({ name: 'new-client' })}
              className="flex items-center gap-2 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white px-5 py-3 rounded-xl font-bold text-sm shadow-lg shadow-indigo-600/25 transition-all hover:shadow-indigo-600/40 hover:scale-[1.02] active:scale-[0.98]"
            >
              <UserPlus className="w-4 h-4" />
              <span>Onboard New Client</span>
            </button>
          </div>
        </div>
      </div>

      {/* KPI Cards Grid with Staggered Fade-in */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-5">
        {[
          { 
            label: 'Total Client Files', 
            value: clients.length, 
            icon: Users, 
            gradient: 'from-blue-600/20 to-indigo-600/10',
            textColor: 'text-blue-400',
            iconColor: 'text-blue-400' 
          },
          { 
            label: 'Approved Facilities', 
            value: approved, 
            icon: CheckCircle2, 
            gradient: 'from-emerald-600/20 to-teal-600/10',
            textColor: 'text-emerald-400',
            iconColor: 'text-emerald-400' 
          },
          { 
            label: 'Revenue Collected', 
            value: `$${totalRevenue.toLocaleString()}`, 
            icon: DollarSign, 
            gradient: 'from-violet-600/20 to-purple-600/10',
            textColor: 'text-violet-300',
            iconColor: 'text-violet-400' 
          },
          { 
            label: 'Pending Success Fees', 
            value: `$${pendingRevenue.toLocaleString()}`, 
            icon: Clock, 
            gradient: 'from-amber-600/20 to-yellow-600/10',
            textColor: 'text-amber-300',
            iconColor: 'text-amber-400' 
          },
        ].map((kpi, i) => {
          const Icon = kpi.icon;
          return (
            <motion.div
              key={kpi.label}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.08, duration: 0.3 }}
              className="glass-card glass-card-hover rounded-2xl p-5 relative overflow-hidden"
            >
              <div className={`absolute top-0 right-0 w-24 h-24 bg-gradient-to-br ${kpi.gradient} blur-xl rounded-full -mr-6 -mt-6 pointer-events-none`} />
              <div className="flex items-center justify-between mb-3">
                <span className="text-slate-400 text-xs font-semibold tracking-wide uppercase">{kpi.label}</span>
                <div className="p-2 rounded-xl bg-slate-900/60 border border-slate-800">
                  <Icon className={`w-4 h-4 ${kpi.iconColor}`} />
                </div>
              </div>
              <div className={`text-3xl font-extrabold tracking-tight ${kpi.textColor}`}>{kpi.value}</div>
              <div className="flex items-center gap-1 text-[11px] text-slate-500 mt-2 font-medium">
                <TrendingUp className="w-3 h-3 text-emerald-400" />
                <span>Live synchronizing</span>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Analytics Charts */}
      {clients.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <motion.div
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            className="md:col-span-2 glass-card rounded-2xl p-6"
          >
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-sm font-bold text-white tracking-wide uppercase">Pipeline Velocity</h3>
                <p className="text-xs text-slate-400 mt-0.5">Distribution of clients across processing stages</p>
              </div>
              <span className="text-xs font-semibold text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-2.5 py-1 rounded-lg">Realtime</span>
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={pipelineData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} tickLine={false} axisLine={false} />
                  <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} tickLine={false} axisLine={false} />
                  <Tooltip 
                    cursor={{ fill: 'rgba(99, 102, 241, 0.08)' }}
                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', boxShadow: '0 8px 24px rgba(0,0,0,0.5)' }} 
                  />
                  <Bar dataKey="count" fill="url(#barGradient)" radius={[6, 6, 0, 0]} />
                  <defs>
                    <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#6366f1" />
                      <stop offset="100%" stopColor="#4f46e5" />
                    </linearGradient>
                  </defs>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </motion.div>
          
          <motion.div
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
            className="glass-card rounded-2xl p-6 flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-white tracking-wide uppercase">Plan Allocation</h3>
                <span className="text-xs text-slate-400 font-medium">Breakdown</span>
              </div>
              <div className="h-52 relative">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={planData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                      stroke="none"
                    >
                      {planData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-2 mt-4 pt-4 border-t border-slate-800">
              <div className="flex items-center gap-2 p-2 rounded-xl bg-slate-900/60 border border-slate-800">
                <div className="w-2.5 h-2.5 rounded-full bg-indigo-500" />
                <div>
                  <div className="text-[11px] text-slate-400 font-medium">Plan A</div>
                  <div className="text-xs font-bold text-white">$1,250</div>
                </div>
              </div>
              <div className="flex items-center gap-2 p-2 rounded-xl bg-slate-900/60 border border-slate-800">
                <div className="w-2.5 h-2.5 rounded-full bg-violet-500" />
                <div>
                  <div className="text-[11px] text-slate-400 font-medium">Plan B</div>
                  <div className="text-xs font-bold text-white">$1,500</div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      )}

      {/* Overdue alert banner */}
      {overdue > 0 && (
        <motion.div 
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-rose-950/40 border border-rose-500/40 rounded-2xl p-5 flex items-center gap-4 text-rose-200 shadow-xl"
        >
          <div className="w-10 h-10 rounded-xl bg-rose-500/20 border border-rose-500/30 flex items-center justify-center shrink-0">
            <AlertTriangle className="w-5 h-5 text-rose-400" />
          </div>
          <div className="flex-1">
            <div className="font-bold text-sm text-white">{overdue} client(s) with overdue success fees detected</div>
            <div className="text-xs text-rose-300/80 mt-0.5">Automated 48-hour recovery notifications are queued. Review below.</div>
          </div>
        </motion.div>
      )}

      {/* Search & Filter Toolbar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 glass-panel p-3.5 rounded-2xl border border-slate-800/80">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
          <input 
            value={search} 
            onChange={e => setSearch(e.target.value)}
            placeholder="Search by client name, company, email..."
            className="w-full bg-slate-900/90 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all" 
          />
        </div>
        
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-slate-900/90 border border-slate-800 rounded-xl px-3 py-1.5">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select 
              value={stageFilter} 
              onChange={e => setStageFilter(e.target.value as any)}
              className="bg-transparent text-xs text-white focus:outline-none cursor-pointer"
            >
              <option value="ALL" className="bg-slate-900">All Pipeline Stages</option>
              {STAGE_ORDER.map(s => <option key={s} value={s} className="bg-slate-900">{PIPELINE_STAGES[s].label}</option>)}
            </select>
          </div>
        </div>
      </div>

      {/* Kanban Board with Rounded Glass Cards */}
      {stageFilter === 'ALL' ? (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-white tracking-wide">Interactive Stage Pipeline</h2>
            <span className="text-xs text-slate-400 font-medium">Scroll horizontally to view all stages</span>
          </div>
          
          <div className="overflow-x-auto pb-4 scrollbar-thin">
            <div className="flex gap-4 min-w-max">
              {STAGE_ORDER.map(stage => {
                const meta = PIPELINE_STAGES[stage];
                const stageClients = grouped[stage] || [];
                return (
                  <div key={stage} className={`w-64 border rounded-2xl p-3.5 flex flex-col ${STAGE_COLOR[meta.color]} backdrop-blur-sm`}>
                    <div className="flex items-center justify-between mb-3 px-1">
                      <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">{meta.label}</span>
                      <span className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full border ${STAGE_BADGE[meta.color]}`}>
                        {stageClients.length}
                      </span>
                    </div>

                    <div className="space-y-2.5 flex-1 min-h-[160px]">
                      {stageClients.length === 0 && (
                        <div className="h-full flex items-center justify-center p-6 border border-dashed border-slate-800/80 rounded-xl">
                          <p className="text-slate-600 text-[11px] font-medium text-center">No client records</p>
                        </div>
                      )}
                      {stageClients.map(c => (
                        <motion.button 
                          key={c.id} 
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                          onClick={() => navigate({ name: 'client', id: c.id })}
                          className="w-full text-left glass-card glass-card-hover rounded-xl p-3.5 border border-slate-800 transition-all group"
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div className="font-bold text-xs text-white group-hover:text-indigo-300 transition-colors truncate">
                              {c.firstName} {c.lastName}
                            </div>
                            <ArrowUpRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-indigo-400 transition-colors shrink-0" />
                          </div>
                          <div className="text-[11px] text-slate-400 truncate mt-0.5">{c.companyName}</div>
                          
                          <div className="flex items-center justify-between mt-3 pt-2.5 border-t border-slate-800/60">
                            <span className="text-[10px] font-semibold text-slate-400 px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800">
                              Plan {c.plan}
                            </span>
                            <span className={`text-xs font-bold ${c.invoice?.status === 'PAID' ? 'text-emerald-400' : c.invoice?.status === 'OVERDUE' ? 'text-rose-400' : 'text-amber-400'}`}>
                              ${(c.invoice?.amount ?? 0).toLocaleString()}
                            </span>
                          </div>
                        </motion.button>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      ) : (
        /* List View */
        <div className="space-y-3">
          {loading && <p className="text-slate-400 text-xs py-4 text-center">Loading client profiles...</p>}
          {!loading && filtered.length === 0 && (
            <div className="glass-card rounded-2xl p-8 text-center text-slate-500 text-sm">
              No matching client records found.
            </div>
          )}
          {filtered.map(c => {
            const meta = PIPELINE_STAGES[c.stage];
            return (
              <motion.button 
                key={c.id} 
                whileHover={{ scale: 1.005 }}
                onClick={() => navigate({ name: 'client', id: c.id })}
                className="w-full text-left glass-card glass-card-hover rounded-2xl p-4.5 transition-all flex items-center justify-between gap-4 group"
              >
                <div className="flex-1 min-w-0">
                  <div className="font-bold text-sm text-white group-hover:text-indigo-300 transition-colors">
                    {c.firstName} {c.lastName} 
                    <span className="text-slate-500 font-normal text-xs ml-2">· {c.companyName}</span>
                  </div>
                  <div className="text-xs text-slate-400 mt-0.5">{c.email} · {c.phone}</div>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className={`text-[10px] px-2.5 py-1 rounded-full font-bold border ${STAGE_BADGE[meta.color]}`}>
                    {meta.label}
                  </span>
                  <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-lg border border-emerald-500/20">
                    ${(c.invoice?.amount ?? 0).toLocaleString()}
                  </span>
                  <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-indigo-400 transition-colors" />
                </div>
              </motion.button>
            );
          })}
        </div>
      )}

    </div>
  );
}
