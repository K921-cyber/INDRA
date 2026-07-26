const API_BASE = '/api';

/** Read auth token from localStorage */
function getApiKey(): string | null {
  try {
    return localStorage.getItem('trinetra_api_key') || null;
  } catch {
    return null;
  }
}

/** Build default headers including auth token if stored */
function buildHeaders(extra?: Record<string, string>): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...extra,
  };
  const key = getApiKey();
  if (key) {
    headers['X-API-Key'] = key;
  }
  return headers;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: buildHeaders(options?.headers as Record<string, string> | undefined),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const msg = body?.detail?.detail || body?.detail || `API error: ${res.status} ${res.statusText}`;
    throw new Error(msg);
  }
  return res.json();
}

/** Download a markdown report from the backend as a formatted .docx file */
async function downloadDocx(target: string, markdown: string, filename: string) {
  const res = await fetch(`${API_BASE}/report/docx`, {
    method: 'POST',
    headers: buildHeaders(),
    body: JSON.stringify({ target, markdown }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const msg = body?.detail?.detail || body?.detail || `API error: ${res.status} ${res.statusText}`;
    throw new Error(msg);
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export interface SearchResponse {
  target: string;
  type: string;
  timestamp: string;
  total_plugins: number;
  completed_plugins: number;
  results: PluginResultData[];
}

export interface PluginResultData {
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
}

export interface PluginInfo {
  id: string;
  name: string;
  category: string;
  description: string;
  input_types: string[];
}

export interface DetectResponse {
  target: string;
  detected_type: string;
  confidence: number;
}

export interface WatchResponse {
  id: number;
  target: string;
  target_type: string;
  plugin_ids: string[];
  interval_seconds: number;
  webhook_url?: string;
  email?: string;
  is_active: boolean;
  last_checked_at?: string;
  created_at: string;
}

export interface AlertResponse {
  id: number;
  watch_id: number;
  target: string;
  plugin_id: string;
  old_data: Record<string, any>;
  new_data: Record<string, any>;
  summary: string;
  created_at: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatResponse {
  reply: string;
}

interface WatchCreatePayload {
  target: string;
  target_type?: string;
  plugin_ids?: string[];
  interval_seconds?: number;
  webhook_url?: string;
  email?: string;
}

/** Set or clear the auth token in localStorage */
export function setApiKey(key: string | null) {
  try {
    if (key) {
      localStorage.setItem('trinetra_api_key', key);
    } else {
      localStorage.removeItem('trinetra_api_key');
    }
  } catch {
    // localStorage unavailable
  }
}

/** Get the currently stored auth token */
export function getStoredApiKey(): string | null {
  return getApiKey();
}

export const api = {
  /** Run OSINT scan against a target */
  search: (target: string, type?: string) =>
    request<SearchResponse>('/search', {
      method: 'POST',
      body: JSON.stringify({ target, type }),
    }),

  /** Auto-detect target type */
  detect: (target: string) =>
    request<DetectResponse>(`/detect?target=${encodeURIComponent(target)}`),

  /** List all available plugins */
  listPlugins: () =>
    request<{ total: number; plugins: PluginInfo[] }>('/plugins'),

  /** Health check */
  health: () =>
    request<{ status: string; plugins_available: number }>('/health'),

  // ==================== Watches ====================

  /** Create a new watch */
  createWatch: (data: WatchCreatePayload) =>
    request<WatchResponse>('/watches', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  /** List all watches */
  listWatches: () =>
    request<WatchResponse[]>('/watches'),

  /** Get a single watch */
  getWatch: (id: number) =>
    request<WatchResponse>(`/watches/${id}`),

  /** Delete a watch */
  deleteWatch: (id: number) =>
    request<{ status: string; watch_id: number }>(`/watches/${id}`, {
      method: 'DELETE',
    }),

  /** Toggle watch on/off */
  toggleWatch: (id: number) =>
    request<{ status: string; watch_id: number; is_active: boolean }>(`/watches/${id}/toggle`, {
      method: 'POST',
    }),

  /** List recent alerts */
  listAlerts: (limit: number = 50) =>
    request<AlertResponse[]>(`/watches/alerts?limit=${limit}`),

  /** List alerts for a specific watch */
  listAlertsForWatch: (watchId: number) =>
    request<AlertResponse[]>(`/watches/${watchId}/alerts`),

  // ==================== Chatbot ====================

  /** Send a message to the AI assistant */
  chat: (message: string, history?: ChatMessage[], context?: string) =>
    request<ChatResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify({ message, history, context }),
    }),

  /** Export a chatbot-generated markdown report as a Word (.docx) file */
  exportReportDocx: (target: string, markdown: string) =>
    downloadDocx(target, markdown, `trinetra-report-${(target || 'report').replace(/[^a-zA-Z0-9]/g, '_')}.docx`),
};