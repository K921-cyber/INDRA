import React, { createContext, useContext, useReducer, ReactNode, useCallback, useRef } from 'react';
import { AppState, SearchType, ToolResult, ViewMode, CityData, AppTab, Toast } from '../types';
import { PluginResultData } from '../utils/api';
import { useWebSocket } from '../utils/useWebSocket';
import { mapPluginResult } from '../utils/pluginMapper';

// ==================== Initial State ====================

const initialState: AppState = {
  searchQuery: '',
  searchType: 'unknown',
  isSearching: false,
  results: [],
  totalPlugins: 0,
  completedPlugins: 0,
  activeToolId: null,
  viewMode: 'gui',
  mapCenter: [20.5937, 78.9629], // Center of India
  mapZoom: 5,
  selectedCity: null,
  showCrimeOverlay: false,
  showGraphView: false,
  activeTab: 'search',
  toasts: [],
};

// ==================== Actions ====================

type Action =
  | { type: 'SET_SEARCH_QUERY'; payload: string }
  | { type: 'SET_SEARCH_TYPE'; payload: SearchType }
  | { type: 'SET_SEARCHING'; payload: boolean }
  | { type: 'SET_RESULTS'; payload: ToolResult[] }
  | { type: 'ADD_RESULT'; payload: ToolResult }
  | { type: 'SET_PROGRESS'; payload: { completed: number; total: number } }
  | { type: 'SET_ACTIVE_TOOL'; payload: string | null }
  | { type: 'SET_VIEW_MODE'; payload: ViewMode }
  | { type: 'SET_MAP_CENTER'; payload: [number, number] }
  | { type: 'SET_MAP_ZOOM'; payload: number }
  | { type: 'SET_SELECTED_CITY'; payload: CityData | null }
  | { type: 'TOGGLE_CRIME_OVERLAY' }
  | { type: 'TOGGLE_GRAPH_VIEW' }
  | { type: 'ADD_TOAST'; payload: Toast }
  | { type: 'REMOVE_TOAST'; payload: number }
  | { type: 'RUN_SEARCH'; payload: string }
  | { type: 'SET_ACTIVE_TAB'; payload: AppTab };

function appReducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case 'SET_SEARCH_QUERY':
      return { ...state, searchQuery: action.payload };
    case 'SET_SEARCH_TYPE':
      return { ...state, searchType: action.payload };
    case 'SET_SEARCHING':
      return { ...state, isSearching: action.payload };
    case 'SET_RESULTS':
      return { ...state, results: action.payload };
    case 'ADD_RESULT':
      return { ...state, results: [...state.results, action.payload] };
    case 'SET_PROGRESS':
      return { ...state, completedPlugins: action.payload.completed, totalPlugins: action.payload.total };
    case 'SET_ACTIVE_TOOL':
      return { ...state, activeToolId: action.payload };
    case 'SET_VIEW_MODE':
      return { ...state, viewMode: action.payload };
    case 'SET_MAP_CENTER':
      return { ...state, mapCenter: action.payload };
    case 'SET_MAP_ZOOM':
      return { ...state, mapZoom: action.payload };
    case 'SET_SELECTED_CITY':
      return { ...state, selectedCity: action.payload };
    case 'TOGGLE_CRIME_OVERLAY':
      return { ...state, showCrimeOverlay: !state.showCrimeOverlay };
    case 'TOGGLE_GRAPH_VIEW':
      return { ...state, showGraphView: !state.showGraphView };
    case 'RUN_SEARCH':
      return {
        ...state,
        activeTab: 'search',
        searchQuery: action.payload,
        isSearching: true,
        results: [],
        totalPlugins: 0,
        completedPlugins: 0,
        activeToolId: null,
        showGraphView: false,
      };
    case 'ADD_TOAST':
      // Keep max 5 toasts, remove oldest if exceeded
      const newToasts = [...state.toasts, action.payload];
      if (newToasts.length > 5) newToasts.shift();
      return { ...state, toasts: newToasts };
    case 'REMOVE_TOAST':
      return { ...state, toasts: state.toasts.filter(t => t.id !== action.payload) };
    case 'SET_ACTIVE_TAB':
      return { ...state, activeTab: action.payload };
    default:
      return state;
  }
}

// ==================== Context ====================

interface AppContextType {
  state: AppState;
  dispatch: React.Dispatch<Action>;
  runSearch: (query: string) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  const toastIdCounterRef = useRef(0);

  const addToast = useCallback((message: string, type: Toast['type'] = 'info', icon: string = 'ℹ️') => {
    const id = ++toastIdCounterRef.current;
    dispatch({ type: 'ADD_TOAST', payload: { id, message, type, icon } });
    // Auto-remove after 3.5 seconds
    setTimeout(() => {
      dispatch({ type: 'REMOVE_TOAST', payload: id });
    }, 3500);
  }, []);

  // WebSocket handlers
  const { connect, disconnect } = useWebSocket({
    onStart: (msg) => {
      dispatch({ type: 'SET_PROGRESS', payload: { completed: 0, total: msg.total } });
      addToast(`Scanning target with ${msg.total} plugins...`, 'info', '🚀');
    },
    onResult: (msg) => {
      const result = mapPluginResult(msg.result as PluginResultData);
      dispatch({ type: 'ADD_RESULT', payload: result });
      dispatch({
        type: 'SET_PROGRESS',
        payload: { completed: msg.completed, total: msg.total },
      });
      const icon = result.status === 'failed' ? '⚠️' : '✅';
      const statusText = result.status === 'failed' ? 'Failed' : 'Done';
      addToast(`${icon} ${result.pluginName}: ${statusText}`, result.status === 'failed' ? 'error' : 'success', icon);
    },
    onComplete: () => {
      dispatch({ type: 'SET_SEARCHING', payload: false });
      addToast('🎉 Scan complete!', 'success', '✅');
      disconnect();
    },
    onError: () => {
      dispatch({ type: 'SET_SEARCHING', payload: false });
      addToast('⚠️ Scan failed to complete', 'error', '❌');
      disconnect();
    },
  });

  const runSearch = useCallback(
    async (query: string) => {
      dispatch({ type: 'RUN_SEARCH', payload: query });
      addToast(`🔍 Searching: ${query}`, 'info', '🔍');
      connect({ target: query });
    },
    [connect, addToast],
  );

  return (
    <AppContext.Provider value={{ state, dispatch, runSearch }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) throw new Error('useApp must be used within AppProvider');
  return context;
}
