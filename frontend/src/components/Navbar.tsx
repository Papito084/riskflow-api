import React, { useEffect, useRef, useState } from 'react';
import {
  Activity,
  ChevronDown,
  LogOut,
  Plus,
  Settings,
  ShieldCheck,
  Wallet,
} from 'lucide-react';
import { useAccount } from '../context/AccountContext';
import { useAuth } from '../context/AuthContext';

interface NavbarProps {
  isWsConnected: boolean;
  onOpenNewTrade: () => void;
  onOpenNewAccount: () => void;
  onOpenEditAccount: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  isWsConnected,
  onOpenNewTrade,
  onOpenNewAccount,
  onOpenEditAccount,
}) => {
  const { user, logout } = useAuth();
  const { accounts, selectedAccount, setSelectedAccountId } = useAccount();
  const [isDropdownOpen, setIsDropdownOpen] = useState<boolean>(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="sticky top-0 z-30 border-b border-brand-border bg-brand-dark/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand / Logo */}
        <div className="flex items-center space-x-3">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 p-[1px] shadow-lg shadow-emerald-500/20">
            <div className="h-full w-full bg-brand-card rounded-[11px] flex items-center justify-center">
              <Activity className="h-5 w-5 text-emerald-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                RiskFlow
              </span>
              <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 uppercase tracking-wider">
                Pro
              </span>
            </div>
            <p className="text-[11px] text-brand-muted hidden sm:block">
              Real-Time Risk Analytics & Journal
            </p>
          </div>
        </div>

        {/* Center / Account Selector */}
        <div className="flex items-center space-x-2">
          {accounts.length > 0 && selectedAccount ? (
            <div className="relative" ref={dropdownRef}>
              <div className="flex items-center space-x-1.5">
                {/* Account Trigger Button */}
                <button
                  type="button"
                  onClick={() => setIsDropdownOpen((prev) => !prev)}
                  className="flex items-center space-x-2.5 px-3.5 py-1.5 rounded-xl bg-brand-surface border border-brand-border hover:border-slate-500 transition-all text-left focus:outline-none"
                >
                  <Wallet className="h-4 w-4 text-emerald-400 shrink-0" />
                  <div>
                    <div className="text-xs font-semibold text-slate-200 flex items-center space-x-1.5">
                      <span className="max-w-[130px] sm:max-w-[180px] truncate">
                        {selectedAccount.name}
                      </span>
                      <span className="text-[10px] px-1 py-0.2 rounded bg-slate-800 text-slate-400 font-mono">
                        {selectedAccount.broker_type}
                      </span>
                    </div>
                    <div className="text-[11px] font-mono text-emerald-400">
                      ${Number(selectedAccount.current_balance).toLocaleString('en-US', {
                        minimumFractionDigits: 2,
                      })}{' '}
                      {selectedAccount.currency}
                    </div>
                  </div>
                  <ChevronDown
                    className={`h-3.5 w-3.5 text-slate-400 ml-1 transition-transform duration-200 ${
                      isDropdownOpen ? 'rotate-180 text-emerald-400' : ''
                    }`}
                  />
                </button>

                {/* Edit Account Settings Quick Button */}
                <button
                  type="button"
                  onClick={onOpenEditAccount}
                  title="Edit Account Settings"
                  className="p-2 rounded-xl bg-brand-surface border border-brand-border text-slate-400 hover:text-slate-100 hover:border-slate-500 hover:bg-slate-800/80 transition-all"
                >
                  <Settings className="h-4 w-4" />
                </button>
              </div>

              {/* Account Dropdown Menu */}
              {isDropdownOpen && (
                <div className="absolute left-0 mt-2 w-72 rounded-2xl bg-brand-card border border-brand-border shadow-2xl overflow-hidden z-50 animate-fade-in">
                  <div className="px-3.5 py-2 text-[10px] font-semibold uppercase tracking-wider text-brand-muted border-b border-brand-border/60 flex items-center justify-between">
                    <span>Switch Portfolio Account</span>
                    <span className="text-slate-500 font-mono">{accounts.length} active</span>
                  </div>

                  <div className="max-h-60 overflow-y-auto py-1 divide-y divide-brand-border/30">
                    {accounts.map((acc) => {
                      const isSelected = acc.id === selectedAccount.id;
                      return (
                        <div
                          key={acc.id}
                          className={`w-full px-3.5 py-2.5 hover:bg-brand-surface transition-colors flex items-center justify-between group ${
                            isSelected ? 'bg-emerald-500/10 border-l-2 border-emerald-500' : ''
                          }`}
                        >
                          <button
                            type="button"
                            onClick={() => {
                              setSelectedAccountId(acc.id);
                              setIsDropdownOpen(false);
                            }}
                            className="flex-1 text-left"
                          >
                            <div className="flex items-center space-x-1.5">
                              <span
                                className={`text-xs font-medium ${
                                  isSelected ? 'text-emerald-400' : 'text-slate-200'
                                }`}
                              >
                                {acc.name}
                              </span>
                              <span className="text-[9px] px-1 rounded bg-slate-800 text-slate-400 font-mono">
                                {acc.broker_type}
                              </span>
                            </div>
                            <div className="text-[11px] font-mono text-slate-400 mt-0.5">
                              ${Number(acc.current_balance).toLocaleString('en-US', {
                                minimumFractionDigits: 2,
                              })}{' '}
                              {acc.currency}
                            </div>
                          </button>

                          <div className="flex items-center space-x-1 pl-2">
                            {isSelected ? (
                              <button
                                type="button"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setIsDropdownOpen(false);
                                  onOpenEditAccount();
                                }}
                                title="Edit Active Account Settings"
                                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                              >
                                <Settings className="h-3.5 w-3.5" />
                              </button>
                            ) : null}
                            {isSelected && <ShieldCheck className="h-4 w-4 text-emerald-400" />}
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Add New Account Action */}
                  <div className="p-1.5 border-t border-brand-border/60 bg-brand-surface/40">
                    <button
                      type="button"
                      onClick={() => {
                        setIsDropdownOpen(false);
                        onOpenNewAccount();
                      }}
                      className="w-full px-3 py-2 rounded-xl text-left text-xs font-semibold text-emerald-400 hover:bg-emerald-500/10 hover:text-emerald-300 transition-colors flex items-center space-x-2"
                    >
                      <Plus className="h-4 w-4" />
                      <span>+ Add New Account</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            /* Button when no accounts are found */
            <button
              type="button"
              onClick={onOpenNewAccount}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20 text-xs font-semibold transition-all"
            >
              <Plus className="h-4 w-4" />
              <span>+ Create Trading Account</span>
            </button>
          )}
        </div>

        {/* Right Section: Live Status, New Trade Button, Logout */}
        <div className="flex items-center space-x-3">
          {/* WebSocket Pulse Badge */}
          <div
            className={`hidden md:flex items-center space-x-2 px-2.5 py-1 rounded-full text-xs font-mono border ${
              isWsConnected
                ? 'bg-emerald-950/40 border-emerald-500/30 text-emerald-400'
                : 'bg-zinc-900 border-zinc-700 text-zinc-400'
            }`}
          >
            <span className="relative flex h-2 w-2">
              {isWsConnected && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              )}
              <span
                className={`relative inline-flex rounded-full h-2 w-2 ${
                  isWsConnected ? 'bg-emerald-500' : 'bg-zinc-500'
                }`}
              ></span>
            </span>
            <span>{isWsConnected ? 'LIVE FEED' : 'CONNECTING...'}</span>
          </div>

          {/* New Trade Trigger Button */}
          <button
            onClick={onOpenNewTrade}
            disabled={!selectedAccount}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 disabled:opacity-40 disabled:cursor-not-allowed text-brand-dark font-semibold text-xs transition-all shadow-md shadow-emerald-500/20 hover:shadow-emerald-500/30 active:scale-95"
          >
            <Plus className="h-4 w-4 stroke-[2.5]" />
            <span>New Trade</span>
          </button>

          {/* User Profile & Logout */}
          <div className="flex items-center space-x-2 border-l border-brand-border pl-3">
            <span className="text-xs text-brand-muted hidden lg:inline max-w-[140px] truncate">
              {user?.email}
            </span>
            <button
              onClick={logout}
              title="Sign Out"
              className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
