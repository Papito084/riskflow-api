import React, { createContext, useContext, useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { accountsApi } from '../services/api';
import { TradingAccount } from '../types';
import { useAuth } from './AuthContext';

interface AccountContextType {
  accounts: TradingAccount[];
  selectedAccount: TradingAccount | null;
  selectedAccountId: string | null;
  setSelectedAccountId: (id: string) => void;
  isLoading: boolean;
  refetchAccounts: () => void;
}

const AccountContext = createContext<AccountContextType | undefined>(undefined);

export const AccountProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const [selectedAccountId, setSelectedAccountId] = useState<string | null>(() =>
    localStorage.getItem('riskflow_selected_account_id')
  );

  const {
    data: accounts = [],
    isLoading,
    refetch: refetchAccounts,
  } = useQuery({
    queryKey: ['accounts'],
    queryFn: accountsApi.list,
    enabled: isAuthenticated,
  });

  useEffect(() => {
    if (accounts.length > 0) {
      if (!selectedAccountId || !accounts.some((a) => a.id === selectedAccountId)) {
        const firstId = accounts[0].id;
        setSelectedAccountId(firstId);
        localStorage.setItem('riskflow_selected_account_id', firstId);
      }
    } else {
      setSelectedAccountId(null);
    }
  }, [accounts, selectedAccountId]);

  const handleSelectAccount = (id: string) => {
    setSelectedAccountId(id);
    localStorage.setItem('riskflow_selected_account_id', id);
  };

  const selectedAccount =
    accounts.find((acc) => acc.id === selectedAccountId) || accounts[0] || null;

  return (
    <AccountContext.Provider
      value={{
        accounts,
        selectedAccount,
        selectedAccountId,
        setSelectedAccountId: handleSelectAccount,
        isLoading,
        refetchAccounts,
      }}
    >
      {children}
    </AccountContext.Provider>
  );
};

export const useAccount = (): AccountContextType => {
  const context = useContext(AccountContext);
  if (!context) {
    throw new Error('useAccount must be used within an AccountProvider');
  }
  return context;
};
