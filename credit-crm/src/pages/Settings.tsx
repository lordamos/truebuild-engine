import React, { useEffect, useState } from 'react';
import type { ProviderSettings } from '../types/credit';
import { 
  Settings as SettingsIcon, 
  Mail, 
  Key, 
  Building2, 
  Phone, 
  User, 
  Save, 
  Check, 
  ExternalLink,
  ShieldCheck,
  RefreshCw
} from 'lucide-react';
import { motion } from 'framer-motion';

const API = 'http://localhost:3002/api';

export function Settings() {
  const [settings, setSettings] = useState<ProviderSettings | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    fetch(`${API}/settings`).then(r => r.json()).then(j => setSettings(j.data));
  }, []);

  const set = (k: keyof ProviderSettings) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setSettings(s => s ? { ...s, [k]: e.target.value } : s);

  const save = async () => {
    if (!settings) return;
    setSaving(true);
    await fetch(`${API}/settings`, { 
      method: 'POST', 
      headers: { 'Content-Type': 'application/json' }, 
      body: JSON.stringify(settings) 
    });
    setSaving(false); 
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const inputCls = "w-full bg-slate-900/90 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all";
  const labelCls = "block text-[11px] font-bold text-slate-400 mb-1.5 uppercase tracking-wider";

  return (
    <div className="max-w-4xl mx-auto p-6 md:p-8 space-y-8">
      {/* Header */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800/80">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <SettingsIcon className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight text-white">System Configurations</h1>
            <p className="text-slate-400 text-xs mt-0.5">Manage Mailjet transactional email dispatchers and agency profile parameters.</p>
          </div>
        </div>
      </div>

      {settings && (
        <div className="space-y-6">
          {/* Provider Information Card */}
          <div className="glass-card rounded-2xl p-6 space-y-4">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
              <Building2 className="w-4 h-4 text-indigo-400" />
              <h2 className="text-xs font-bold uppercase tracking-wider text-white">Agency & Guarantor Identity</h2>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className={labelCls}>Managing Consultant Name</label>
                <input className={inputCls} value={settings.name} onChange={set('name')} placeholder="Jane Doe" />
              </div>
              <div>
                <label className={labelCls}>Corporate Agency Entity</label>
                <input className={inputCls} value={settings.companyName} onChange={set('companyName')} placeholder="Credit Acceleration Services LLC" />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className={labelCls}>Direct Consultant Email</label>
                <input type="email" className={inputCls} value={settings.email} onChange={set('email')} placeholder="admin@sumthin3lseglobal.com" />
              </div>
              <div>
                <label className={labelCls}>Direct Phone Contact</label>
                <input className={inputCls} value={settings.phone} onChange={set('phone')} placeholder="(321) 555-0100" />
              </div>
            </div>
          </div>

          {/* Mailjet Configuration Card */}
          <div className="glass-card rounded-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Mail className="w-4 h-4 text-violet-400" />
                <h2 className="text-xs font-bold uppercase tracking-wider text-white">Mailjet Automated Dispatch Gateway</h2>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Connected
              </span>
            </div>

            <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-200 text-xs flex items-start gap-3">
              <ShieldCheck className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
              <div className="leading-relaxed">
                Transactional credentials and email scheduling intervals are securely linked. Ensure your <strong>Sender Address</strong> is verified in your Mailjet organization console.
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className={labelCls}>Verified Dispatch From Email *</label>
                <input type="email" className={inputCls} value={settings.fromEmail} onChange={set('fromEmail')} placeholder="support@domain.com" />
              </div>
              <div>
                <label className={labelCls}>Verified Sender Display Name</label>
                <input className={inputCls} value={settings.fromName} onChange={set('fromName')} placeholder="Credit Acceleration Team" />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className={labelCls}>Mailjet API Key</label>
                <input className={inputCls} value={settings.mailjetApiKey} onChange={set('mailjetApiKey')} />
              </div>
              <div>
                <label className={labelCls}>Mailjet Secret Key</label>
                <input type="password" className={inputCls} value={settings.mailjetSecretKey} onChange={set('mailjetSecretKey')} placeholder="***masked***" />
              </div>
            </div>

            <div className="pt-2">
              <a 
                href="https://app.mailjet.com/account/sender" 
                target="_blank" 
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 text-xs text-indigo-400 hover:text-indigo-300 font-medium transition-colors"
              >
                <span>Verify Mailjet Sender Domain</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>

          {/* Save Button */}
          <button 
            onClick={save} 
            disabled={saving}
            className={`w-full py-3.5 rounded-xl font-bold text-xs uppercase tracking-wider text-white transition-all shadow-lg flex items-center justify-center gap-2 ${
              saved 
                ? 'bg-gradient-to-r from-emerald-600 to-teal-600 shadow-emerald-600/25' 
                : 'bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 shadow-indigo-600/25'
            } disabled:opacity-50`}
          >
            {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : saved ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}
            <span>{saving ? 'Persisting Configuration...' : saved ? 'Configuration Saved!' : 'Save System Settings'}</span>
          </button>
        </div>
      )}
    </div>
  );
}
