import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { AlertCircle, Building2, DollarSign, Loader2, PlusCircle, ShieldCheck, X } from 'lucide-react';
import { useAccount } from '../context/AccountContext';
import { accountsApi } from '../services/api';
import { BrokerType, Currency, TradingAccountCreatePayload } from '../types';

interface NewAccountModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const PRESET_BALANCES = [
  { label: '$25K', value: '25000.00' },
  { label: '$50K', value: '50000.00' },
  { label: '$100K', value: '100000.00' },
  { label: '$200K', value: '200000.00' },
];

export const NewAccountModal: React.FC<NewAccountModalProps> = ({ isOpen, onClose }) => {
  const queryClient = useQueryClient();
  const { setSelectedAccountId } = useAccount();

  const [name, setName] = useState<string>('');
  const [brokerType, setBrokerType] = useState<BrokerType>('PropFirm');
  const [initialBalance, setInitialBalance] = useState<string>('100000.00');
  const [currency, setCurrency] = useState<Currency>('USD');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: (payload: TradingAccountCreatePayload) => accountsApi.create(payload),
    onSuccess: (newAccount) => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      setSelectedAccountId(newAccount.id);
      onClose();
      resetForm();
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail || err.message || 'Failed to create account';
      setErrorMsg(typeof msg === 'string' ? msg : JSON.stringify(msg));
    },
  });

  const resetForm = () => {
    setName('');
    setBrokerType('PropFirm');
    setInitialBalance('100000.00');
    setCurrency('USD');
    setErrorMsg(null);
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    const trimmedName = name.trim();
    if (!trimmedName || trimmedName.length < 2) {
      setErrorMsg('Account name must be at least 2 characters long.');
      return;
    }

    const balNum = parseFloat(initialBalance);
    if (isNaN(balNum) || balNum <= 0) {
      setErrorMsg('Initial balance must be a valid positive number.');
      return;
    }

    createMutation.mutate({
      name: trimmedName,
      broker_type: brokerType,
      initial_balance: balNum.toFixed(2),
      currency,
    });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-lg rounded-2xl bg-brand-card border border-brand-border shadow-2xl p-6 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-brand-border">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <PlusCircle className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-100">Add Trading Account</h2>
              <p className="text-xs text-brand-muted">
                Connect a new prop firm challenge, funded account, or personal portfolio.
              </p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-brand-surface transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Error Banner */}
        {errorMsg && (
          <div className="mt-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center space-x-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          {/* Account Name */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Account Label / Name
            </label>
            <div className="relative">
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. FTMO 100k Swing, Bulenox 50k, IBKR Personal"
                className="w-full px-3.5 py-2.5 rounded-xl bg-brand-surface border border-brand-border text-slate-100 placeholder-slate-500 text-xs focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all"
                required
              />
            </div>
          </div>

          {/* Broker Type & Currency Grid */}
          <div className="grid grid-cols-2 gap-3">
            {/* Broker Type */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Broker / Account Type
              </label>
              <div className="relative">
                <select
                  value={brokerType}
                  onChange={(e) => setBrokerType(e.target.value as BrokerType)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-brand-surface border border-brand-border text-slate-200 text-xs focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all appearance-none cursor-pointer"
                >
                  <option value="PropFirm">Prop Firm (Funded / Evaluation)</option>
                  <option value="Personal">Personal (Direct Broker)</option>
                </select>
                <div className="absolute right-3.5 top-3 pointer-events-none text-slate-400">
                  <Building2 className="h-4 w-4" />
                </div>
              </div>
            </div>

            {/* Currency */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Base Currency
              </label>
              <div className="relative">
                <select
                  value={currency}
                  onChange={(e) => setCurrency(e.target.value as Currency)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-brand-surface border border-brand-border text-slate-200 text-xs focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all appearance-none cursor-pointer"
                >
                  <option value="USD">USD ($)</option>
                  <option value="EUR">EUR (€)</option>
                </select>
                <div className="absolute right-3.5 top-3 pointer-events-none text-slate-400">
                  <DollarSign className="h-4 w-4" />
                </div>
              </div>
            </div>
          </div>

          {/* Initial Balance */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="block text-xs font-semibold text-slate-300">
                Starting Capital / Balance ({currency})
              </label>
              <div className="flex items-center space-x-1">
                {PRESET_BALANCES.map((p) => (
                  <button
                    key={p.label}
                    type="button"
                    onClick={() => setInitialBalance(p.value)}
                    className="px-2 py-0.5 rounded bg-brand-surface border border-brand-border text-[10px] font-mono text-slate-400 hover:text-emerald-400 hover:border-emerald-500/40 transition-colors"
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="relative">
              <input
                type="number"
                step="0.01"
                min="1"
                value={initialBalance}
                onChange={(e) => setInitialBalance(e.target.value)}
                placeholder="100000.00"
                className="w-full px-3.5 py-2.5 rounded-xl bg-brand-surface border border-brand-border text-slate-100 placeholder-slate-500 text-xs font-mono focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all"
                required
              />
              <div className="absolute right-3.5 top-2.5 text-xs font-mono text-slate-400">
                {currency}
              </div>
            </div>
          </div>

          {/* Features note */}
          <div className="p-3 rounded-xl bg-brand-surface/60 border border-brand-border/60 text-[11px] text-brand-muted flex items-start space-x-2.5">
            <ShieldCheck className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
            <p>
              Once created, you can instantly journal trades, view real-time risk analytics, and track equity curves for this account.
            </p>
          </div>

          {/* Form Actions */}
          <div className="flex items-center justify-end space-x-3 pt-3 border-t border-brand-border">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 rounded-xl text-xs font-medium text-slate-300 hover:text-slate-100 hover:bg-brand-surface transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="flex items-center space-x-2 px-5 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-brand-dark font-semibold text-xs transition-all shadow-md shadow-emerald-500/20 active:scale-95"
            >
              {createMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Creating Account...</span>
                </>
              ) : (
                <>
                  <PlusCircle className="h-4 w-4 stroke-[2.5]" />
                  <span>Create Account</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
