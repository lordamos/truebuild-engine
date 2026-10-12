import React, { useState } from 'react';
import type { Page } from '../App';
import { 
  ArrowLeft, 
  Check, 
  User, 
  Building2, 
  CreditCard, 
  FileCheck, 
  Sparkles,
  ShieldAlert,
  Loader2,
  ChevronRight
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API = 'http://localhost:3002/api';

interface Props { navigate: (p: Page) => void; }

const STEPS = [
  { label: 'Client Identity', icon: User },
  { label: 'Business & Plan', icon: Building2 },
  { label: 'Credit Profile', icon: CreditCard },
  { label: 'Finalize & Onboard', icon: FileCheck },
];

export function NewClient({ navigate }: Props) {
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [form, setForm] = useState({
    firstName: '', lastName: '', email: '', phone: '', address: '', city: '', state: '', zip: '',
    companyName: '', ein: '', businessType: '', plan: 'A' as 'A' | 'B',
    equifax: '', experian: '', transunion: '', targetScore: '750', reportText: '',
    notes: '',
  });

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }));

  const canNext = () => {
    if (step === 0) return form.firstName && form.lastName && form.email && form.phone;
    if (step === 1) return form.companyName && form.plan;
    return true;
  };

  const submit = async () => {
    setLoading(true); setError('');
    try {
      const payload = {
        ...form,
        creditProfile: {
          currentScores: {
            equifax: form.equifax ? parseInt(form.equifax) : undefined,
            experian: form.experian ? parseInt(form.experian) : undefined,
            transunion: form.transunion ? parseInt(form.transunion) : undefined,
          },
          targetScore: parseInt(form.targetScore) || 750,
          reportText: form.reportText,
          negativeItems: [],
          debtAccounts: [],
        },
      };
      const res = await fetch(`${API}/clients`, { 
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' }, 
        body: JSON.stringify(payload) 
      });
      const json = await res.json();
      if (!json.success) throw new Error(json.error);
      navigate({ name: 'client', id: json.data.id });
    } catch (e: any) {
      setError(e.message ?? 'Failed to create client');
    } finally { setLoading(false); }
  };

  const inputCls = "w-full bg-slate-900/90 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all";
  const labelCls = "block text-[11px] font-bold text-slate-400 mb-1.5 uppercase tracking-wider";

  return (
    <div className="max-w-3xl mx-auto p-6 md:p-8">
      {/* Header */}
      <div className="mb-8">
        <button 
          onClick={() => navigate({ name: 'dashboard' })} 
          className="inline-flex items-center gap-1.5 text-slate-400 hover:text-white text-xs font-semibold mb-4 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Operations Dashboard</span>
        </button>
        
        <div className="flex items-center gap-2 mb-1">
          <div className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <Sparkles className="w-4 h-4" />
          </div>
          <h1 className="text-2xl font-extrabold tracking-tight text-white">Client Intake Engine</h1>
        </div>
        <p className="text-slate-400 text-xs">Register new personal guarantor profile to initiate autonomous FCRA audit pipeline.</p>
      </div>

      {/* Modern Stepper */}
      <div className="glass-panel p-4 rounded-2xl mb-8 border border-slate-800/80">
        <div className="flex items-center justify-between">
          {STEPS.map((s, i) => {
            const Icon = s.icon;
            const isCompleted = i < step;
            const isCurrent = i === step;
            return (
              <React.Fragment key={s.label}>
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold transition-all ${
                    isCurrent 
                      ? 'bg-gradient-to-tr from-indigo-600 to-violet-600 text-white shadow-md shadow-indigo-600/30' 
                      : isCompleted 
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' 
                        : 'bg-slate-900 border border-slate-800 text-slate-500'
                  }`}>
                    {isCompleted ? <Check className="w-4 h-4" /> : <Icon className="w-4 h-4" />}
                  </div>
                  <div className="hidden sm:block text-left">
                    <div className="text-[10px] uppercase font-bold tracking-wider text-slate-500">Step 0{i + 1}</div>
                    <div className={`text-xs font-bold ${isCurrent ? 'text-white' : 'text-slate-400'}`}>{s.label}</div>
                  </div>
                </div>
                {i < STEPS.length - 1 && (
                  <div className={`flex-1 h-0.5 mx-3 rounded-full transition-colors ${
                    i < step ? 'bg-gradient-to-r from-emerald-500 to-indigo-500' : 'bg-slate-800'
                  }`} />
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* Step Container Card */}
      <div className="glass-card rounded-2xl p-6 md:p-8 space-y-6">
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -10 }}
            transition={{ duration: 0.2 }}
            className="space-y-5"
          >
            {/* Step 0: Contact Info */}
            {step === 0 && (
              <>
                <div className="border-b border-slate-800 pb-4 mb-4">
                  <h2 className="text-sm font-bold text-white uppercase tracking-wider">01. Personal Identity Data</h2>
                  <p className="text-slate-400 text-xs mt-0.5">Required for legal bureau dispute filings under FCRA § 609.</p>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className={labelCls}>First Name *</label>
                    <input className={inputCls} placeholder="John" value={form.firstName} onChange={set('firstName')} />
                  </div>
                  <div>
                    <label className={labelCls}>Last Name *</label>
                    <input className={inputCls} placeholder="Smith" value={form.lastName} onChange={set('lastName')} />
                  </div>
                </div>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className={labelCls}>Direct Email *</label>
                    <input type="email" className={inputCls} placeholder="john@domain.com" value={form.email} onChange={set('email')} />
                  </div>
                  <div>
                    <label className={labelCls}>Mobile Contact *</label>
                    <input className={inputCls} placeholder="(321) 555-0100" value={form.phone} onChange={set('phone')} />
                  </div>
                </div>

                <div>
                  <label className={labelCls}>Residential Street Address</label>
                  <input className={inputCls} placeholder="123 Ocean Palm Drive" value={form.address} onChange={set('address')} />
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className={labelCls}>City</label>
                    <input className={inputCls} placeholder="Palm Bay" value={form.city} onChange={set('city')} />
                  </div>
                  <div>
                    <label className={labelCls}>State</label>
                    <input className={inputCls} placeholder="FL" value={form.state} onChange={set('state')} />
                  </div>
                  <div>
                    <label className={labelCls}>ZIP</label>
                    <input className={inputCls} placeholder="32905" value={form.zip} onChange={set('zip')} />
                  </div>
                </div>
              </>
            )}

            {/* Step 1: Business & Program Plan */}
            {step === 1 && (
              <>
                <div className="border-b border-slate-800 pb-4 mb-4">
                  <h2 className="text-sm font-bold text-white uppercase tracking-wider">02. Corporate Entity & Engagement Plan</h2>
                  <p className="text-slate-400 text-xs mt-0.5">Commercial guarantor entity and program pricing structure.</p>
                </div>

                <div>
                  <label className={labelCls}>Company Legal Entity Name *</label>
                  <input className={inputCls} placeholder="Apex Ventures LLC" value={form.companyName} onChange={set('companyName')} />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className={labelCls}>Federal EIN</label>
                    <input className={inputCls} placeholder="XX-XXXXXXX" value={form.ein} onChange={set('ein')} />
                  </div>
                  <div>
                    <label className={labelCls}>Entity Structure</label>
                    <select className={inputCls} value={form.businessType} onChange={set('businessType')}>
                      <option value="">Select Structure</option>
                      <option value="LLC">LLC</option>
                      <option value="C-Corp">C-Corporation</option>
                      <option value="S-Corp">S-Corporation</option>
                      <option value="Sole Proprietor">Sole Proprietorship</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className={labelCls}>Engagement Plan Tier *</label>
                  <div className="grid grid-cols-2 gap-4 mt-2">
                    <button
                      type="button"
                      onClick={() => setForm(f => ({ ...f, plan: 'A' }))}
                      className={`p-4 rounded-xl text-left border transition-all ${
                        form.plan === 'A'
                          ? 'border-indigo-500 bg-indigo-500/10 shadow-lg shadow-indigo-500/20'
                          : 'border-slate-800 bg-slate-900/60 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-bold text-xs text-white">Tier A: Standard</span>
                        <span className="text-[10px] font-extrabold px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300">$1,250 Total</span>
                      </div>
                      <div className="text-[11px] text-slate-400 mt-2">$250 Retainer + $1,000 on First Approval</div>
                    </button>

                    <button
                      type="button"
                      onClick={() => setForm(f => ({ ...f, plan: 'B' }))}
                      className={`p-4 rounded-xl text-left border transition-all ${
                        form.plan === 'B'
                          ? 'border-violet-500 bg-violet-500/10 shadow-lg shadow-violet-500/20'
                          : 'border-slate-800 bg-slate-900/60 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-bold text-xs text-white">Tier B: Deferred</span>
                        <span className="text-[10px] font-extrabold px-2 py-0.5 rounded bg-violet-500/20 text-violet-300">$1,500 Total</span>
                      </div>
                      <div className="text-[11px] text-slate-400 mt-2">$0 Retainer + $1,500 Deferred on Approval</div>
                    </button>
                  </div>
                </div>
              </>
            )}

            {/* Step 2: Tri-Merge Credit Profile */}
            {step === 2 && (
              <>
                <div className="border-b border-slate-800 pb-4 mb-4">
                  <h2 className="text-sm font-bold text-white uppercase tracking-wider">03. Tri-Merge Bureau Scores & Raw Report</h2>
                  <p className="text-slate-400 text-xs mt-0.5">Input starting scores or paste raw report text for automatic regex parsing.</p>
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className={labelCls}>Equifax</label>
                    <input type="number" className={inputCls} placeholder="640" value={form.equifax} onChange={set('equifax')} />
                  </div>
                  <div>
                    <label className={labelCls}>Experian</label>
                    <input type="number" className={inputCls} placeholder="655" value={form.experian} onChange={set('experian')} />
                  </div>
                  <div>
                    <label className={labelCls}>TransUnion</label>
                    <input type="number" className={inputCls} placeholder="635" value={form.transunion} onChange={set('transunion')} />
                  </div>
                </div>

                <div>
                  <label className={labelCls}>Raw Credit Report Text (IdentityIQ / SmartCredit / Experian)</label>
                  <textarea 
                    rows={4} 
                    className={`${inputCls} font-mono text-[11px]`} 
                    placeholder="Paste entire text dump from credit monitoring report here. Automated parser will extract collections, charge-offs, and inquiries automatically." 
                    value={form.reportText} 
                    onChange={set('reportText')} 
                  />
                </div>
              </>
            )}

            {/* Step 3: Review & Activate */}
            {step === 3 && (
              <>
                <div className="border-b border-slate-800 pb-4 mb-4">
                  <h2 className="text-sm font-bold text-white uppercase tracking-wider">04. Review & Launch File</h2>
                  <p className="text-slate-400 text-xs mt-0.5">Confirm details. This will generate client portal token and draft consulting agreement.</p>
                </div>

                <div className="glass-panel p-4 rounded-xl border border-slate-800/80 space-y-2 text-xs">
                  <div className="flex justify-between py-1 border-b border-slate-800">
                    <span className="text-slate-400">Guarantor Name:</span>
                    <span className="font-bold text-white">{form.firstName} {form.lastName}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800">
                    <span className="text-slate-400">Corporate Entity:</span>
                    <span className="font-bold text-white">{form.companyName || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800">
                    <span className="text-slate-400">Contact Email:</span>
                    <span className="font-bold text-white">{form.email}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800">
                    <span className="text-slate-400">Selected Plan:</span>
                    <span className="font-bold text-indigo-400">Tier {form.plan} ({form.plan === 'A' ? '$1,250' : '$1,500'})</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-400">Bureau Scores:</span>
                    <span className="font-bold text-emerald-400">EQ: {form.equifax || '-'} | EX: {form.experian || '-'} | TU: {form.transunion || '-'}</span>
                  </div>
                </div>
              </>
            )}
          </motion.div>
        </AnimatePresence>

        {/* Error message */}
        {error && (
          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Navigation Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-slate-800">
          {step > 0 ? (
            <button
              type="button"
              onClick={() => setStep(s => s - 1)}
              className="px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white text-xs font-semibold transition-all hover:bg-slate-800"
            >
              Previous Step
            </button>
          ) : <div />}

          {step < STEPS.length - 1 ? (
            <button
              type="button"
              disabled={!canNext()}
              onClick={() => setStep(s => s + 1)}
              className="flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-bold shadow-lg shadow-indigo-600/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span>Continue</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          ) : (
            <button
              type="button"
              disabled={loading}
              onClick={submit}
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-bold shadow-lg shadow-emerald-600/25 transition-all disabled:opacity-50"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
              <span>Deploy Client File</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
