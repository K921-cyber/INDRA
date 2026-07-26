// ==================== Search Types ====================

export type SearchType = 'domain' | 'ip' | 'email' | 'phone' | 'username' | 'name' | 'unknown';

export interface SearchResult {
  target: string;
  type: SearchType;
  timestamp: string;
}

// ==================== Tool/Plugin Types ====================

export type ToolCategory = 'infrastructure' | 'threat' | 'advanced';
export type ViewMode = 'gui' | 'terminal' | 'split';
export type RiskLevel = 'safe' | 'medium' | 'critical';
export type Freshness = 'moments' | 'minutes' | 'hours' | 'days' | 'weeks';

export interface ToolPlugin {
  id: string;
  name: string;
  description: string;
  category: ToolCategory;
  icon: string;
  inputTypes: SearchType[];
  enabled: boolean;
}

export interface ToolResult {
  pluginId: string;
  pluginName: string;
  category: ToolCategory;
  target: string;
  freshness: Freshness;
  timestamp: string;
  status: 'running' | 'completed' | 'failed';
  guiData: Record<string, any>;
  terminalData: string;
}

// ==================== Map Types ====================

export interface CityData {
  name: string;
  lat: number;
  lng: number;
  risk: RiskLevel;
  assetCount: number;
  activeThreats: number;
  headlines: string[];
}

export interface AttackVector {
  id: string;
  from: string;
  fromLat: number;
  fromLng: number;
  to: string;
  toLat: number;
  toLng: number;
  attackType: string;
  severity: RiskLevel;
  sourceIp?: string;
  isp?: string;
  org?: string;
  source?: string;
  malware?: string;
}

export interface CrimeDataPoint {
  state: string;
  stateCode: string;
  incidentCount: number;
  risk: RiskLevel;
  coordinates: [number, number];
}

// ==================== Graph Types ====================

export type GraphNodeType = 'target' | 'ip' | 'dns' | 'geo' | 'port' | 'cve' | 'email' | 'domain' | 'infrastructure' | 'threat' | 'advanced';

export interface GraphNode {
  id: string;
  label: string;
  type: GraphNodeType;
  data?: Record<string, any>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// ==================== Store Types ====================

export interface AppState {
  searchQuery: string;
  searchType: SearchType;
  isSearching: boolean;
  results: ToolResult[];
  totalPlugins: number;
  completedPlugins: number;
  activeToolId: string | null;
  viewMode: ViewMode;
  mapCenter: [number, number];
  mapZoom: number;
  selectedCity: CityData | null;
  showCrimeOverlay: boolean;
  showGraphView: boolean;
  activeTab: AppTab;
  toasts: Toast[];
}

// ==================== Watch Types ====================

export interface WatchEntry {
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

export interface AlertEntry {
  id: number;
  watch_id: number;
  target: string;
  plugin_id: string;
  old_data: Record<string, any>;
  new_data: Record<string, any>;
  summary: string;
  created_at: string;
}

export type ActiveView = 'dashboard' | 'watches';

export type AppTab = 'search' | 'watches' | 'feed';

// ==================== Toast Types ====================

export interface Toast {
  id: number;
  message: string;
  type: 'info' | 'success' | 'error' | 'warning';
  icon: string;
}
