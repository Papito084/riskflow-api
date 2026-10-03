import axios from 'axios';
import {
  RiskMetricsResponse,
  TokenResponse,
  Trade,
  TradeClosePayload,
  TradeCreatePayload,
  TradingAccount,
  TradingAccountCreatePayload,
  TradingAccountUpdatePayload,
  User,
} from '../types';

const getApiBaseUrl = (): string => {
  const envUrl = import.meta.env.VITE_API_URL;
  if (envUrl && envUrl.trim() !== '') {
    return envUrl.replace(/\/+$/, '');
  }
  // Fallback to relative URL, perfectly routed by Nginx or Vite dev proxy
  return '';
};

export const API_BASE_URL = getApiBaseUrl();

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: Inject JWT Bearer Token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('riskflow_access_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response Interceptor: Handle 401 Unauthorized Session Expiration
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const requestUrl = error.config?.url || '';
    // Do NOT dispatch expired event when the user is simply attempting to log in
    if (error.response?.status === 401 && !requestUrl.includes('/auth/login')) {
      localStorage.removeItem('riskflow_access_token');
      localStorage.removeItem('riskflow_refresh_token');
      window.dispatchEvent(new Event('riskflow_auth_expired'));
    }
    return Promise.reject(error);
  }
);

// Auth Service
export const authApi = {
  login: async (email: string, password: string): Promise<TokenResponse> => {
    const res = await apiClient.post<TokenResponse>('/auth/login', { email, password });
    return res.data;
  },
  getMe: async (): Promise<User> => {
    const res = await apiClient.get<User>('/auth/me');
    return res.data;
  },
};

// Trading Accounts Service
export const accountsApi = {
  list: async (): Promise<TradingAccount[]> => {
    const res = await apiClient.get<TradingAccount[]>('/accounts/');
    return res.data;
  },
  get: async (accountId: string): Promise<TradingAccount> => {
    const res = await apiClient.get<TradingAccount>(`/accounts/${accountId}`);
    return res.data;
  },
  create: async (payload: TradingAccountCreatePayload): Promise<TradingAccount> => {
    const res = await apiClient.post<TradingAccount>('/accounts/', payload);
    return res.data;
  },
  update: async (
    accountId: string,
    payload: TradingAccountUpdatePayload
  ): Promise<TradingAccount> => {
    const res = await apiClient.patch<TradingAccount>(`/accounts/${accountId}`, payload);
    return res.data;
  },
};

// Trades Service
export const tradesApi = {
  list: async (
    accountId: string,
    params?: { status?: string; symbol?: string; limit?: number }
  ): Promise<Trade[]> => {
    const res = await apiClient.get<Trade[]>(`/trades/account/${accountId}`, { params });
    return res.data;
  },
  create: async (payload: TradeCreatePayload): Promise<Trade> => {
    const res = await apiClient.post<Trade>('/trades/', payload);
    return res.data;
  },
  close: async (tradeId: string, payload: TradeClosePayload): Promise<Trade> => {
    const res = await apiClient.post<Trade>(`/trades/${tradeId}/close`, payload);
    return res.data;
  },
};

// Analytics Service
export const analyticsApi = {
  get: async (accountId: string): Promise<RiskMetricsResponse> => {
    const res = await apiClient.get<RiskMetricsResponse>(`/analytics/accounts/${accountId}`);
    return res.data;
  },
};
