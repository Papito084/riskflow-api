import React, { useMemo } from 'react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { TrendingUp } from 'lucide-react';
import { Trade, TradingAccount } from '../types';

interface EquityChartProps {
  account: TradingAccount | null;
  trades: Trade[];
  isLoading: boolean;
}

interface DataPoint {
  index: number;
  date: string;
  equity: number;
  pnl: number;
  symbol: string;
}

export const EquityChart: React.FC<EquityChartProps> = ({ account, trades, isLoading }) => {
  const chartData = useMemo<DataPoint[]>(() => {
    if (!account) return [];

    const initial = Number(account.initial_balance);
    const closed = trades
      .filter((t) => t.status === 'CLOSED' && t.pnl !== null)
      .sort((a, b) => new Date(a.opened_at).getTime() - new Date(b.opened_at).getTime());

    const points: DataPoint[] = [
      {
        index: 0,
        date: 'Start',
        equity: initial,
        pnl: 0,
        symbol: 'Account Deposit',
      },
    ];

    let current = initial;
    closed.forEach((t, i) => {
      const pnl = Number(t.pnl);
      current += pnl;
      points.push({
        index: i + 1,
        date: new Date(t.closed_at || t.opened_at).toLocaleDateString(undefined, {
          month: 'short',
          day: 'numeric',
        }),
        equity: Math.round(current * 100) / 100,
        pnl,
        symbol: `${t.direction} ${t.symbol}`,
      });
    });

    return points;
  }, [account, trades]);

  if (isLoading || !account) {
    return (
      <div className="glass-panel p-5 rounded-xl border border-brand-border h-80 flex items-center justify-center animate-pulse">
        <div className="text-brand-muted text-sm font-mono">Computing equity trajectory...</div>
      </div>
    );
  }

  const initialBalance = Number(account.initial_balance);
  const currentBalance = Number(account.current_balance);
  const isNetProfit = currentBalance >= initialBalance;
  const strokeColor = isNetProfit ? '#10b981' : '#f43f5e';

  return (
    <div className="glass-panel p-5 rounded-xl border border-brand-border/80 mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-brand-border/50 gap-2">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <TrendingUp className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold tracking-tight text-slate-100">
              Equity Curve & Portfolio Trajectory
            </h3>
            <p className="text-[11px] text-brand-muted">
              Cumulative balance evolution over {chartData.length - 1} executed trades
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-4 text-xs font-mono">
          <div>
            <span className="text-brand-muted">Initial: </span>
            <span className="text-slate-300">${initialBalance.toLocaleString()}</span>
          </div>
          <div>
            <span className="text-brand-muted">Current: </span>
            <span className={`font-semibold ${isNetProfit ? 'text-emerald-400' : 'text-rose-400'}`}>
              ${currentBalance.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </span>
          </div>
        </div>
      </div>

      <div className="h-72 w-full pt-4">
        {chartData.length <= 1 ? (
          <div className="h-full flex flex-col items-center justify-center text-brand-muted text-xs">
            <p>No closed trades recorded yet for this account.</p>
            <p className="text-[11px] mt-1 text-slate-500">
              Open and close trades to visualize the mathematical equity curve.
            </p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
              <defs>
                <linearGradient id="equityGlow" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={strokeColor} stopOpacity={0.35} />
                  <stop offset="95%" stopColor={strokeColor} stopOpacity={0.0} />
                </linearGradient>
              </defs>

              <CartesianGrid strokeDasharray="3 3" stroke="#1c202c" vertical={false} />

              <XAxis
                dataKey="date"
                stroke="#64748b"
                fontSize={11}
                tickLine={false}
                axisLine={{ stroke: '#232736' }}
              />

              <YAxis
                stroke="#64748b"
                fontSize={11}
                tickLine={false}
                axisLine={{ stroke: '#232736' }}
                domain={['auto', 'auto']}
                tickFormatter={(val) => `$${Number(val).toLocaleString()}`}
              />

              <ReferenceLine
                y={initialBalance}
                stroke="#475569"
                strokeDasharray="4 4"
                label={{
                  value: 'Baseline',
                  fill: '#94a3b8',
                  fontSize: 10,
                  position: 'insideBottomRight',
                }}
              />

              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload as DataPoint;
                    const pnlPositive = data.pnl >= 0;
                    return (
                      <div className="bg-brand-card/95 border border-brand-border p-3 rounded-lg shadow-xl text-xs backdrop-blur-md">
                        <div className="text-[11px] text-brand-muted font-medium mb-1">
                          {data.symbol} ({data.date})
                        </div>
                        <div className="font-mono text-sm font-bold text-slate-100">
                          Balance: ${data.equity.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                        </div>
                        {data.index > 0 && (
                          <div
                            className={`font-mono text-[11px] font-semibold mt-0.5 ${
                              pnlPositive ? 'text-emerald-400' : 'text-rose-400'
                            }`}
                          >
                            Trade PnL: {pnlPositive ? '+' : ''}${data.pnl.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                          </div>
                        )}
                      </div>
                    );
                  }
                  return null;
                }}
              />

              <Area
                type="monotone"
                dataKey="equity"
                stroke={strokeColor}
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#equityGlow)"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
};
