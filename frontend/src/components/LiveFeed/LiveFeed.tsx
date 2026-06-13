import React, { useState, useMemo } from 'react';
import { useThreatContext } from '../../store/ThreatContext';
import { ThreatAttackVector } from '../../utils/useThreatFeed';
import { useApp } from '../../store/AppContext';
import { AttackVector } from '../../types';
import { VectorDetailModal, VectorLike } from '../VectorDetailModal/VectorDetailModal';
import { BoltIcon, AlertTriangleIcon, ShieldIcon, ClockIcon, CrosshairIcon, SearchIcon, CloseIcon } from '../Icons/Icons';

type FeedTab = 'all' | 'attacks' | 'events' | 'news';

export default function LiveFeed() {
  const { state: threatState } = useThreatContext();
  const { dispatch } = useApp();
  const [feedFilter, setFeedFilter] = useState<FeedTab>('all');
  const [selectedVector, setSelectedVector] = useState<VectorLike | null>(null);

  // Safely get timestamp from AttackVector or ThreatAttackVector
  const getTimestamp = (av: AttackVector | ThreatAttackVector) => {
    if ('timestamp' in av) {
      return formatTime(av.timestamp);
    }
    return 'recent';
  };

  const formatTime = (ts: string) => {
    const d = new Date(ts);
    const now = Date.now();
    const diff = now - d.getTime();
    if (diff < 60000) return 'just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return d.toLocaleDateString();
  };

  const activeVectors = threatState.attackVectors;

  // All events come from the live WebSocket feed (real RSS news + threat events)
  const allEvents = useMemo(() => {
    return threatState.tickerEvents.map(e => ({
      ...e,
      source: e.source || 'Live Feed',
    })).sort(
      (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
  }, [threatState.tickerEvents]);

  // Filter events
  const filteredEvents = useMemo(() => {
    switch (feedFilter) {
      case 'attacks':
        return allEvents.filter(e => e.type === 'threat_event');
      case 'events':
        return allEvents.filter(e => e.type === 'news_event');
      case 'news':
        return allEvents.filter(e => e.type === 'news_event');
      default:
        return allEvents;
    }
  }, [feedFilter, allEvents]);

  const criticalCount = activeVectors.filter(v => v.severity === 'critical').length;
  const mediumCount = activeVectors.filter(v => v.severity === 'medium').length;
  const totalAttacks = activeVectors.length;



  return (
    <div className="live-feed-page">
      {/* Header */}
      <div className="live-feed-header">
        <div className="live-feed-header-left">
          <h2>
            <span className="live-feed-title-icon">
              <BoltIcon size={18} color="var(--accent-red)" />
            </span>
            Live Threat Feed
          </h2>
          <div className="live-feed-status">
            <span className={`live-feed-dot ${threatState.isConnected ? 'connected' : ''}`} />
            {threatState.isConnected ? 'Connected' : 'Disconnected'}
          </div>
        </div>
        <div className="live-feed-stats-row">
          <div className="live-feed-stat-card critical">
            <span className="live-feed-stat-value">{criticalCount}</span>
            <span className="live-feed-stat-label">Critical</span>
          </div>
          <div className="live-feed-stat-card medium">
            <span className="live-feed-stat-value">{mediumCount}</span>
            <span className="live-feed-stat-label">Medium</span>
          </div>
          <div className="live-feed-stat-card total">
            <span className="live-feed-stat-value">{totalAttacks}</span>
            <span className="live-feed-stat-label">Attack Vectors</span>
          </div>
          <div className="live-feed-stat-card events">
            <span className="live-feed-stat-value">{allEvents.length}</span>
            <span className="live-feed-stat-label">Total Events</span>
          </div>
        </div>
      </div>

      {/* Main content area */}
      <div className="live-feed-body">
        {/* Attack Vectors Map/Section */}
        <div className="live-feed-attacks-section">
          <div className="live-feed-section-header">
            <div className="live-feed-section-title">
              <CrosshairIcon size={14} color="var(--accent-red)" />
              <span>Active Attack Vectors</span>
            </div>
            <div className="live-feed-section-count">{activeVectors.length} active</div>
          </div>
          <div className="live-feed-attacks-grid">
            {activeVectors.map((av) => {
              const severityColor = av.severity === 'critical' ? 'var(--accent-red)' 
                : av.severity === 'medium' ? 'var(--accent-yellow)' 
                : 'var(--accent-green)';
              return (
                <div 
                  key={av.id} 
                  className={`live-feed-attack-card ${av.severity}`}
                  onClick={() => setSelectedVector(av)}
                  title="Click for full details & report"
                >
                  <div className="attack-card-header">
                    <span className="attack-card-type" style={{ color: severityColor }}>
                      {av.attackType}
                    </span>
                    <span className="attack-card-severity" style={{ background: `${severityColor}18`, color: severityColor, border: `1px solid ${severityColor}30` }}>
                      {av.severity.toUpperCase()}
                    </span>
                  </div>
                  <div className="attack-card-route">
                    <span className="attack-from">{av.from}</span>
                    <span className="attack-arrow">→</span>
                    <span className="attack-to">{av.to}</span>
                  </div>
                  <div className="attack-card-time">
                    <ClockIcon size={10} color="var(--text-muted)" />
                    {getTimestamp(av)}
                  </div>
                  {av.modeledTarget && (
                    <div style={{ fontSize: 9, color: 'var(--text-muted)', marginTop: 6, padding: '3px 6px', borderRadius: 4, background: 'rgba(234, 179, 8, 0.08)', border: '1px solid rgba(234, 179, 8, 0.12)', display: 'inline-block' }}>
                      🎯 Target estimated from statistical crime data
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Events Timeline */}
        <div className="live-feed-events-section">
          <div className="live-feed-section-header">
            <div className="live-feed-section-title">
              <AlertTriangleIcon size={14} color="var(--accent-yellow)" />
              <span>Threat Events & News</span>
            </div>
            <div className="live-feed-filter-tabs">
              {(['all', 'attacks', 'events', 'news'] as FeedTab[]).map(tab => (
                <button
                  key={tab}
                  className={`live-feed-filter-tab ${feedFilter === tab ? 'active' : ''}`}
                  onClick={() => setFeedFilter(tab)}
                >
                  {tab === 'all' ? 'All' : tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </div>
          </div>
          <div className="live-feed-events-list">
            {filteredEvents.length === 0 ? (
              <div className="live-feed-empty">
                <ShieldIcon size={24} color="var(--text-muted)" />
                <p>No events to display</p>
              </div>
            ) : (
              filteredEvents.slice(0, 50).map((ev) => {
                const severityColor = ev.severity === 'critical' ? 'var(--accent-red)' 
                  : ev.severity === 'medium' ? 'var(--accent-yellow)' 
                  : 'var(--accent-green)';
                const isNews = ev.type === 'news_event';
                const hasUrl = 'url' in ev && ev.url;
                return (
                  <div 
                    key={ev.id} 
                    className={`live-feed-event-item ${ev.severity} ${hasUrl ? 'has-link' : ''}`}
                    onClick={() => {
                      if (hasUrl) window.open(ev.url, '_blank', 'noopener,noreferrer');
                    }}
                    style={hasUrl ? { cursor: 'pointer' } : undefined}
                    title={hasUrl ? 'Open article in new tab' : undefined}
                  >
                    <div className="live-feed-event-indicator" style={{ background: severityColor }} />
                    <span className="live-feed-event-icon">{ev.icon}</span>
                    <div className="live-feed-event-content">
                      <span className={`live-feed-event-text ${isNews ? 'news-text' : ''}`}>
                        {ev.text}
                        {isNews && <span className="news-link-icon"> ↗</span>}
                      </span>
                      <div className="live-feed-event-meta">
                        {'source' in ev && ev.source && (
                          <span className="live-feed-event-source">{ev.source}</span>
                        )}
                        <span className="live-feed-event-time">{formatTime(ev.timestamp)}</span>
                      </div>
                    </div>
                    <span className="live-feed-event-severity" style={{ color: severityColor }}>
                      {ev.severity.toUpperCase()}
                    </span>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* Vector detail modal */}
      <VectorDetailModal vector={selectedVector} onClose={() => setSelectedVector(null)} />
    </div>
  );
}
