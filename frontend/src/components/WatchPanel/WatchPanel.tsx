import React, { useState, useEffect, useCallback } from 'react';
import { api, WatchResponse, AlertResponse, PluginInfo } from '../../utils/api';
import { detectSearchType } from '../../utils/detectSearchType';
import { SearchType } from '../../types';
import { EyeIcon, RefreshIcon, BellIcon, TrashIcon, PlayIcon, PauseIcon, DownloadIcon } from '../Icons/Icons';
import FullReportView from '../FullReportView/FullReportView';

const SORTED_INTERVALS = [
  { label: 'Every 5 min', seconds: 300 },
  { label: 'Every 15 min', seconds: 900 },
  { label: 'Every 30 min', seconds: 1800 },
  { label: 'Every hour', seconds: 3600 },
  { label: 'Every 2 hours', seconds: 7200 },
  { label: 'Every 6 hours', seconds: 21600 },
  { label: 'Every 12 hours', seconds: 43200 },
  { label: 'Every 24 hours', seconds: 86400 },
  { label: 'Every 7 days', seconds: 604800 },
];

function formatInterval(seconds: number): string {
  const interval = SORTED_INTERVALS.find(i => i.seconds === seconds);
  if (interval) return interval.label;
  if (seconds < 3600) return `Every ${seconds / 60}m`;
  if (seconds < 86400) return `Every ${seconds / 3600}h`;
  return `Every ${Math.round(seconds / 86400)}d`;
}

function formatTime(iso: string | undefined | null): string {
  if (!iso) return 'Never';
  const d = new Date(iso);
  const now = Date.now();
  const diff = now - d.getTime();
  if (diff < 60000) return 'Just now';
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
  return d.toLocaleDateString();
}

// ── Plugin Selector Sub-component ───────────────────────────

const CATEGORY_ICONS: Record<string, string> = {
  infrastructure: '🖥',
  threat: '🛡',
  person: '👤',
  advanced: '⚡',
};

