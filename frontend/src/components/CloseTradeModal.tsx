import React, { useEffect, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { CheckCircle2, DollarSign, X } from 'lucide-react';
import { useAccount } from '../context/AccountContext';
import { tradesApi } from '../services/api';
import { Trade, TradeClosePayload } from '../types';

interface CloseTradeModalProps {
  trade: Trade | null;
  isOpen: boolean;
  onClose: () => void;
}

export const CloseTradeModal: React.FC<CloseTradeModalProps> = ({ trade, isOpen, onClose }) => {
  const { selectedAccount } = useAccount();
  const queryClient = useQueryClient();

  const [exitPrice, setExitPrice] = useState<string>('');
  const [pnl, setPnl] = useState<string>('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (trade) {
      setExitPrice(trade.entry_price);
      setPnl('0.00');
      setErrorMsg(null);
    }
  }, [trade]);

  const closeMutation = useMutation({
    mutationFn: (payload: TradeClosePayload) => {
      if (!trade) throw new Error('No trade selected');
      return tradesApi.close(trade.id, payload);
    },
    onSuccess: () => {
      if (selectedAccount) {
        queryClient.invalidateQueries({ queryKey: ['analytics', selectedAccount.id] });
        queryClient.invalidateQueries({ queryKey: ['trades', selectedAccount.id] });
        queryClient.invalidateQueries({ queryKey: ['accounts'] });
      }
      onClose();
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail || err.message || 'Failed to close trade';
      setErrorMsg(typeof msg === 'string' ? msg : JSON.stringify(msg));
    },
  });

  if (!isOpen || !trade) return null;

  // Real-time calculation helper
  const handleExitPriceChange = (val: string) => {
    setExitPrice(val);
    const exitNum = parseFloat(val);
    const entryNum = parseFloat(trade.entry_price);
    const lotNum = parseFloat(trade.lot_size);

    if (!isNaN(exitNum) && !isNaN(entryNum) && !isNaN(lotNum)) {
      const delta = trade.direction === 'BUY' ? exitNum - entryNum : entryNum - exitNum;
      // Default standard financial lot multiplier
      const multiplier = trade.symbol.includes('XAU') ? 100 : trade.symbol.includes('US100') ? 20 : 1000;
      const computedPnl = delta * lotNum * multiplier;
      setPnl(computedPnl.toFixed(2));
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!exitPrice) {
      setErrorMsg('Please specify an exit price');
      return;
    }

    closeMutation.mutate({
      exit_price: exitPrice,
      pnl: pnl ? pnl : null,
    });
  };

  const pnlNumber = parseFloat(pnl || '0');
  const isProfitable = pnlNumber > 0;
  const isLoss = pnlNumber < 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-md bg-brand-card border border-brand-border rounded-2xl shadow-2xl p-6 relative">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-slate-400 hover:text-slate-200 transition-colors"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="flex items-center space-x-2.5 mb-4">
          <div className="p-2 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <CheckCircle2 className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100">Close Position</h2>
            <p className="text-xs text-brand-muted font-mono">
              {trade.direction} {trade.symbol} • {trade.lot_size} Lots
            </p>
          </div>
        </div>

        {errorMsg && (
          <div className="mb-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-mono">
            {errorMsg}
          </div>
        )}

        {/* Position Summary Card */}
        <div className="mb-4 p-3 rounded-xl bg-brand-surface border border-brand-border text-xs font-mono space-y-1">
          <div className="flex justify-between text-brand-muted">
            <span>Entry Price:</span>
            <span className="text-slate-200">${Number(trade.entry_price).toFixed(4)}</span>
          </div>
          <div className="flex justify-between text-brand-muted">
            <span>Opened At:</span>
            <span className="text-slate-200">{new Date(trade.opened_at).toLocaleString()}</span>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block text-brand-muted mb-1 font-medium">Exit Execution Price ($)</label>
            <input
              type="number"
              step="any"
              required
              value={exitPrice}
              onChange={(e) => handleExitPriceChange(e.target.value)}
              className="w-full bg-brand-surface border border-brand-border rounded-lg px-3 py-2 text-slate-100 font-mono text-sm focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="block text-brand-muted mb-1 font-medium">Realized PnL ($)</label>
            <div className="relative">
              <input
                type="number"
                step="any"
                required
                value={pnl}
                onChange={(e) => setPnl(e.target.value)}
                className={`w-full bg-brand-surface border rounded-lg pl-8 pr-3 py-2 font-mono font-bold text-sm focus:outline-none ${
                  isProfitable
                    ? 'border-emerald-500/50 text-emerald-400'
                    : isLoss
                    ? 'border-rose-500/50 text-rose-400'
                    : 'border-brand-border text-slate-200'
                }`}
              />
              <DollarSign className="h-4 w-4 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
            </div>
            <p className="text-[10px] text-brand-muted mt-1">
              Estimated outcome: {isProfitable ? 'Profit' : isLoss ? 'Loss' : 'Break-Even'}
            </p>
          </div>

          <div className="flex items-center justify-end space-x-2 pt-4 border-t border-brand-border/60">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-slate-400 hover:text-slate-200 transition-colors font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={closeMutation.isPending}
              className="px-5 py-2 rounded-lg bg-rose-500 hover:bg-rose-400 text-white font-bold transition-all shadow-lg shadow-rose-500/20 active:scale-95 disabled:opacity-50"
            >
              {closeMutation.isPending ? 'Closing...' : 'Confirm & Realize'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
