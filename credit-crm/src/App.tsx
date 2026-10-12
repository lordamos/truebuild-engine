import React, { useState, useEffect } from 'react';
import { Dashboard } from './pages/Dashboard';
import { ClientDetail } from './pages/ClientDetail';
import { NewClient } from './pages/NewClient';
import { Settings } from './pages/Settings';
import { IntakeForm } from './pages/IntakeForm';
import { 
  LayoutDashboard, 
  UserPlus, 
  Settings as SettingsIcon, 
  ShieldCheck, 
  Sparkles,
  Zap
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export type Page =
  | { name: 'dashboard' }
  | { name: 'client'; id: string }
  | { name: 'new-client' }
  | { name: 'settings' }
  | { name: 'intake'; token: string };

export default function App() {
  const [page, setPage] = useState<Page>({ name: 'dashboard' });

  // Simple hash-based routing
  useEffect(() => {
    const onHash = () => {
      const hash = window.location.hash;
      if (hash.startsWith('#/client/')) {
        setPage({ name: 'client', id: hash.replace('#/client/', '') });
      } else if (hash.startsWith('#/intake/')) {
        setPage({ name: 'intake', token: hash.replace('#/intake/', '') });
      } else if (hash === '#/new') {
        setPage({ name: 'new-client' });
      } else if (hash === '#/settings') {
        setPage({ name: 'settings' });
      } else {
        setPage({ name: 'dashboard' });
      }
    };
    window.addEventListener('hashchange', onHash);
    onHash();
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

  const navigate = (p: Page) => {
    if (p.name === 'dashboard') window.location.hash = '#/';
    else if (p.name === 'client') window.location.hash = `#/client/${p.id}`;
    else if (p.name === 'new-client') window.location.hash = '#/new';
    else if (p.name === 'settings') window.location.hash = '#/settings';
    setPage(p);
  };

  // Intake route doesn't get the global nav
  if (page.name === 'intake') {
    return <IntakeForm token={page.token} />;
  }

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'new-client', label: 'New Client', icon: UserPlus },
    { id: 'settings', label: 'Settings', icon: SettingsIcon },
  ];

  return (
    <div className="flex flex-col min-h-screen bg-slate-950 text-slate-100 selection:bg-indigo-500/30 selection:text-indigo-200">
      {/* Premium Glass Top Navigation */}
      <nav className="glass-panel sticky top-0 z-50 border-b border-slate-800/80 px-6 py-3.5 transition-all">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          
          {/* Logo & Brand */}
          <button 
            onClick={() => navigate({ name: 'dashboard' })} 
            className="flex items-center gap-3.5 group text-left focus:outline-none"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-violet-500 p-0.5 shadow-lg shadow-indigo-500/25 group-hover:shadow-indigo-500/40 transition-all duration-300 transform group-hover:scale-105 flex items-center justify-center">
              <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                <Zap className="w-5 h-5 text-indigo-400 fill-indigo-400/20 group-hover:text-indigo-300 transition-colors" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-base tracking-tight text-white group-hover:text-indigo-300 transition-colors">
                  Credit Acceleration
                </span>
                <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-full bg-indigo-500/15 text-indigo-300 border border-indigo-500/30">
                  CRM Pro
                </span>
              </div>
              <div className="text-[11px] font-medium text-slate-400 flex items-center gap-1.5">
                <ShieldCheck className="w-3 h-3 text-emerald-400" />
                <span>Sumthin3lse Global · Brevard County, FL</span>
              </div>
            </div>
          </button>

          {/* Navigation Actions */}
          <div className="flex items-center gap-2 bg-slate-900/60 p-1.5 rounded-2xl border border-slate-800/80 backdrop-blur-md">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = page.name === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => navigate({ name: item.id as any })}
                  className={`relative px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all duration-200 ${
                    isActive
                      ? 'text-white shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                  }`}
                >
                  {isActive && (
                    <motion.div
                      layoutId="activeNavIndicator"
                      className="absolute inset-0 bg-gradient-to-r from-indigo-600 to-violet-600 rounded-xl shadow-md shadow-indigo-600/30"
                      transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                    />
                  )}
                  <span className="relative z-10 flex items-center gap-2">
                    <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                    <span>{item.label}</span>
                  </span>
                </button>
              );
            })}
          </div>

        </div>
      </nav>

      {/* Main Content Area with Route Transitions */}
      <main className="flex-1 overflow-auto">
        <AnimatePresence mode="wait">
          <motion.div
            key={page.name + (page.name === 'client' ? page.id : '')}
            initial={{ opacity: 0, y: 12, filter: 'blur(4px)' }}
            animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
            exit={{ opacity: 0, y: -12, filter: 'blur(4px)' }}
            transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
            className="w-full h-full"
          >
            {page.name === 'dashboard' && <Dashboard navigate={navigate} />}
            {page.name === 'client' && <ClientDetail clientId={page.id} navigate={navigate} />}
            {page.name === 'new-client' && <NewClient navigate={navigate} />}
            {page.name === 'settings' && <Settings />}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}
