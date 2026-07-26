import { ToolResult } from '../types';
import { PluginResultData } from './api';

/** Map API response (snake_case) to frontend ToolResult (camelCase) */
export function mapPluginResult(r: PluginResultData): ToolResult {
  return {
    pluginId: r.plugin_id,
    pluginName: r.plugin_name,
    category: r.category as ToolResult['category'],
    target: r.target,
    freshness: r.freshness as ToolResult['freshness'],
    timestamp: r.timestamp,
    status: r.status as ToolResult['status'],
    guiData: r.gui_data,
    terminalData: r.terminal_data,
  };
}
