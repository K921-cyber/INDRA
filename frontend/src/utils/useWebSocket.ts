import { useRef, useCallback, useEffect } from 'react';
import { getWebSocketBase } from './wsUtils';

export interface WebSocketStartMessage {
  type: 'start';
  total: number;
  plugins: Array<{ plugin_id: string; plugin_name: string; category: string }>;
}

export interface WebSocketResultMessage {
  type: 'result';
  result: {
    plugin_id: string;
    plugin_name: string;
    category: string;
    target: string;
    status: string;
    freshness: string;
    timestamp: string;
    gui_data: Record<string, any>;
    terminal_data: string;
    error?: string;
  };
  completed: number;
  total: number;
  plugin_id: string;
}

export interface WebSocketCompleteMessage {
  type: 'complete';
  total: number;
  completed: number;
}

export interface WebSocketErrorMessage {
  type: 'error';
  message: string;
}

export type WebSocketMessage =
  | WebSocketStartMessage
  | WebSocketResultMessage
  | WebSocketCompleteMessage
  | WebSocketErrorMessage;interface UseWebSocketOptions {
  onStart?: (msg: WebSocketStartMessage) => void;
  onResult?: (msg: WebSocketResultMessage) => void;
  onComplete?: (msg: WebSocketCompleteMessage) => void;
  onError?: (msg: WebSocketErrorMessage) => void;
}

/**
 * Custom hook that manages a WebSocket connection for streaming scan results.
 *
 * Usage:
 *   const { connect, disconnect, isConnected } = useWebSocket({
 *     onResult: (msg) => dispatch({ type: 'ADD_RESULT', payload: msg.result }),
 *   });
 *   connect({ target: 'example.com' });
 */
export function useWebSocket(options: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const optionsRef = useRef(options);
  optionsRef.current = options;

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []);

  const connect = useCallback((payload: { target: string; type?: string }) => {
    // Close any existing connection
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    // Include API key in query string for WebSocket auth
    let wsUrl = `${getWebSocketBase()}/ws/search`;
    try {
      const apiKey = localStorage.getItem('trinetra_api_key');
      if (apiKey) {
        wsUrl += `?api_key=${encodeURIComponent(apiKey)}`;
      }
    } catch {
      // localStorage unavailable
    }

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      // Send the search request once connected
      ws.send(JSON.stringify(payload));
    };

    ws.onmessage = (event) => {
      try {
        const msg: WebSocketMessage = JSON.parse(event.data);

        switch (msg.type) {
          case 'start':
            optionsRef.current.onStart?.(msg);
            break;
          case 'result':
            optionsRef.current.onResult?.(msg);
            break;
          case 'complete':
            optionsRef.current.onComplete?.(msg);
            break;
          case 'error':
            optionsRef.current.onError?.(msg);
            break;
        }
      } catch (err) {
        console.error('WebSocket: failed to parse message', err);
      }
    };

    ws.onerror = (event) => {
      console.error('WebSocket error:', event);
    };

    ws.onclose = () => {
      if (wsRef.current === ws) {
        wsRef.current = null;
      }
    };
  }, []);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  return { connect, disconnect };
}
