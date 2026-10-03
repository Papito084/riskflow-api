import React, { useEffect, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { AlertCircle, Building2, Check, Loader2, Settings, Shield, X } from 'lucide-react';
import { accountsApi } from '../services/api';
import { BrokerType, TradingAccount, TradingAccountUpdatePayload } from '../types';

interface EditAccountModalProps {
  account: TradingAccount | null;
  isOpen: boolean;
  onClose: () => void;
}

export const EditAccountModal: React.FC<EditAccountModalProps> = ({
  account,
  isOpen,
  onClose,
}) => {
  const queryClient = useQueryClient();

  const [name, setName] = useState<string>('');
  const [brokerType, setBrokerType] = useState<BrokerType>('PropFirm');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (account) {
      setName(account.name);
      setBrokerType(account.broker_type);
      setErrorMsg(null);
    }
  }, [account]);

  const updateMutation = useMutation({
    mutationFn: (payload: TradingAccountUpdatePayload) => {
      if (!account) throw new Error('No account selected for editing');
      return accountsApi.update(account.id, payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      onClose();
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail || err.message || 'Failed to update account';
      setErrorMsg(typeof msg === 'string' ? msg : JSON.stringify(msg));
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    const trimmedName = name.trim();
    if (!trimmedName || trimmedName.length < 2) {
      setErrorMsg('Account name must be at least 2 characters long.');
      return;
    }

    updateMutation.mutate({
      name: trimmedName,
      broker_type: brokerType,
    });
  };

  if (!isOpen || !account) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-lg rounded-2xl bg-brand-card border border-brand-border shadow-2xl p-6 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-brand-border">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400">
              <Settings className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-100">Account Settings</h2>
              <p className="text-xs text-brand-muted">
                Configure account preferences and classification.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
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
          {/* Read-Only Account Summary Strip */}
          <div className="p-3 rounded-xl bg-brand-surface border border-brand-border/60 flex items-center justify-between">
            <div>
              <div className="text-[10px] uppercase font-semibold text-brand-muted tracking-wider">
                Current Balance
              </div>
              <div className="text-sm font-mono font-bold text-emerald-400">
                ${Number(account.current_balance).toLocaleString('en-US', { minimumFractionDigits: 2 })} {account.currency}
              </div>
            </div>
            <div className="text-right">
              <div className="text-[10px] uppercase font-semibold text-brand-muted tracking-wider">
                Starting Capital
              </div>
              <div className="text-xs font-mono text-slate-300">
                ${Number(account.initial_balance).toLocaleString('en-US', { minimumFractionDigits: 2 })} {account.currency}
              </div>
            </div>
          </div>

          {/* Account Name */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Account Label / Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. FTMO 100k Swing"
              className="w-full px-3.5 py-2.5 rounded-xl bg-brand-surface border border-brand-border text-slate-100 placeholder-slate-500 text-xs focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
              required
            />
          </div>

          {/* Broker Type */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Broker / Account Classification
            </label>
            <div className="relative">
              <select
                value={brokerType}
                onChange={(e) => setBrokerType(e.target.value as BrokerType)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-brand-surface border border-brand-border text-slate-200 text-xs focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all appearance-none cursor-pointer"
              >
                <option value="PropFirm">Prop Firm (Funded / Evaluation)</option>
                <option value="Personal">Personal (Direct Broker Portfolio)</option>
              </select>
              <div className="absolute right-3.5 top-3 pointer-events-none text-slate-400">
                <Building2 className="h-4 w-4" />
              </div>
            </div>
          </div>

          {/* Account ID / Info */}
          <div className="p-3 rounded-xl bg-brand-surface/40 border border-brand-border/40 text-[11px] text-brand-muted flex items-start space-x-2">
            <Shield className="h-4 w-4 text-blue-400 shrink-0 mt-0.5" />
            <div className="space-y-0.5">
              <p className="text-slate-300 font-medium">Account ID: <span className="font-mono text-slate-400">{account.id}</span></p>
              <p>Balance and performance metrics are mathematically calculated from trade history and cannot be edited manually.</p>
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex items-center justify-end space-x-3 pt-3 border-t border-brand-border">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-medium text-slate-300 hover:text-slate-100 hover:bg-brand-surface transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={updateMutation.isPending}
              className="flex items-center space-x-2 px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-semibold text-xs transition-all shadow-md shadow-blue-600/20 active:scale-95"
            >
              {updateMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Saving Changes...</span>
                </>
              ) : (
                <>
                  <Check className="h-4 w-4 stroke-[2.5]" />
                  <span>Save Settings</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
