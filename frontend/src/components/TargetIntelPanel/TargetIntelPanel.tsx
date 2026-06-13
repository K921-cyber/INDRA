import React, { useState, useEffect } from 'react';
import { useApp } from '../../store/AppContext';
import { GlobeIcon, SearchIcon, AlertTriangleIcon } from '../Icons/Icons';

interface WebResult {
  title: string;
  snippet: string;
  url: string;
  source: string;
  type: string;
}

interface NewsMention {
  id: string;
  text: string;
  url?: string;
  icon: string;
  source: string;
  severity: string;
  timestamp: string;
}

interface TargetIntelData {
  target: string;
  target_type: string;
  detected: any;
  web_results: WebResult[];
  news_mentions: NewsMention[];
  related_info: Record<string, string>;
  total_web: number;
  total_news: number;
  timestamp: string;
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  const now = Date.now();
  const diff = now - d.getTime();
  if (diff < 60000) return 'just now';
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
}

function getDomain(url: string): string {
  try {
    return new URL(url).hostname.replace('www.', '');
  } catch {
    return url;
  }
}

export default function TargetIntelPanel() {
  const { state } = useApp();
  const [data, setData] = useState<TargetIntelData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [expanded, setExpanded] = useState(true);
  const [webExpanded, setWebExpanded] = useState(true);
  const [newsExpanded, setNewsExpanded] = useState(true);

  const query = state.searchQuery;

  useEffect(() => {
    if (!query) {
      setData(null);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError('');

    fetch(`/api/target-intel?target=${encodeURIComponent(query)}`)
      .then(res => {
        if (!res.ok) throw new Error(`API error: ${res.status}`);
        return res.json();
      })
      .then((result: TargetIntelData) => {
        if (!cancelled) {
          setData(result);
          setLoading(false);
        }
      })
      .catch((err: any) => {
        if (!cancelled) {
          setError(err.message || 'Failed to fetch intel');
          setLoading(false);
        }
      });

    return () => { cancelled = true; };
  }, [query]);

  // Don't show if idle
  if (!query) return null;

  return (
    <div className="target-intel-panel">
      <div className="tip-header" onClick={() => setExpanded(!expanded)}>
        <div className="tip-header-left">
          <GlobeIcon size={13} color="var(--accent-cyan)" />
          <span className="tip-header-title">Target Intelligence</span>
          {loading && <span className="tip-loading-dot" />}
        </div>
        <div className="tip-header-right">
          {data && !loading && (
            <span className="tip-header-count">{data.total_web + data.total_news}</span>
          )}
          <span className="tip-chevron">{expanded ? '▼' : '▶'}</span>
        </div>
      </div>

      {expanded && (
        <div className="tip-body">
          {loading && (
            <div className="tip-loading">
              <div className="loading-spinner" />
              <span>Searching web for "{query}"...</span>
            </div>
          )}

          {error && (
            <div className="tip-error">
              <AlertTriangleIcon size={12} color="var(--accent-red)" />
              <span>{error}</span>
            </div>
          )}

          {data && !loading && (
            <>
              {/* Target badge */}
              <div className="tip-target-badge">
                <SearchIcon size={10} color="var(--text-muted)" />
                <span className="tip-target-text">{data.target}</span>
                <span className="tip-target-type">{data.target_type.toUpperCase()}</span>
              </div>

              {/* ── Web Results ── */}
              {data.web_results.length > 0 && (
                <div className="tip-section">
                  <div className="tip-section-header" onClick={() => setWebExpanded(!webExpanded)}>
                    <GlobeIcon size={11} color="var(--accent-blue)" />
                    <span className="tip-section-title">Web Results ({data.total_web})</span>
                    <span className="tip-chevron">{webExpanded ? '▼' : '▶'}</span>
                  </div>
                  {webExpanded && (
                    <div className="tip-results">
                      {data.web_results.slice(0, 8).map((r, i) => (
                        <a key={i} href={r.url} target="_blank" rel="noopener noreferrer" className="tip-result-card">
                          <div className="tip-result-title">{r.title || 'Related link'}</div>
                          <div className="tip-result-snippet">{r.snippet}</div>
                          <div className="tip-result-meta">
                            <span className="tip-result-source">{getDomain(r.url) || r.source}</span>
                            <span className="tip-result-external">↗</span>
                          </div>
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* ── News Mentions ── */}
              {data.news_mentions.length > 0 && (
                <div className="tip-section">
                  <div className="tip-section-header" onClick={() => setNewsExpanded(!newsExpanded)}>
                    <span style={{ fontSize: 11 }}>📰</span>
                    <span className="tip-section-title">News Mentions ({data.total_news})</span>
                    <span className="tip-chevron">{newsExpanded ? '▼' : '▶'}</span>
                  </div>
                  {newsExpanded && (
                    <div className="tip-news-list">
                      {data.news_mentions.map((item) => (
                        <div
                          key={item.id}
                          className="tip-news-item"
                          onClick={() => {
                            if (item.url) window.open(item.url, '_blank', 'noopener,noreferrer');
                          }}
                          style={item.url ? { cursor: 'pointer' } : undefined}
                        >
                          <span className="tip-news-icon">{item.icon || '📰'}</span>
                          <div className="tip-news-content">
                            <span className="tip-news-text">{item.text}</span>
                            <div className="tip-news-meta">
                              <span className="tip-news-source">{item.source}</span>
                              <span className="tip-news-time">{formatTime(item.timestamp)}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* ── Empty State ── */}
              {data.web_results.length === 0 && data.news_mentions.length === 0 && (
                <div className="tip-empty">
                  <SearchIcon size={16} color="var(--text-muted)" />
                  <span>No web intelligence found for "{query}"</span>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
