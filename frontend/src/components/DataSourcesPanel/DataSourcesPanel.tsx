import React, { useEffect, useState, useCallback } from 'react';
import { useThreatContext } from '../../store/ThreatContext';

// ==================== Types ====================

interface SourceHealth {
  status: 'healthy' | 'error' | 'unknown';
  last_fetch: string | null;
  error: string | null;
  url?: string;
  description?: string;
  metrics?: Record<string, number | string>;
}

interface HealthData {
  overall: {
    status: 'healthy' | 'degraded';
    threat_feeds_healthy: boolean;
    rss_feeds_healthy: boolean;
    timestamp: string;
  };
  threat_intel_feeds: Record<string, SourceHealth>;
  news_rss_feeds: Record<string, SourceHealth>;
  reference_data: {
    source: string;
    status: string;
    description: string;
    year: number;
  };
}

// ==================== Constants ====================

const STATUS_CONFIG: Record<string, { icon: string; color: string; label: string }> = {
  healthy: { icon: '🟢', color: '#22c55e', label: 'Online' },
  error: { icon: '🔴', color: '#ef4444', label: 'Error' },
  unknown: { icon: '🟡', color: '#eab308', label: 'Connecting...' },
  static: { icon: '📄', color: '#3b82f6', label: 'Static Data' },
};

function statusIcon(status: string): string {
  return STATUS_CONFIG[status]?.icon || '⚪';
}

function statusColor(status: string): string {
  return STATUS_CONFIG[status]?.color || '#5a6a80';
}

function statusLabel(status: string): string {
  return STATUS_CONFIG[status]?.label || status;
}

function formatFetchTime(iso: string | null): string {
  if (!iso) return '—';
  try {
    const d = new Date(iso);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffSec = Math.floor(diffMs / 1000);
    if (diffSec < 60) return `${diffSec}s ago`;
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHr = Math.floor(diffMin / 60);
    return `${diffHr}h ago`;
  } catch {
    return iso;
  }
}

// ==================== Component ====================

interface DataSourcesPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function DataSourcesPanel({ isOpen, onClose }: DataSourcesPanelProps) {
  const [healthData, setHealthData] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { state: threatState } = useThreatContext();

