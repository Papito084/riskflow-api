import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowDownRight, ArrowUpRight, PlusCircle, X } from 'lucide-react';
import { useAccount } from '../context/AccountContext';
import { tradesApi } from '../services/api';
import { TradeCreatePayload, TradeDirection, TradeStatus } from '../types';

interface NewTradeModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const PRESET_ASSETS = [
  { symbol: 'XAUUSD', name: 'Gold / USD', defaultPrice: '2350.50', defaultLot: '2.0' },
  { symbol: 'EURUSD', name: 'Euro / USD', defaultPrice: '1.0850', defaultLot: '1.0' },
  { symbol: 'US100', name: 'Nasdaq 100', defaultPrice: '19200.00', defaultLot: '0.5' },
  { symbol: 'BTCUSD', name: 'Bitcoin', defaultPrice: '64500.00', defaultLot: '0.1' },
];

export const NewTradeModal: React.FC<NewTradeModalProps> = ({ isOpen, onClose }) => {
  const { selectedAccount } = useAccount();
  const queryClient = useQueryClient();

  const [symbol, setSymbol] = useState<string>('XAUUSD');
  const [direction, setDirection] = useState<TradeDirection>('BUY');
  const [entryPrice, setEntryPrice] = useState<string>('2350.50');
  const [lotSize, setLotSize] = useState<string>('1.0');
  const [status, setStatus] = useState<TradeStatus>('OPEN');
  const [exitPrice, setExitPrice] = useState<string>('');
  const [pnl, setPnl] = useState<string>('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: (payload: TradeCreatePayload) => tradesApi.create(payload),
    onSuccess: () => {
      if (selectedAccount) {
        queryClient.invalidateQueries({ queryKey: ['analytics', selectedAccount.id] });
        queryClient.invalidateQueries({ queryKey: ['trades', selectedAccount.id] });
        queryClient.invalidateQueries({ queryKey: ['accounts'] });
      }
      onClose();
      resetForm();
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail || err.message || 'Failed to register trade';
      setErrorMsg(typeof msg === 'string' ? msg : JSON.stringify(msg));
    },
  });

  const resetForm = () => {
    setSymbol('XAUUSD');
    setDirection('BUY');
    setEntryPrice('2350.50');
    setLotSize('1.0');
    setStatus('OPEN');
    setExitPrice('');
    setPnl('');
    setErrorMsg(null);
  };

  if (!isOpen || !selectedAccount) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    const payload: TradeCreatePayload = {
      account_id: selectedAccount.id,
      symbol: symbol.toUpperCase().trim(),
      direction,
      entry_price: entryPrice,
      lot_size: lotSize,
      status,
    };

    if (status === 'CLOSED') {
      if (!exitPrice) {
        setErrorMsg('Exit price is required for closed trades');
        return;
      }
      payload.exit_price = exitPrice;
      payload.pnl = pnl || null;
    }

    createMutation.mutate(payload);
  };

  const applyPreset = (preset: (typeof PRESET_ASSETS)[0]) => {
    setSymbol(preset.symbol);
    setEntryPrice(preset.defaultPrice);
    setLotSize(preset.defaultLot);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-lg bg-brand-card border border-brand-border rounded-2xl shadow-2xl p-6 relative">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-slate-400 hover:text-slate-200 transition-colors"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Modal Header */}
        <div className="flex items-center space-x-2.5 mb-5">
          <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <PlusCircle className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100">Ingest Trade Position</h2>
            <p className="text-xs text-brand-muted">
              Target Portfolio: <span className="text-slate-300 font-medium">{selectedAccount.name}</span>
            </p>
          </div>
        </div>

        {errorMsg && (
          <div className="mb-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-mono">
            {errorMsg}
          </div>
        )}

        {/* Quick Presets */}
        <div className="mb-4">
          <label className="block text-[11px] font-semibold text-brand-muted uppercase tracking-wider mb-1.5">
            Quick Asset Presets
          </label>
          <div className="grid grid-cols-4 gap-2">
            {PRESET_ASSETS.map((p) => (
              <button
                key={p.symbol}
                type="button"
                onClick={() => applyPreset(p)}
                className={`px-2.5 py-1.5 rounded-lg border text-xs font-mono text-center transition-all ${
                  symbol === p.symbol
                    ? 'border-emerald-500 bg-emerald-500/10 text-emerald-400 font-bold'
                    : 'border-brand-border bg-brand-surface text-slate-400 hover:border-slate-600'
                }`}
              >
                {p.symbol}
              </button>
            ))}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          {/* Symbol & Direction */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-brand-muted mb-1 font-medium">Asset Symbol</label>
              <input
                type="text"
                required
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                placeholder="e.g. XAUUSD"
                className="w-full bg-brand-surface border border-brand-border rounded-lg px-3 py-2 text-slate-100 font-mono focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-brand-muted mb-1 font-medium">Direction</label>
              <div className="grid grid-cols-2 gap-1.5">
                <button
                  type="button"
                  onClick={() => setDirection('BUY')}
                  className={`py-2 rounded-lg font-bold flex items-center justify-center space-x-1 transition-all ${
                    direction === 'BUY'
                      ? 'bg-emerald-500 text-brand-dark shadow-lg shadow-emerald-500/20'
                      : 'bg-brand-surface text-slate-400 border border-brand-border hover:text-slate-200'
                  }`}
                >
                  <ArrowUpRight className="h-4 w-4" />
                  <span>BUY</span>
                </button>
                <button
                  type="button"
                  onClick={() => setDirection('SELL')}
                  className={`py-2 rounded-lg font-bold flex items-center justify-center space-x-1 transition-all ${
                    direction === 'SELL'
                      ? 'bg-rose-500 text-brand-dark shadow-lg shadow-rose-500/20'
                      : 'bg-brand-surface text-slate-400 border border-brand-border hover:text-slate-200'
                  }`}
                >
                  <ArrowDownRight className="h-4 w-4" />
                  <span>SELL</span>
                </button>
              </div>
            </div>
          </div>

          {/* Entry Price & Lot Size */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-brand-muted mb-1 font-medium">Entry Price ($)</label>
              <input
                type="number"
                step="any"
                required
                value={entryPrice}
                onChange={(e) => setEntryPrice(e.target.value)}
                className="w-full bg-brand-surface border border-brand-border rounded-lg px-3 py-2 text-slate-100 font-mono focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="block text-brand-muted mb-1 font-medium">Volume (Lots)</label>
              <input
                type="number"
                step="any"
                required
                value={lotSize}
                onChange={(e) => setLotSize(e.target.value)}
                className="w-full bg-brand-surface border border-brand-border rounded-lg px-3 py-2 text-slate-100 font-mono focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          {/* Trade Status (OPEN vs CLOSED) */}
          <div>
            <label className="block text-brand-muted mb-1 font-medium">Position Status</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setStatus('OPEN')}
                className={`py-1.5 rounded-lg border font-mono font-medium transition-all ${
                  status === 'OPEN'
                    ? 'border-amber-500 bg-amber-500/10 text-amber-400 font-bold'
                    : 'border-brand-border bg-brand-surface text-slate-400'
                }`}
              >
                OPEN (Active Position)
              </button>
              <button
                type="button"
                onClick={() => setStatus('CLOSED')}
                className={`py-1.5 rounded-lg border font-mono font-medium transition-all ${
                  status === 'CLOSED'
                    ? 'border-emerald-500 bg-emerald-500/10 text-emerald-400 font-bold'
                    : 'border-brand-border bg-brand-surface text-slate-400'
                }`}
              >
                CLOSED (Historical / Finalized)
              </button>
            </div>
          </div>

          {/* Optional Closed fields */}
          {status === 'CLOSED' && (
            <div className="grid grid-cols-2 gap-3 pt-2 border-t border-brand-border/60">
              <div>
                <label className="block text-brand-muted mb-1 font-medium">Exit Price ($)</label>
                <input
                  type="number"
                  step="any"
                  required
                  value={exitPrice}
                  onChange={(e) => setExitPrice(e.target.value)}
                  placeholder="e.g. 2375.00"
                  className="w-full bg-brand-surface border border-brand-border rounded-lg px-3 py-2 text-slate-100 font-mono focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div>
                <label className="block text-brand-muted mb-1 font-medium">Realized PnL ($)</label>
                <input
                  type="number"
                  step="any"
                  value={pnl}
                  onChange={(e) => setPnl(e.target.value)}
                  placeholder="Auto-calculated if blank"
                  className="w-full bg-brand-surface border border-brand-border rounded-lg px-3 py-2 text-slate-100 font-mono focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>
          )}

          {/* Submit Actions */}
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
              disabled={createMutation.isPending}
              className="px-5 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-brand-dark font-bold transition-all shadow-lg shadow-emerald-500/20 active:scale-95 disabled:opacity-50"
            >
              {createMutation.isPending ? 'Ingesting...' : 'Ingest Trade'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
