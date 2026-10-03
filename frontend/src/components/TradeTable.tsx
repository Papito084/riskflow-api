import React, { useState } from 'react';
import { ArrowDownRight, ArrowUpRight, CheckCircle2, Clock, Filter, Search, XCircle } from 'lucide-react';
import { Trade, TradeStatus } from '../types';

interface TradeTableProps {
  trades: Trade[];
  isLoading: boolean;
  onCloseTradeClick: (trade: Trade) => void;
}

export const TradeTable: React.FC<TradeTableProps> = ({ trades, isLoading, onCloseTradeClick }) => {
  const [filterStatus, setFilterStatus] = useState<TradeStatus | 'ALL'>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const filteredTrades = trades.filter((t) => {
    const matchesStatus = filterStatus === 'ALL' || t.status === filterStatus;
    const matchesSymbol = t.symbol.toLowerCase().includes(searchTerm.toLowerCase().trim());
    return matchesStatus && matchesSymbol;
  });

  return (
    <div className="glass-panel rounded-xl border border-brand-border/80 overflow-hidden">
      {/* Header and Filter Controls */}
      <div className="p-4 sm:p-5 border-b border-brand-border/60 flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="flex items-center space-x-2">
          <Filter className="h-4 w-4 text-emerald-400" />
          <h3 className="text-sm font-bold text-slate-100 tracking-tight">Trading Journal & Log</h3>
          <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">
            {filteredTrades.length} trades
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {/* Status Segmented Buttons */}
          <div className="flex items-center bg-brand-surface rounded-lg p-1 border border-brand-border text-xs">
            {(['ALL', 'OPEN', 'CLOSED'] as const).map((st) => (
              <button
                key={st}
                onClick={() => setFilterStatus(st)}
                className={`px-3 py-1 rounded-md transition-all font-medium ${
                  filterStatus === st
                    ? 'bg-brand-card text-emerald-400 shadow font-semibold'
                    : 'text-brand-muted hover:text-slate-200'
                }`}
              >
                {st === 'ALL' ? 'All' : st === 'OPEN' ? 'Open Positions' : 'Closed'}
              </button>
            ))}
          </div>

          {/* Search Box */}
          <div className="relative">
            <Search className="h-3.5 w-3.5 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Filter symbol (e.g. XAUUSD)..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-brand-surface border border-brand-border rounded-lg pl-8 pr-3 py-1 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500/50 w-44 font-mono"
            />
          </div>
        </div>
      </div>

      {/* Table Content */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-brand-border/60 bg-brand-surface/50 text-[11px] font-semibold text-brand-muted uppercase tracking-wider">
              <th className="py-3 px-4">Asset</th>
              <th className="py-3 px-4">Direction</th>
              <th className="py-3 px-4">Size (Lots)</th>
              <th className="py-3 px-4">Entry</th>
              <th className="py-3 px-4">Exit</th>
              <th className="py-3 px-4">Realized PnL</th>
              <th className="py-3 px-4">Date Executed</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-brand-border/40 font-mono">
            {isLoading ? (
              [...Array(5)].map((_, i) => (
                <tr key={i} className="animate-pulse">
                  <td colSpan={9} className="py-4 px-4">
                    <div className="h-4 bg-slate-800/60 rounded"></div>
                  </td>
                </tr>
              ))
            ) : filteredTrades.length === 0 ? (
              <tr>
                <td colSpan={9} className="py-12 text-center text-brand-muted text-xs">
                  No trades found matching current criteria.
                </td>
              </tr>
            ) : (
              filteredTrades.map((trade) => {
                const isBuy = trade.direction === 'BUY';
                const hasPnl = trade.pnl !== null;
                const pnlNum = Number(trade.pnl || 0);
                const isProfitable = pnlNum > 0;
                const isLoss = pnlNum < 0;

                return (
                  <tr
                    key={trade.id}
                    className="hover:bg-brand-surface/40 transition-colors group"
                  >
                    {/* Symbol */}
                    <td className="py-3 px-4 font-bold text-slate-200 flex items-center space-x-1.5">
                      <span>{trade.symbol}</span>
                    </td>

                    {/* Direction */}
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-semibold ${
                          isBuy
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                        }`}
                      >
                        {isBuy ? (
                          <ArrowUpRight className="h-3 w-3" />
                        ) : (
                          <ArrowDownRight className="h-3 w-3" />
                        )}
                        <span>{trade.direction}</span>
                      </span>
                    </td>

                    {/* Lot Size */}
                    <td className="py-3 px-4 text-slate-300">{Number(trade.lot_size).toFixed(2)}</td>

                    {/* Entry Price */}
                    <td className="py-3 px-4 text-slate-300">${Number(trade.entry_price).toFixed(4)}</td>

                    {/* Exit Price */}
                    <td className="py-3 px-4 text-slate-400">
                      {trade.exit_price ? `$${Number(trade.exit_price).toFixed(4)}` : '—'}
                    </td>

                    {/* Realized PnL */}
                    <td className="py-3 px-4 font-bold">
                      {hasPnl ? (
                        <span
                          className={`${
                            isProfitable
                              ? 'text-emerald-400'
                              : isLoss
                              ? 'text-rose-400'
                              : 'text-slate-400'
                          }`}
                        >
                          {pnlNum > 0 ? '+' : ''}${pnlNum.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                        </span>
                      ) : (
                        <span className="text-slate-500 text-[11px]">Active</span>
                      )}
                    </td>

                    {/* Date */}
                    <td className="py-3 px-4 text-slate-400 text-[11px] whitespace-nowrap">
                      {new Date(trade.opened_at).toLocaleDateString()} {new Date(trade.opened_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>

                    {/* Status */}
                    <td className="py-3 px-4">
                      {trade.status === 'OPEN' ? (
                        <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                          <Clock className="h-3 w-3 animate-spin" />
                          <span>OPEN</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-800 text-slate-400 border border-slate-700">
                          <CheckCircle2 className="h-3 w-3" />
                          <span>CLOSED</span>
                        </span>
                      )}
                    </td>

                    {/* Action */}
                    <td className="py-3 px-4 text-right">
                      {trade.status === 'OPEN' ? (
                        <button
                          onClick={() => onCloseTradeClick(trade)}
                          className="px-2.5 py-1 rounded bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 text-[11px] font-semibold transition-all active:scale-95 flex items-center space-x-1 ml-auto"
                        >
                          <XCircle className="h-3 w-3" />
                          <span>Close</span>
                        </button>
                      ) : (
                        <span className="text-slate-600 text-[11px]">Finalized</span>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