  const fetchHealth = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/health/sources');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: HealthData = await res.json();
      setHealthData(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      fetchHealth();
      const interval = setInterval(fetchHealth, 15000);
      return () => clearInterval(interval);
    }
  }, [isOpen, fetchHealth]);

  if (!isOpen) return null;

  return (
    <div className="ds-overlay" onClick={onClose}>
      <div className="ds-panel" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="ds-header">
          <div className="ds-header-left">
            <span className="ds-header-icon">📡</span>
            <div className="ds-header-text">
              <span className="ds-header-title">Data Sources</span>
              <span className="ds-header-sub">Live health status of all intelligence feeds</span>
            </div>
          </div>
          <div className="ds-header-right">
            <button className="ds-refresh-btn" onClick={fetchHealth} disabled={loading}>
              {loading ? '⟳' : '↻'}
            </button>
            <button className="ds-close-btn" onClick={onClose}>✕</button>
          </div>
        </div>

        <div className="ds-body">
          {/* Overall Status */}
          {healthData && (
            <div className="ds-overall">
              <span
                className="ds-overall-dot"
                style={{ background: statusColor(healthData.overall.status) }}
              />
              <span className="ds-overall-text">
                {healthData.overall.status === 'healthy' ? 'All systems operational' : 'Degraded operation'}
              </span>
              <span className="ds-overall-time">
                Updated {formatFetchTime(healthData.overall.timestamp)}
              </span>
            </div>
          )}

          {/* WebSocket Connection */}
          <div className="ds-section">
            <div className="ds-section-title">CONNECTION</div>
            <div className="ds-source-row">
              <span className="ds-source-icon">{threatState.isConnected ? '🟢' : '🟡'}</span>
              <div className="ds-source-info">
                <span className="ds-source-name">WebSocket Threat Feed</span>
                <span className="ds-source-desc">{threatState.isConnected ? 'Connected — streaming real-time events' : 'Connecting...'}</span>
              </div>
              <span className="ds-source-status" style={{ color: threatState.isConnected ? '#22c55e' : '#eab308' }}>
                {threatState.isConnected ? 'LIVE' : 'Connecting'}
              </span>
            </div>
          </div>

          {/* Threat Intel Feeds */}
          <div className="ds-section">
            <div className="ds-section-title">
              THREAT INTELLIGENCE FEEDS
              {healthData && (
                <span className={`ds-section-badge ${healthData.overall.threat_feeds_healthy ? 'good' : 'warn'}`}>
                  {healthData.overall.threat_feeds_healthy ? 'ALL OK' : 'ISSUES'}
                </span>
              )}
            </div>
            {loading && !healthData ? (
              <div className="ds-loading">Loading feed status...</div>
            ) : healthData ? (
              Object.entries(healthData.threat_intel_feeds).map(([name, source]) => (
                <div key={name} className="ds-source-row">
                  <span className="ds-source-icon">{statusIcon(source.status)}</span>
                  <div className="ds-source-info">
                    <span className="ds-source-name">{name}</span>
                    <span className="ds-source-desc">{source.description}</span>
                    {source.last_fetch && (
                      <span className="ds-source-meta">Last fetch: {formatFetchTime(source.last_fetch)}</span>
                    )}
                    {source.error && (
                      <span className="ds-source-error">⚠ {source.error}</span>
                    )}
                  </div>
                  <div className="ds-source-stats">
                    <span className="ds-source-status" style={{ color: statusColor(source.status) }}>
                      {statusLabel(source.status)}
                    </span>
                    {source.metrics && Object.entries(source.metrics).map(([k, v]) => (
                      v !== undefined && v !== null && (
                        <span key={k} className="ds-source-stat">
                          {k === 'ip_count' ? `${v} IPs` :
                           k === 'geo_lookups' ? `${v} lookups` : `${k}=${v}`}
                        </span>
                      )
                    ))}
                  </div>
                </div>
              ))
            ) : (
              <div className="ds-error-text">{error || 'No data available'}</div>
            )}
          </div>

          {/* News RSS Feeds */}
          <div className="ds-section">
            <div className="ds-section-title">
              NEWS RSS FEEDS
              {healthData && (
                <span className={`ds-section-badge ${healthData.overall.rss_feeds_healthy ? 'good' : 'warn'}`}>
                  {healthData.overall.rss_feeds_healthy ? 'ALL OK' : 'ISSUES'}
                </span>
              )}
            </div>
            {healthData ? (
              Object.entries(healthData.news_rss_feeds).map(([name, source]) => (
                <div key={name} className="ds-source-row">
                  <span className="ds-source-icon">{statusIcon(source.status)}</span>
                  <div className="ds-source-info">
                    <span className="ds-source-name">{name}</span>
                    {source.last_fetch && (
                      <span className="ds-source-meta">Last fetch: {formatFetchTime(source.last_fetch)}</span>
                    )}
                    {source.error && (
                      <span className="ds-source-error">⚠ {source.error}</span>
                    )}
                  </div>
                  <div className="ds-source-stats">
                    <span className="ds-source-status" style={{ color: statusColor(source.status) }}>
                      {statusLabel(source.status)}
                    </span>
                    {source.metrics?.articles !== undefined && (
                      <span className="ds-source-stat">{source.metrics.articles} new</span>
                    )}
                  </div>
                </div>
              ))
            ) : loading ? (
              <div className="ds-loading">Loading RSS status...</div>
            ) : null}
          </div>

          {/* Reference Data */}
          <div className="ds-section">
            <div className="ds-section-title">REFERENCE DATA</div>
            {healthData && (
              <div className="ds-source-row">
                <span className="ds-source-icon">{statusIcon(healthData.reference_data.status)}</span>
                <div className="ds-source-info">
                  <span className="ds-source-name">{healthData.reference_data.source}</span>
                  <span className="ds-source-desc">{healthData.reference_data.description}</span>
                </div>
                <div className="ds-source-stats">
                  <span className="ds-source-status" style={{ color: statusColor(healthData.reference_data.status) }}>
                    {healthData.reference_data.year}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
