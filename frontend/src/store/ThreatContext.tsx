import React, { createContext, useContext, useReducer, ReactNode, useCallback, useEffect, useRef } from 'react';
import {
  useThreatFeed,
  ThreatAttackVector,
  ThreatTickerEvent,
  ThreatInitialState,
} from '../utils/useThreatFeed';

// ==================== Types ====================

export interface LiveCityData {
  name: string;
  lat: number;
  lng: number;
  risk: string;
  assetCount: number;
  activeThreats: number;
}

export interface ThreatState {
  attackVectors: ThreatAttackVector[];
  tickerEvents: ThreatTickerEvent[];
  cities: LiveCityData[];
  isConnected: boolean;
  totalIncidents: number;
  criticalThreats: number;
}

// ==================== Initial State ====================

const initialState: ThreatState = {
  attackVectors: [],
  tickerEvents: [],
  cities: [],
  isConnected: false,
  totalIncidents: 0,
  criticalThreats: 0,
};

// ==================== Actions ====================

type ThreatAction =
  | { type: 'SET_CONNECTED'; payload: boolean }
  | { type: 'SET_INITIAL_STATE'; payload: ThreatInitialState }
  | { type: 'ADD_ATTACK_VECTOR'; payload: ThreatAttackVector }
  | { type: 'ADD_TICKER_EVENT'; payload: ThreatTickerEvent };

function threatReducer(state: ThreatState, action: ThreatAction): ThreatState {
  switch (action.type) {
    case 'SET_CONNECTED':
      return { ...state, isConnected: action.payload };

    case 'SET_INITIAL_STATE': {
      const events = action.payload.events;
      const attackVectors = events.filter(
        (e): e is ThreatAttackVector => e.type === 'attack_vector'
      );
      const tickerEvents = events.filter(
        (e): e is ThreatTickerEvent => e.type === 'threat_event' || e.type === 'news_event'
      );
      return {
        ...state,
        attackVectors,
        tickerEvents,
        cities: action.payload.cities.map(c => ({
          ...c,
          risk: c.risk as string,
        })),
        totalIncidents: attackVectors.length + tickerEvents.length,
        criticalThreats: attackVectors.filter(v => v.severity === 'critical').length,
      };
    }

    case 'ADD_ATTACK_VECTOR': {
      const newVectors = [...state.attackVectors, action.payload];
      // Keep last 50 attack vectors
      if (newVectors.length > 50) newVectors.shift();
      return {
        ...state,
        attackVectors: newVectors,
        totalIncidents: state.totalIncidents + 1,
        criticalThreats: newVectors.filter(v => v.severity === 'critical').length,
      };
    }

    case 'ADD_TICKER_EVENT': {
      const newEvents = [...state.tickerEvents, action.payload];
      // Keep last 100 ticker events
      if (newEvents.length > 100) newEvents.shift();
      return {
        ...state,
        tickerEvents: newEvents,
        totalIncidents: state.totalIncidents + 1,
      };
    }

    default:
      return state;
  }
}

// ==================== Context ====================

interface ThreatContextType {
  state: ThreatState;
  connect: () => void;
  disconnect: () => void;
}

const ThreatContext = createContext<ThreatContextType | undefined>(undefined);

export function ThreatProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(threatReducer, initialState);
  const connectedRef = useRef(false);

  const handleAttackVector = useCallback((vector: ThreatAttackVector) => {
    dispatch({ type: 'ADD_ATTACK_VECTOR', payload: vector });
  }, []);

  const handleThreatEvent = useCallback((event: ThreatTickerEvent) => {
    dispatch({ type: 'ADD_TICKER_EVENT', payload: event });
  }, []);

  const handleInitialState = useCallback((initial: ThreatInitialState) => {
    dispatch({ type: 'SET_INITIAL_STATE', payload: initial });
    dispatch({ type: 'SET_CONNECTED', payload: true });
  }, []);

  const handleError = useCallback(() => {
    dispatch({ type: 'SET_CONNECTED', payload: false });
  }, []);

  const { connect: wsConnect, disconnect: wsDisconnect } = useThreatFeed({
    onAttackVector: handleAttackVector,
    onThreatEvent: handleThreatEvent,
    onInitialState: handleInitialState,
    onError: handleError,
  });

  const connect = useCallback(() => {
    if (!connectedRef.current) {
      connectedRef.current = true;
      wsConnect();
    }
  }, [wsConnect]);

  const disconnect = useCallback(() => {
    connectedRef.current = false;
    wsDisconnect();
  }, [wsDisconnect]);

  // Auto-connect on mount
  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return (
    <ThreatContext.Provider value={{ state, connect, disconnect }}>
      {children}
    </ThreatContext.Provider>
  );
}

export function useThreatContext() {
  const context = useContext(ThreatContext);
  if (!context) throw new Error('useThreatContext must be used within ThreatProvider');
  return context;
}
