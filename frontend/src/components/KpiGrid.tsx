import React from 'react';
import {
  AlertTriangle,
  Award,
  Database,
  DollarSign,
  Percent,
  Scale,
  TrendingDown,
  TrendingUp,
  Zap,
} from 'lucide-react';
import { RiskMetricsResponse } from '../types';

interface KpiGridProps {
  metrics: RiskMetricsResponse | null;
  isLoading: boolean;
}

export const KpiGrid: React.FC<KpiGridProps> = ({ metrics, isLoading }) => {
  if (isLoading || !metrics) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5 mb-6">
        {[...Array(6)].map((_, i) => (
          <div
            key={i}
            className="h-28 rounded-xl bg-brand-surface border border-brand-border animate-pulse p-4 flex flex-col justify-between"
          >
            <div className="h-3 w-16 bg-slate-800 rounded"></div>
            <div className="h-6 w-24 bg-slate-800 rounded"></div>
            <div className="h-2 w-20 bg-slate-800 rounded"></div>
          </div>
        ))}
      </div>
    );
  }

  const isNetProfitPositive = Number(metrics.net_profit) >= 0;
  const winRate = Number(metrics.win_rate_pct);

  return (
    <div className="mb-6 space-y-2">
      {/* Cache Status Bar */}
      <div className="flex items-center justify-between text-xs px-1 text-brand-muted">
        <div className="flex items-center space-x-2">
          {metrics.cached ? (
            <span className="inline-flex items-center space-x-1.5 px-2 py-0.5 rounded-full bg-cyan-950/40 text-cyan-400 border border-cyan-800/40 font-mono text-[11px]">
              <Database className="h-3 w-3" />
              <span>Redis Cached (60s TTL)</span>
            </span>
          ) : (
            <span className="inline-flex items-center space-x-1.5 px-2 py-0.5 rounded-full bg-amber-950/40 text-amber-400 border border-amber-800/40 font-mono text-[11px]">
              <Zap className="h-3 w-3" />
              <span>Real-Time Computed</span>
            </span>
          )}
          <span className="text-[11px]">
            {metrics.closed_trades} closed trades | {metrics.open_trades} open
          </span>
        </div>
        <span className="text-[11px] font-mono">
          Last sync: {new Date(metrics.calculated_at).toLocaleTimeString()}
        </span>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5">
        {/* 1. Win Rate */}
        <div className="glass-panel p-4 rounded-xl border border-brand-border/80 hover:border-brand-border transition-all">
          <div className="flex items-center justify-between text-brand-muted mb-2">
            <span className="text-[11px] font-medium uppercase tracking-wider">Win Rate</span>
            <Percent className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-100 mb-1">
            {winRate.toFixed(1)}%
          </div>
          <div className="flex items-center space-x-1.5 text-[11px] text-brand-muted">
            <span className="text-emerald-400 font-semibold">{metrics.winning_trades}W</span>
            <span>/</span>
            <span className="text-rose-400 font-semibold">{metrics.losing_trades}L</span>
          </div>
        </div>

        {/* 2. Net Realized PnL */}
        <div
          className={`glass-panel p-4 rounded-xl border transition-all ${
            isNetProfitPositive
              ? 'border-emerald-500/20 hover:border-emerald-500/40'
              : 'border-rose-500/20 hover:border-rose-500/40'
          }`}
        >
          <div className="flex items-center justify-between text-brand-muted mb-2">
            <span className="text-[11px] font-medium uppercase tracking-wider">Net Realized PnL</span>
            <DollarSign
              className={`h-4 w-4 ${isNetProfitPositive ? 'text-emerald-400' : 'text-rose-400'}`}
            />
          </div>
          <div
            className={`text-2xl font-bold font-mono mb-1 ${
              isNetProfitPositive ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            {isNetProfitPositive ? '+' : ''}${Number(metrics.net_profit).toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
          <div className="flex items-center space-x-1 text-[11px] text-brand-muted truncate">
            {isNetProfitPositive ? (
              <TrendingUp className="h-3 w-3 text-emerald-400 shrink-0" />
            ) : (
              <TrendingDown className="h-3 w-3 text-rose-400 shrink-0" />
            )}
            <span>Gross: +${Number(metrics.gross_profit).toLocaleString()}</span>
          </div>
        </div>

        {/* 3. Profit Factor */}
        <div className="glass-panel p-4 rounded-xl border border-brand-border/80 hover:border-brand-border transition-all">
          <div className="flex items-center justify-between text-brand-muted mb-2">
            <span className="text-[11px] font-medium uppercase tracking-wider">Profit Factor</span>
            <Scale className="h-4 w-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-100 mb-1">
            {metrics.profit_factor ? Number(metrics.profit_factor).toFixed(2) : '∞'}
          </div>
          <div className="text-[11px] text-brand-muted truncate">
            Loss: -${Number(metrics.gross_loss).toLocaleString()}
          </div>
        </div>

        {/* 4. Max Drawdown */}
        <div className="glass-panel p-4 rounded-xl border border-rose-500/20 hover:border-rose-500/40 transition-all">
          <div className="flex items-center justify-between text-brand-muted mb-2">
            <span className="text-[11px] font-medium uppercase tracking-wider">Max Drawdown</span>
            <AlertTriangle className="h-4 w-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-rose-400 mb-1">
            -{Number(metrics.max_drawdown_pct).toFixed(2)}%
          </div>
          <div className="text-[11px] text-brand-muted truncate">
            Peak-Trough: -${Number(metrics.max_drawdown_amount).toLocaleString()}
          </div>
        </div>

        {/* 5. Expectancy */}
        <div className="glass-panel p-4 rounded-xl border border-brand-border/80 hover:border-brand-border transition-all">
          <div className="flex items-center justify-between text-brand-muted mb-2">
            <span className="text-[11px] font-medium uppercase tracking-wider">Expectancy</span>
            <Award className="h-4 w-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-100 mb-1">
            ${Number(metrics.expectancy).toFixed(2)}
          </div>
          <div className="text-[11px] text-brand-muted truncate">
            Avg Win: ${Number(metrics.average_win).toFixed(0)}
          </div>
        </div>

        {/* 6. Risk / Reward Ratio */}
        <div className="glass-panel p-4 rounded-xl border border-brand-border/80 hover:border-brand-border transition-all">
          <div className="flex items-center justify-between text-brand-muted mb-2">
            <span className="text-[11px] font-medium uppercase tracking-wider">Risk / Reward (RRR)</span>
            <Zap className="h-4 w-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-100 mb-1">
            {metrics.risk_reward_ratio ? `1:${Number(metrics.risk_reward_ratio).toFixed(2)}` : 'N/A'}
          </div>
          <div className="text-[11px] text-brand-muted truncate">
            Avg Loss: ${Number(metrics.average_loss).toFixed(0)}
          </div>
        </div>
      </div>
    </div>
  );
};
