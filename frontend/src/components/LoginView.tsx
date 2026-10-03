import React, { useState } from 'react';
import { Activity, ArrowRight, Loader2, Lock, Mail, ShieldAlert, Sparkles } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const LoginView: React.FC = () => {
  const { login } = useAuth();
  const [email, setEmail] = useState<string>('demo@riskflow.io');
  const [password, setPassword] = useState<string>('DemoPassword123!');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await login(email, password);
    } catch (err: any) {
      if (err.response?.status === 401) {
        const detail = err.response.data?.detail;
        setError(detail || 'Invalid email or password. Please verify your credentials.');
      } else if (err.code === 'ERR_NETWORK' || !err.response) {
        setError('Cannot connect to RiskFlow backend. Ensure the API service is running on port 8000.');
      } else {
        const msg =
          err.response?.data?.detail ||
          err.response?.data?.error ||
          err.message ||
          'Authentication failed. Please verify your credentials.';
        setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const fillDemo = () => {
    setEmail('demo@riskflow.io');
    setPassword('DemoPassword123!');
    setError(null);
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center p-4 relative overflow-hidden bg-brand-dark">
      {/* Background Decorative Glows */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-teal-500/10 rounded-full blur-3xl pointer-events-none"></div>

      <div className="w-full max-w-md z-10">
        {/* Brand Card Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center h-14 w-14 rounded-2xl bg-gradient-to-tr from-emerald-600 to-teal-400 p-[1px] shadow-xl shadow-emerald-500/20 mb-4">
            <div className="h-full w-full bg-brand-card rounded-[15px] flex items-center justify-center">
              <Activity className="h-7 w-7 text-emerald-400" />
            </div>
          </div>
          <h1 className="text-2xl font-extrabold tracking-tight text-white">RiskFlow Terminal</h1>
          <p className="text-sm text-brand-muted mt-1">
            Real-Time Trading Journal & Portfolio Risk Analytics
          </p>
        </div>

        {/* Login Form Box */}
        <div className="glass-panel p-8 rounded-2xl border border-brand-border/80 shadow-2xl relative">
          {error && (
            <div className="mb-5 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-start space-x-2.5 shadow-sm animate-fade-in">
              <ShieldAlert className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" />
              <div className="flex-1 font-medium">{error}</div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Trader Email
              </label>
              <div className="relative">
                <Mail className="h-4 w-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  required
                  disabled={isSubmitting}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="trader@example.com"
                  className="w-full bg-brand-surface border border-brand-border rounded-xl pl-9 pr-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 font-mono transition-colors disabled:opacity-50"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="h-4 w-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  required
                  disabled={isSubmitting}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-brand-surface border border-brand-border rounded-xl pl-9 pr-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 font-mono transition-colors disabled:opacity-50"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-brand-dark font-bold text-sm transition-all shadow-lg shadow-emerald-500/20 active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center space-x-2 mt-2"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin text-brand-dark" />
                  <span>Authenticating...</span>
                </>
              ) : (
                <>
                  <span>Enter Trading Terminal</span>
                  <ArrowRight className="h-4 w-4 stroke-[2.5]" />
                </>
              )}
            </button>
          </form>

          {/* Quick Demo Pre-fill */}
          <div className="mt-6 pt-5 border-t border-brand-border/60 text-center">
            <button
              type="button"
              onClick={fillDemo}
              disabled={isSubmitting}
              className="inline-flex items-center space-x-1.5 text-xs text-emerald-400 hover:text-emerald-300 transition-colors font-medium disabled:opacity-50"
            >
              <Sparkles className="h-3.5 w-3.5" />
              <span>Fill Seeded Demo Credentials</span>
            </button>
            <p className="text-[11px] text-brand-muted mt-1 font-mono">
              demo@riskflow.io / DemoPassword123!
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
