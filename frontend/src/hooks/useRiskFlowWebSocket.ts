import { useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { WebSocketEvent } from '../types';

interface UseRiskFlowWebSocketReturn {
  isConnected: boolean;
  lastEvent: WebSocketEvent | null;
  notification: string | null;
  dismissNotification: () => void;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const useRiskFlowWebSocket = (
  accountId: string | null,
  token: string | null
): UseRiskFlowWebSocketReturn => {
  const queryClient = useQueryClient();
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [lastEvent, setLastEvent] = useState<WebSocketEvent | null>(null);
  const [notification, setNotification] = useState<string | null>(null);

  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const dismissNotification = () => setNotification(null);

  useEffect(() => {
    if (!accountId || !token) {
      if (socketRef.current) {
        socketRef.current.close();
      }
      setIsConnected(false);
      return;
    }

    const wsProtocol = API_BASE_URL.startsWith('https') ? 'wss:' : 'ws:';
    const host = API_BASE_URL.replace(/^https?:\/\//, '');
    const wsUrl = `${wsProtocol}//${host}/api/v1/ws/accounts/${accountId}?token=${encodeURIComponent(token)}`;

    let isComponentMounted = true;

    const connectWebSocket = () => {
      try {
        const ws = new WebSocket(wsUrl);
        socketRef.current = ws;

        ws.onopen = () => {
          if (!isComponentMounted) return;
          setIsConnected(true);

          // Heartbeat ping every 25s
          pingIntervalRef.current = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
              ws.send('ping');
            }
          }, 25000);
        };

        ws.onmessage = (event) => {
          if (!isComponentMounted) return;
          if (event.data === 'pong') return;

          try {
            const data: WebSocketEvent = JSON.parse(event.data);
            setLastEvent(data);

            if (data.event_type === 'TRADE_CREATED') {
              // Smooth invalidate without flashing
              queryClient.invalidateQueries({ queryKey: ['analytics', accountId] });
              queryClient.invalidateQueries({ queryKey: ['trades', accountId] });
              queryClient.invalidateQueries({ queryKey: ['accounts'] });

              const sym = data.trade?.symbol || 'Trade';
              const dir = data.trade?.direction || '';
              setNotification(`⚡ Real-Time: ${dir} ${sym} position ingested!`);
            } else if (data.event_type === 'TRADE_CLOSED') {
              queryClient.invalidateQueries({ queryKey: ['analytics', accountId] });
              queryClient.invalidateQueries({ queryKey: ['trades', accountId] });
              queryClient.invalidateQueries({ queryKey: ['accounts'] });

              const sym = data.trade?.symbol || 'Trade';
              const pnl = data.trade?.pnl ? `$${data.trade.pnl}` : '';
              setNotification(`🎯 Real-Time: ${sym} closed (${pnl})`);
            }
          } catch (err) {
            console.warn('Non-JSON WebSocket message received:', event.data);
          }
        };

        ws.onclose = () => {
          if (!isComponentMounted) return;
          setIsConnected(false);
          if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);

          // Attempt reconnection after 3 seconds
          reconnectTimeoutRef.current = setTimeout(() => {
            if (isComponentMounted) {
              connectWebSocket();
            }
          }, 3000);
        };

        ws.onerror = (err) => {
          console.warn('WebSocket connection error:', err);
          ws.close();
        };
      } catch (err) {
        console.error('Failed to instantiate WebSocket:', err);
      }
    };

    connectWebSocket();

    return () => {
      isComponentMounted = false;
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [accountId, token, queryClient]);

  // Auto-dismiss notification after 5s
  useEffect(() => {
    if (notification) {
      const timer = setTimeout(() => {
        setNotification(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [notification]);

  return {
    isConnected,
    lastEvent,
    notification,
    dismissNotification,
  };
};
