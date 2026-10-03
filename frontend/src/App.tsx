import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Bell, X } from 'lucide-react';
import { CloseTradeModal } from './components/CloseTradeModal';
import { EditAccountModal } from './components/EditAccountModal';
import { EquityChart } from './components/EquityChart';
import { KpiGrid } from './components/KpiGrid';
import { LoginView } from './components/LoginView';
import { Navbar } from './components/Navbar';
import { NewAccountModal } from './components/NewAccountModal';
import { NewTradeModal } from './components/NewTradeModal';
import { TradeTable } from './components/TradeTable';
import { AccountProvider, useAccount } from './context/AccountContext';
import { AuthProvider, useAuth } from './context/AuthContext';
import { useRiskFlowWebSocket } from './hooks/useRiskFlowWebSocket';
import { analyticsApi, tradesApi } from './services/api';
import { Trade } from './types';

const DashboardContent: React.FC = () => {
  const { token } = useAuth();
  const { selectedAccount, selectedAccountId } = useAccount();

  // WebSocket Live Hook
  const { isConnected, notification, dismissNotification } = useRiskFlowWebSocket(
    selectedAccountId,
    token
  );

  // Modal States
  const [isNewTradeOpen, setIsNewTradeOpen] = useState<boolean>(false);
  const [tradeToClose, setTradeToClose] = useState<Trade | null>(null);
  const [isNewAccountOpen, setIsNewAccountOpen] = useState<boolean>(false);
  const [isEditAccountOpen, setIsEditAccountOpen] = useState<boolean>(false);

  // Analytics Query
  const { data: metrics = null, isLoading: isMetricsLoading } = useQuery({
    queryKey: ['analytics', selectedAccountId],
    queryFn: () => analyticsApi.get(selectedAccountId!),
    enabled: !!selectedAccountId,
    staleTime: 30000,
  });

  // Trades Query
  const { data: trades = [], isLoading: isTradesLoading } = useQuery({
    queryKey: ['trades', selectedAccountId],
    queryFn: () => tradesApi.list(selectedAccountId!, { limit: 100 }),
    enabled: !!selectedAccountId,
  });

  return (
    <div className="min-h-screen bg-brand-dark flex flex-col text-slate-100 pb-16">
      <Navbar
        isWsConnected={isConnected}
        onOpenNewTrade={() => setIsNewTradeOpen(true)}
        onOpenNewAccount={() => setIsNewAccountOpen(true)}
        onOpenEditAccount={() => setIsEditAccountOpen(true)}
      />

      {/* Floating Real-time Notification Banner */}
      {notification && (
        <div className="fixed bottom-6 right-6 z-50 animate-bounce">
          <div className="glass-panel px-4 py-3 rounded-xl border border-emerald-500/40 shadow-2xl flex items-center space-x-3 bg-brand-card/95 text-xs text-slate-200">
            <Bell className="h-4 w-4 text-emerald-400 shrink-0" />
            <span className="font-mono font-medium">{notification}</span>
            <button
              onClick={dismissNotification}
              className="text-slate-400 hover:text-slate-200 ml-2"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      )}

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-6">
        {/* KPI Grid */}
        <KpiGrid metrics={metrics} isLoading={isMetricsLoading} />

        {/* Equity Curve Chart */}
        <EquityChart
          account={selectedAccount}
          trades={trades}
          isLoading={isTradesLoading}
        />

        {/* Journal Trade Table */}
        <TradeTable
          trades={trades}
          isLoading={isTradesLoading}
          onCloseTradeClick={(t) => setTradeToClose(t)}
        />
      </main>

      {/* Modals */}
      <NewAccountModal
        isOpen={isNewAccountOpen}
        onClose={() => setIsNewAccountOpen(false)}
      />

      <EditAccountModal
        account={selectedAccount}
        isOpen={isEditAccountOpen}
        onClose={() => setIsEditAccountOpen(false)}
      />

      <NewTradeModal
        isOpen={isNewTradeOpen}
        onClose={() => setIsNewTradeOpen(false)}
      />

      <CloseTradeModal
        trade={tradeToClose}
        isOpen={!!tradeToClose}
        onClose={() => setTradeToClose(null)}
      />
    </div>
  );
};

export const App: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-brand-dark flex items-center justify-center">
        <div className="text-center space-y-3">
          <div className="h-8 w-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-xs font-mono text-brand-muted">Connecting to RiskFlow Engine...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginView />;
  }

  return (
    <AccountProvider>
      <DashboardContent />
    </AccountProvider>
  );
};

const Root: React.FC = () => (
  <AuthProvider>
    <App />
  </AuthProvider>
);

export default Root;
