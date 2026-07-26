import { useRef, useCallback, useEffect } from 'react';
import { getWebSocketBase } from './wsUtils';

// ==================== Types ====================

export interface ThreatAttackVector {
  type: 'attack_vector';
  id: string;
  from: string;
  fromLat: number;
  fromLng: number;
  to: string;
  toLat: number;
  toLng: number;
  attackType: string;
  severity: 'critical' | 'medium' | 'safe';
  sourceIp?: string;
  isp?: string;
  org?: string;
  source?: string;      // Which threat feed: ThreatFox, Feodo, IPsum
  malware?: string;     // Real malware family name from feed
  timestamp: string;
  modeledTarget?: boolean;  // true = target city is statistically modeled
  note?: string | null;     // Disclosure about estimated/simulated fields
}

export interface ThreatTickerEvent {
  type: 'threat_event' | 'news_event';
  id: string;
  severity: 'critical' | 'medium' | 'safe';
  text: string;
  icon: string;
  source?: string;
  city?: string;
  attackType?: string;
  url?: string;
  timestamp: string;
}

export interface ThreatInitialState {
  type: 'initial_state';
  events: (ThreatAttackVector | ThreatTickerEvent)[];
  cities: Array<{
    name: string;
    lat: number;
    lng: number;
    risk: string;
    assetCount: number;
    activeThreats: number;
    note?: string;  // Disclosure about estimated data
  }>;
  timestamp: string;
}

export type ThreatFeedMessage =
  | ThreatInitialState
  | ThreatAttackVector
  | ThreatTickerEvent;

interface UseThreatFeedOptions {
  onAttackVector?: (vector: ThreatAttackVector) => void;
  onThreatEvent?: (event: ThreatTickerEvent) => void;
  onInitialState?: (state: ThreatInitialState) => void;
  onError?: (error: Event) => void;
}

/**
 * Custom hook that manages a WebSocket connection to the live threat feed.
 *
 * Streams real-time attack vectors, threat events, and news headlines
 * for the interactive map and ticker.
 */
export function useThreatFeed(options: UseThreatFeedOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const optionsRef = useRef(options);
  const disconnectedRef = useRef(false);
  const retryCountRef = useRef(0);
  optionsRef.current = options;

  const cleanup = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  // Cleanup on unmount — use disconnect() to prevent reconnect loop
  useEffect(() => {
    return () => {
      disconnectedRef.current = true;
      cleanup();
    };
  }, [cleanup]);

  const connect = useCallback(() => {
    cleanup();
    // Reset disconnected flag so new external connect() calls work
    // even after an explicit disconnect() or React Strict Mode unmount.
    // Reconnect prevention is handled by onclose checking disconnectedRef.
    disconnectedRef.current = false;

    // Include auth token in query string for WebSocket auth
    let wsUrl = `${getWebSocketBase()}/ws/threats`;
    try {
      const token = localStorage.getItem('trinetra_api_key');
      if (token) {
        wsUrl += `?api_key=${encodeURIComponent(token)}`;
      }
    } catch {
      // localStorage unavailable
    }

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      // Connected to live threat stream — reset retry count
      retryCountRef.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const msg: ThreatFeedMessage = JSON.parse(event.data);

        switch (msg.type) {
          case 'initial_state':
            optionsRef.current.onInitialState?.(msg);
            break;
          case 'attack_vector':
            optionsRef.current.onAttackVector?.(msg);
            break;
          case 'threat_event':
          case 'news_event':
            optionsRef.current.onThreatEvent?.(msg);
            break;
        }
      } catch (err) {
        console.error('[ThreatFeed] Failed to parse message:', err);
      }
    };

    ws.onerror = (_event) => {
      // Suppress noisy console.error for transient connection failures.
      // Reconnect is handled in onclose with exponential backoff.
      // Still fire the callback so ThreatContext can update isConnected.
      optionsRef.current.onError?.(_event);
    };

    ws.onclose = () => {
      // Ignore stale onclose events from previous WebSocket instances
      if (wsRef.current !== ws) return;
      wsRef.current = null;
      // Only auto-reconnect if we haven't been explicitly disconnected
      if (!disconnectedRef.current) {
        // Exponential backoff: 500ms, 1s, 2s, 4s, 8s, then cap at 8s
        const delay = Math.min(500 * Math.pow(2, retryCountRef.current), 8000);
        retryCountRef.current += 1;
        reconnectTimerRef.current = setTimeout(() => {
          connect();
        }, delay);
      }
    };
  }, [cleanup]);

  const disconnect = useCallback(() => {
    // Mark as intentionally disconnected first so onclose won't reconnect
    disconnectedRef.current = true;
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  return { connect, disconnect };
}