function PluginSelector({
  detectedType,
  selected,
  onChange,
}: {
  detectedType: SearchType;
  selected: string[];
  onChange: (ids: string[]) => void;
}) {
  const [plugins, setPlugins] = useState<PluginInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError('');
    api.listPlugins().then(res => {
      if (!cancelled) {
        setPlugins(res.plugins);
        setLoading(false);
      }
    }).catch((err: any) => {
      if (!cancelled) {
        setError(err.message || 'Failed to load plugins');
        setLoading(false);
      }
    });
    return () => { cancelled = true; };
  }, []);

  // Auto-select matching plugins when target type or plugin list changes
  useEffect(() => {
    if (plugins.length === 0 || detectedType === 'unknown') return;
    const matching = plugins
      .filter(p => p.input_types.includes(detectedType))
      .map(p => p.id);
    // Preserve any manually-selected plugins outside the current type
    const nonMatching = selected.filter(
      id => !plugins.find(p => p.id === id)?.input_types.includes(detectedType)
    );
    onChange([...new Set([...nonMatching, ...matching])]);
  }, [detectedType, plugins]);

  const categories = plugins.reduce<Record<string, PluginInfo[]>>((acc, p) => {
    (acc[p.category] ??= []).push(p);
    return acc;
  }, {});

  const categoryOrder = ['infrastructure', 'threat', 'person', 'advanced'];
  const categoryLabels: Record<string, string> = {
    infrastructure: 'Infrastructure',
    threat: 'Threat Intel',
    person: 'Person',
    advanced: 'Advanced',
  };

  const togglePlugin = (id: string) => {
    onChange(
      selected.includes(id)
        ? selected.filter(s => s !== id)
        : [...selected, id]
    );
  };

  const selectAllInCategory = (catPlugins: PluginInfo[]) => {
    const catIds = catPlugins.map(p => p.id);
    onChange([...new Set([...selected, ...catIds])]);
  };

  const deselectAllInCategory = (catPlugins: PluginInfo[]) => {
    const catIds = new Set(catPlugins.map(p => p.id));
    onChange(selected.filter(s => !catIds.has(s)));
  };

  const selectAllMatching = () => {
    if (detectedType === 'unknown') return;
    const matching = plugins
      .filter(p => p.input_types.includes(detectedType))
      .map(p => p.id);
    onChange(matching);
  };

  const allCount = plugins.length;
  const selectedCount = selected.length;

  return (
    <div className="plugin-selector">
      <button
        className={`ps-toggle ${expanded ? 'expanded' : ''}`}
        onClick={() => setExpanded(!expanded)}
        type="button"
      >
        <span className="ps-toggle-label">
          Scanning plugins
          <span className="ps-toggle-count">
            {loading ? '…' : `${selectedCount}/${allCount}`}
          </span>
        </span>
        <span className="ps-chevron">{expanded ? '▼' : '▶'}</span>
      </button>

      {expanded && (
        <div className="ps-body">
          {loading && (
            <div className="ps-loading">
              <div className="loading-spinner" />
            </div>
          )}
          {error && <div className="ps-error">{error}</div>}
          {!loading && !error && (
            <>
              {detectedType !== 'unknown' && (
                <button className="ps-match-btn" onClick={selectAllMatching} type="button">
                  Select all matching ({detectedType.toUpperCase()})
                </button>
              )}
              {categoryOrder.map(cat => {
                const catPlugins = categories[cat];
                if (!catPlugins || catPlugins.length === 0) return null;
                return (
                  <div key={cat} className="ps-category">
                    <div className="ps-category-header">
                      <span className="ps-cat-icon">{CATEGORY_ICONS[cat] || '📦'}</span>
                      <span className="ps-cat-name">{categoryLabels[cat] || cat}</span>
                      <span className="ps-cat-count">{catPlugins.length}</span>
                      <div className="ps-cat-actions">
                        <button
                          className="ps-cat-action"
                          onClick={() => selectAllInCategory(catPlugins)}
                          title="Select all"
                          type="button"
                        >All</button>
                        <button
                          className="ps-cat-action"
                          onClick={() => deselectAllInCategory(catPlugins)}
                          title="Deselect all"
                          type="button"
                        >None</button>
                      </div>
                    </div>
                    <div className="ps-plugin-list">
                      {catPlugins.map(p => {
                        const isSelected = selected.includes(p.id);
                        const isRelevant = detectedType !== 'unknown' && p.input_types.includes(detectedType);
                        return (
                          <label
                            key={p.id}
                            className={`ps-plugin ${isSelected ? 'selected' : ''} ${isRelevant ? 'relevant' : ''}`}
                          >
                            <input
                              type="checkbox"
                              className="ps-plugin-checkbox"
                              checked={isSelected}
                              onChange={() => togglePlugin(p.id)}
                            />
                            <span className="ps-plugin-check" />
                            <span className="ps-plugin-name">{p.name}</span>
                            {isRelevant && <span className="ps-plugin-match-indicator" title="Compatible with detected target type">✓</span>}
                          </label>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </>
          )}
        </div>
      )}
    </div>
  );
}

// ── Sub-component: New Watch Form ──────────────────────────

function NewWatchForm({ onCreated }: { onCreated: () => void }) {
  const [target, setTarget] = useState('');
  const [detectedType, setDetectedType] = useState<SearchType>('unknown');
  const [intervalSeconds, setIntervalSeconds] = useState(3600);
  const [selectedPlugins, setSelectedPlugins] = useState<string[]>([]);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');

  const handleChange = useCallback((val: string) => {
    setTarget(val);
    setDetectedType(val.trim() ? detectSearchType(val.trim()) : 'unknown');
  }, []);

  const handleCreate = useCallback(async () => {
    const q = target.trim();
    if (!q) return;
    setCreating(true);
    setError('');
    try {
      await api.createWatch({
        target: q,
        interval_seconds: intervalSeconds,
        plugin_ids: selectedPlugins.length > 0 ? selectedPlugins : undefined,
      });
      setTarget('');
      setDetectedType('unknown');
      setSelectedPlugins([]);
      onCreated();
    } catch (err: any) {
      setError(err.message || 'Failed to create watch');
    } finally {
      setCreating(false);
    }
  }, [target, intervalSeconds, selectedPlugins, onCreated]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleCreate();
  }, [handleCreate]);

  const badgeClass = `search-badge badge-${detectedType}`;

  return (
    <div className="new-watch-form">
      <div className="nwf-row">
        <div className="nwf-input-wrapper">
          <span className="nwf-icon"><EyeIcon size={16} /></span>
          <input
            className="nwf-input"
            type="text"
            placeholder="Target domain, IP, email, phone..."
            value={target}
            onChange={e => handleChange(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          {target.trim() && detectedType !== 'unknown' && (
            <span className={badgeClass}>{detectedType.toUpperCase()}</span>
          )}
        </div>
        <select
          className="nwf-select"
          value={intervalSeconds}
          onChange={e => setIntervalSeconds(Number(e.target.value))}
        >
          {SORTED_INTERVALS.map(i => (
            <option key={i.seconds} value={i.seconds}>{i.label}</option>
          ))}
        </select>
        <button className="nwf-btn" onClick={handleCreate} disabled={!target.trim() || creating}>
          {creating ? '⏳' : '+ Watch'}
        </button>
      </div>

      <PluginSelector
        detectedType={detectedType}
        selected={selectedPlugins}
        onChange={setSelectedPlugins}
      />

      {error && <div className="nwf-error">{error}</div>}
    </div>
  );
}

// ── Sub-component: Watch Row ───────────────────────────────

function WatchRow({
  watch,
  onToggled,
  onDeleted,
  alerts,
}: {
  watch: WatchResponse;
  onToggled: () => void;
  onDeleted: () => void;
  alerts: AlertResponse[];
}) {
  const [toggling, setToggling] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [showAlerts, setShowAlerts] = useState(false);

  const watchAlerts = alerts.filter(a => a.watch_id === watch.id);
  const criticalAlerts = watchAlerts.filter(a => a.summary.toLowerCase().includes('critical'));

  const handleToggle = useCallback(async () => {
    setToggling(true);
    try {
      await api.toggleWatch(watch.id);
      onToggled();
    } finally {
      setToggling(false);
    }
  }, [watch.id, onToggled]);

  const handleDelete = useCallback(async () => {
    setDeleting(true);
    try {
      await api.deleteWatch(watch.id);
      onDeleted();
    } finally {
      setDeleting(false);
    }
  }, [watch.id, onDeleted]);

  return (
    <div className={`watch-row ${!watch.is_active ? 'watch-inactive' : ''}`}>
      <div className="watch-row-main">
        <div className="watch-info">
          <span className="watch-target">{watch.target}</span>
          <span className="watch-badge">{watch.target_type}</span>
          <span className="watch-interval">{formatInterval(watch.interval_seconds)}</span>
        </div>
        <div className="watch-meta">
          <span className="watch-checked">Last: {formatTime(watch.last_checked_at)}</span>
          {watchAlerts.length > 0 && (
            <button
              className="watch-alert-count"
              onClick={() => setShowAlerts(!showAlerts)}
              title={`${watchAlerts.length} alert(s)`}
            >
              <BellIcon size={12} /> {watchAlerts.length}
              {criticalAlerts.length > 0 && ` (${criticalAlerts.length} critical)`}
            </button>
          )}
          <button
            className={`watch-toggle ${watch.is_active ? 'active' : ''}`}
            onClick={handleToggle}
            disabled={toggling}
            title={watch.is_active ? 'Pause watch' : 'Resume watch'}
          >
            {watch.is_active ? <PauseIcon size={14} color="var(--accent-green)" /> : <PlayIcon size={14} color="var(--text-muted)" />}
          </button>
          <button className="watch-delete" onClick={handleDelete} disabled={deleting} title="Delete watch">
            <TrashIcon size={14} />
          </button>
        </div>
      </div>

      {showAlerts && watchAlerts.length > 0 && (
        <div className="watch-alerts-list">
          {watchAlerts.slice(0, 10).map(a => (
            <div key={a.id} className="watch-alert-item">
              <div className="alert-header">
                <strong>{a.plugin_id}</strong>
                <span className="alert-time">{formatTime(a.created_at)}</span>
              </div>
              <div className="alert-summary">{a.summary}</div>
            </div>
          ))}
          {watchAlerts.length > 10 && (
            <div className="alert-more">+{watchAlerts.length - 10} more</div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Main WatchPanel Component ──────────────────────────────

export default function WatchPanel() {
  const [watches, setWatches] = useState<WatchResponse[]>([]);
  const [alerts, setAlerts] = useState<AlertResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showReport, setShowReport] = useState(false);

  const refresh = useCallback(async () => {
    setError('');
    try {
      const [w, a] = await Promise.all([
        api.listWatches(),
        api.listAlerts(100),
      ]);
      setWatches(w);
      setAlerts(a);
    } catch (err: any) {
      setError(err.message || 'Failed to load watches');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const activeWatches = watches.filter(w => w.is_active);
  const inactiveWatches = watches.filter(w => !w.is_active);

  return (
    <div className="watch-panel">
      <div className="watch-panel-header">          <h2><EyeIcon size={20} /> Watch & Monitoring</h2>
        <span className="watch-panel-subtitle">
          {loading ? 'Loading...' : `${activeWatches.length} active · ${inactiveWatches.length} paused`}
        </span>
        <div className="watch-panel-actions">
          <button className="watch-report-btn" onClick={() => setShowReport(true)} title="Generate full intelligence report">
            <DownloadIcon size={12} /> Report
          </button>
          <button className="watch-refresh-btn" onClick={refresh} title="Refresh">
            <RefreshIcon size={14} />
          </button>
        </div>
      </div>

      {/* Create form */}
      <NewWatchForm onCreated={refresh} />

      {error && <div className="watch-error">{error}</div>}

      {loading ? (
        <div className="watch-loading">
          <div className="loading-spinner" />
        </div>
      ) : watches.length === 0 ? (
        <div className="watch-empty">
          <div className="watch-empty-icon"><EyeIcon size={48} color="var(--text-muted)" /></div>
          <h3>No watches yet</h3>
          <p>Enter a target above to start monitoring. TRINETRA will re-scan it at the configured interval and alert you of changes.</p>
        </div>
      ) : (
        <div className="watch-list">
          <div className="watch-section-label">Active ({activeWatches.length})</div>
          {activeWatches.map(w => (
            <WatchRow key={w.id} watch={w} onToggled={refresh} onDeleted={refresh} alerts={alerts} />
          ))}

          {inactiveWatches.length > 0 && (
            <>
              <div className="watch-section-label paused">Paused ({inactiveWatches.length})</div>
              {inactiveWatches.map(w => (
                <WatchRow key={w.id} watch={w} onToggled={refresh} onDeleted={refresh} alerts={alerts} />
              ))}
            </>
          )}
        </div>
      )}

      {/* Recent Alerts Summary */}
      {alerts.length > 0 && !loading && (
        <div className="watch-alerts-summary">
          <div className="watch-section-label">Recent Alerts ({alerts.length})</div>
          <div className="alert-mini-list">
            {alerts.slice(0, 5).map(a => (
              <div key={a.id} className="alert-mini-item">
                <span className="alert-mini-time">{formatTime(a.created_at)}</span>
                <span className="alert-mini-target">{a.target}</span>
                <span className="alert-mini-text">{a.summary.slice(0, 120)}{a.summary.length > 120 ? '…' : ''}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Full Report Overlay */}
      {showReport && <FullReportView onClose={() => setShowReport(false)} />}
    </div>
  );
}
