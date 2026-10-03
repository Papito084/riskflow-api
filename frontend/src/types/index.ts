export type BrokerType = 'PropFirm' | 'Personal';
export type Currency = 'USD' | 'EUR';
export type TradeDirection = 'BUY' | 'SELL';
export type TradeStatus = 'OPEN' | 'CLOSED';

export interface User {
  id: string;
  email: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface TradingAccount {
  id: string;
  user_id: string;
  name: string;
  broker_type: BrokerType;
  initial_balance: string;
  current_balance: string;
  currency: Currency;
  created_at: string;
}

export interface TradingAccountCreatePayload {
  name: string;
  broker_type: BrokerType;
  initial_balance: string;
  currency: Currency;
}

export interface TradingAccountUpdatePayload {
  name?: string;
  broker_type?: BrokerType;
}

export interface Trade {
  id: string;
  account_id: string;
  symbol: string;
  direction: TradeDirection;
  entry_price: string;
  exit_price: string | null;
  lot_size: string;
  pnl: string | null;
  opened_at: string;
  closed_at: string | null;
  status: TradeStatus;
}

export interface TradeCreatePayload {
  account_id: string;
  symbol: string;
  direction: TradeDirection;
  entry_price: string;
  lot_size: string;
  exit_price?: string | null;
  pnl?: string | null;
  status: TradeStatus;
}

export interface TradeClosePayload {
  exit_price: string;
  pnl?: string | null;
}

export interface RiskMetricsResponse {
  account_id: string;
  total_trades: number;
  closed_trades: number;
  open_trades: number;
  winning_trades: number;
  losing_trades: number;
  break_even_trades: number;

  win_rate_pct: string;
  loss_rate_pct: string;

  gross_profit: string;
  gross_loss: string;
  net_profit: string;

  profit_factor: string | null;
  max_drawdown_amount: string;
  max_drawdown_pct: string;
  average_win: string;
  average_loss: string;
  risk_reward_ratio: string | null;
  expectancy: string;

  cached: boolean;
  calculated_at: string;
}

export interface WebSocketEvent {
  event_type: 'CONNECTED' | 'TRADE_CREATED' | 'TRADE_CLOSED';
  account_id: string;
  trade?: Trade;
  message?: string;
  timestamp?: string;
}
