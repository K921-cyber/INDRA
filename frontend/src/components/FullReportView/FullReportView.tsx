import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useApp } from '../../store/AppContext';
import { useThreatContext } from '../../store/ThreatContext';
import { api, WatchResponse, AlertResponse } from '../../utils/api';
import {
  ShieldIcon, EyeIcon, BoltIcon, AlertTriangleIcon,
  DownloadIcon, CloseIcon, CheckCircleIcon, ClockIcon, BellIcon
} from '../Icons/Icons';

// ── Helpers ─────────────────────────────────────────────────

function formatTime(iso: string | undefined | null): string {
  if (!iso) return 'Never';
  const d = new Date(iso);
  const now = Date.now();
  const diff = now - d.getTime();
  if (diff < 60000) return 'Just now';
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}

function formatInterval(seconds: number): string {
  if (seconds < 3600) return `Every ${seconds / 60} min`;
  if (seconds < 86400) return `Every ${seconds / 3600} h`;
  return `Every ${Math.round(seconds / 86400)} d`;
}

function fmtTimestamp(ts: string | undefined | null): string {
  if (!ts) return '—';
  const d = new Date(ts);
  return d.toLocaleString('en-IN', {
    day: 'numeric', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  });
}

// ── Sub-component: Severity Badge ────────────────────────────

function SevBadge({ severity }: { severity: string }) {
  const cls = severity === 'critical' ? 'rp-sev-critical' : severity === 'medium' ? 'rp-sev-medium' : 'rp-sev-safe';
  return <span className={`rp-sev-badge ${cls}`}>{severity.toUpperCase()}</span>;
}

// ── Main Component ────────────────────────────────────────────

export default function FullReportView({ onClose }: { onClose: () => void }) {
  const { state: appState } = useApp();
  const { state: threatState } = useThreatContext();

  const [watches, setWatches] = useState<WatchResponse[]>([]);
  const [alerts, setAlerts] = useState<AlertResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError('');
    Promise.all([
      api.listWatches(),
      api.listAlerts(100),
    ]).then(([w, a]) => {
      if (!cancelled) {
        setWatches(w);
        setAlerts(a);
        setLoading(false);
      }
    }).catch((err: any) => {
      if (!cancelled) {
        setError(err.message || 'Failed to load data');
        setLoading(false);
      }
    });
    return () => { cancelled = true; };
  }, []);

  const handlePrint = useCallback(() => {
    window.print();
  }, []);

  // ── Computed stats ───────────────────────────────────────

  const stats = useMemo(() => ({
    totalPlugins: 20,
    attackVectors: threatState.attackVectors.length,
    criticalThreats: threatState.criticalThreats,
    totalEvents: threatState.totalIncidents,
    activeWatches: watches.filter(w => w.is_active).length,
    pausedWatches: watches.filter(w => !w.is_active).length,
    totalAlerts: alerts.length,
    completedScans: appState.results.filter(r => r.status === 'completed').length,
    failedScans: appState.results.filter(r => r.status === 'failed').length,
  }), [threatState, watches, alerts, appState.results]);

  const now = new Date().toLocaleString('en-IN', {
    day: 'numeric', month: 'long', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });

  return (
    <div className="rp-overlay">
      <div className="rp-document" id="full-report">
        {/* ── Toolbar ───────────────────────────────────────── */}
        <div className="rp-toolbar no-print">
          <div className="rp-toolbar-left">
            <span className="rp-toolbar-icon">📋</span>
            <div className="rp-toolbar-info">
              <span className="rp-toolbar-title">Threat Intelligence Report</span>
              <span className="rp-toolbar-sub">Full system overview</span>
            </div>
          </div>
          <div className="rp-toolbar-right">
            <button className="rp-action-btn rp-btn-primary" onClick={handlePrint}>
              <DownloadIcon size={12} /> Save as PDF
            </button>
            <button className="rp-close-btn" onClick={onClose}>
              <CloseIcon size={12} color="var(--text-muted)" />
            </button>
          </div>
        </div>

        {/* ── Body ──────────────────────────────────────────── */}
        <div className="rp-body">
          {error && (
            <div style={{ color: 'var(--accent-red)', padding: 16, textAlign: 'center', fontSize: 13 }}>
              {error}
            </div>
          )}

          {loading ? (
            <div style={{ textAlign: 'center', padding: 60 }}>
              <div className="loading-spinner" />
              <p style={{ marginTop: 12, color: 'var(--text-muted)', fontSize: 13 }}>Loading report data...</p>
            </div>
          ) : (
            <>
              {/* ═══════════ COVER PAGE ═══════════ */}
              <div className="rp-cover-page">
                <div className="rp-cover-classification">TOP SECRET // SI // TK // NOFORN</div>
                <div className="rp-cover-emblem">
                  <ShieldIcon size={48} color="var(--accent-blue)" />
                </div>
                <h1 className="rp-cover-title">TRINETRA</h1>
                <div className="rp-cover-subtitle">OPERATIONAL INTELLIGENCE REPORT</div>
                <div className="rp-cover-divider" />
                <div className="rp-cover-meta">
                  <div className="rp-cover-meta-item">
                    <span className="rp-cover-meta-label">Report Date</span>
                    <span className="rp-cover-meta-value">{now}</span>
                  </div>
                  <div className="rp-cover-meta-item">
                    <span className="rp-cover-meta-label">Classification</span>
                    <span className="rp-cover-meta-value" style={{ color: '#dc2626' }}>TOP SECRET // SI // TK // NOFORN</span>
                  </div>
                  <div className="rp-cover-meta-item">
                    <span className="rp-cover-meta-label">Prepared By</span>
                    <span className="rp-cover-meta-value">TRINETRA OSINT Platform v1.0</span>
                  </div>
                  <div className="rp-cover-meta-item">
                    <span className="rp-cover-meta-label">Status</span>
                    <span className="rp-cover-meta-value" style={{ color: '#22c55e' }}>OPERATIONAL</span>
                  </div>
                </div>
                <div className="rp-cover-footer">
                  <p>This report contains information gathered from open-source intelligence (OSINT) channels.</p>
                  <p>Distribution is limited to authorized personnel only.</p>
                </div>
              </div>

              {/* ═══════════ PAGE BREAK ═══════════ */}
              <div className="rp-page-break" />

              {/* ═══════════ EXECUTIVE SUMMARY ═══════════ */}
              <div className="rp-section">
                <div className="rp-classification-bar">TOP SECRET // SI // TK // NOFORN</div>
                <h2 className="rp-section-title">1. Executive Summary</h2>
                <p className="rp-section-desc">
                  Comprehensive threat intelligence overview generated by TRINETRA OSINT platform.
                  Aggregates live threat feeds, active monitoring watches, and scan results.
                </p>
                <div className="rp-summary-grid">
                  <div className="rp-summary-card">
                    <div className="rp-summary-icon"><ShieldIcon size={18} color="var(--accent-cyan)" /></div>
                    <div className="rp-summary-info">
                      <span className="rp-summary-value">{stats.totalPlugins}</span>
                      <span className="rp-summary-label">OSINT Plugins</span>
                    </div>
                  </div>
                  <div className="rp-summary-card rp-card-critical">
                    <div className="rp-summary-icon"><AlertTriangleIcon size={18} color="var(--accent-red)" /></div>
                    <div className="rp-summary-info">
                      <span className="rp-summary-value">{stats.criticalThreats}</span>
                      <span className="rp-summary-label">Critical Threats</span>
                    </div>
                  </div>
                  <div className="rp-summary-card">
                    <div className="rp-summary-icon"><BoltIcon size={18} color="var(--accent-orange)" /></div>
                    <div className="rp-summary-info">
                      <span className="rp-summary-value">{stats.attackVectors}</span>
                      <span className="rp-summary-label">Attack Vectors</span>
                    </div>
                  </div>
                  <div className="rp-summary-card">
                    <div className="rp-summary-icon"><BellIcon size={18} color="var(--accent-red)" /></div>
                    <div className="rp-summary-info">
                      <span className="rp-summary-value">{stats.totalAlerts}</span>
                      <span className="rp-summary-label">Watch Alerts</span>
                    </div>
                  </div>
                  <div className="rp-summary-card">
                    <div className="rp-summary-icon"><EyeIcon size={18} color="var(--accent-blue)" /></div>
                    <div className="rp-summary-info">
                      <span className="rp-summary-value">{stats.activeWatches}</span>
                      <span className="rp-summary-label">Active Watches</span>
                    </div>
                  </div>
                  <div className="rp-summary-card">
                    <div className="rp-summary-icon"><CheckCircleIcon size={18} color="var(--accent-green)" /></div>
                    <div className="rp-summary-info">
                      <span className="rp-summary-value">{stats.completedScans}</span>
                      <span className="rp-summary-label">Completed Scans</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* ═══════════ THREAT LANDSCAPE ═══════════ */}
              <div className="rp-section">
                <h2 className="rp-section-title">2. Live Threat Landscape</h2>
                <p className="rp-section-desc">
                  Real-time attack vectors detected from global threat intelligence feeds
                  (ThreatFox, Feodo Tracker, IPsum) targeting Indian infrastructure.
                </p>

                {threatState.attackVectors.length === 0 ? (
                  <div className="rp-empty">No attack vectors detected in current session.</div>
                ) : (
                  <>
                    {/* Severity Distribution */}
                    <div className="rp-subsection">
                      <h3 className="rp-subsection-title">Severity Distribution</h3>
                      <div className="rp-sev-dist">
                        {['critical', 'medium', 'safe'].map(sev => {
                          const count = threatState.attackVectors.filter(v => v.severity === sev).length;
                          const pct = threatState.attackVectors.length > 0
                            ? Math.round((count / threatState.attackVectors.length) * 100)
                            : 0;
                          return (
                            <div key={sev} className="rp-sev-dist-item">
                              <span className="rp-sev-dist-label">{sev}</span>
                              <div className="rp-sev-dist-track">
                                <div
                                  className={`rp-sev-dist-fill rp-sev-${sev}`}
                                  style={{ width: `${pct}%` }}
                                />
                              </div>
                              <span className="rp-sev-dist-count">{count} ({pct}%)</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    {/* Recent Attack Vectors Table */}
                    <div className="rp-subsection">
                      <h3 className="rp-subsection-title">Recent Attack Vectors (last 20)</h3>
                      <table className="rp-table">
                        <thead>
                          <tr>
                            <th>Source IP</th>
                            <th>Origin → Target</th>
                            <th>Attack Type</th>
                            <th>Malware</th>
                            <th>Feed</th>
                            <th>Severity</th>
                          </tr>
                        </thead>
                        <tbody>
                          {threatState.attackVectors.slice(-20).reverse().map(v => (
                            <tr key={v.id}>
                              <td className="rp-mono">{v.sourceIp || '—'}</td>
                              <td>{v.from} → {v.to}</td>
                              <td>{v.attackType}</td>
                              <td>{v.malware || '—'}</td>
                              <td>{v.source || '—'}</td>
                              <td><SevBadge severity={v.severity} /></td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </>
                )}
              </div>

              {/* ═══════════ WATCHES & MONITORING ═══════════ */}
              <div className="rp-page-break" />
              <div className="rp-section">
                <div className="rp-classification-bar">TOP SECRET // SI // TK // NOFORN</div>
                <h2 className="rp-section-title">3. Watches & Monitoring</h2>
                <p className="rp-section-desc">
                  Continuously monitored targets with automated re-scanning and change detection.
                </p>

                {error ? (
                  <div className="rp-empty" style={{ color: 'var(--accent-red)', borderColor: 'rgba(239,68,68,0.2)' }}>
                    ⚠️ Could not load watch data — {error}
                  </div>
                ) : watches.length === 0 ? (
                  <div className="rp-empty">No watches configured.</div>
                ) : (
                  <>
                    {/* Active Watches */}
                    <div className="rp-subsection">
                      <h3 className="rp-subsection-title">
                        Active Watches ({stats.activeWatches})
                      </h3>
                      <table className="rp-table">
                        <thead>
                          <tr>
                            <th>Target</th>
                            <th>Type</th>
                            <th>Interval</th>
                            <th>Plugins</th>
                            <th>Last Checked</th>
                            <th>Alerts</th>
                          </tr>
                        </thead>
                        <tbody>
                          {watches.filter(w => w.is_active).map(w => {
                            const watchAlerts = alerts.filter(a => a.watch_id === w.id);
                            return (
                              <tr key={w.id}>
                                <td className="rp-mono">{w.target}</td>
                                <td><span className="rp-type-badge">{w.target_type}</span></td>
                                <td>{formatInterval(w.interval_seconds)}</td>
                                <td>{w.plugin_ids?.length || 'All matching'}</td>
                                <td>{formatTime(w.last_checked_at)}</td>
                                <td>
                                  <span style={{ color: watchAlerts.length > 0 ? 'var(--accent-red)' : 'var(--text-muted)' }}>
                                    {watchAlerts.length}
                                  </span>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>

                    {/* Paused Watches */}
                    {stats.pausedWatches > 0 && (
                      <div className="rp-subsection">
                        <h3 className="rp-subsection-title">
                          Paused Watches ({stats.pausedWatches})
                        </h3>
                        <table className="rp-table">
                          <thead>
                            <tr>
                              <th>Target</th>
                              <th>Type</th>
                              <th>Interval</th>
                              <th>Last Checked</th>
                            </tr>
                          </thead>
                          <tbody>
                            {watches.filter(w => !w.is_active).map(w => (
                              <tr key={w.id}>
                                <td className="rp-mono">{w.target}</td>
                                <td><span className="rp-type-badge">{w.target_type}</span></td>
                                <td>{formatInterval(w.interval_seconds)}</td>
                                <td>{formatTime(w.last_checked_at)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </>
                )}
              </div>

              {/* ═══════════ ALERTS ═══════════ */}
              <div className="rp-section">
                <h2 className="rp-section-title">4. Watch Alerts</h2>
                <p className="rp-section-desc">
                  Detected changes from watch re-scans. Each alert shows what changed
                  between the previous and most recent scan.
                </p>

                {error ? (
                  <div className="rp-empty" style={{ color: 'var(--accent-red)', borderColor: 'rgba(239,68,68,0.2)' }}>
                    ⚠️ Could not load alert data — {error}
                  </div>
                ) : alerts.length === 0 ? (
                  <div className="rp-empty">No alerts recorded.</div>
                ) : (
                  <table className="rp-table">
                    <thead>
                      <tr>
                        <th>Time</th>
                        <th>Target</th>
                        <th>Plugin</th>
                        <th>Summary</th>
                      </tr>
                    </thead>
                    <tbody>
                      {alerts.slice(0, 50).map(a => (
                        <tr key={a.id}>
                          <td className="rp-nowrap">{formatTime(a.created_at)}</td>
                          <td className="rp-mono">{a.target}</td>
                          <td>{a.plugin_id}</td>
                          <td className="rp-alert-summary">{a.summary}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>

              {/* ═══════════ THREAT EVENTS ═══════════ */}
              <div className="rp-page-break" />
              <div className="rp-section">
                <div className="rp-classification-bar">TOP SECRET // SI // TK // NOFORN</div>
                <h2 className="rp-section-title">5. Threat Intelligence Events</h2>
                <p className="rp-section-desc">
                  Real-time security events, threat intelligence alerts, and news headlines
                  relevant to Indian cybersecurity landscape.
                </p>

                {threatState.tickerEvents.length === 0 ? (
                  <div className="rp-empty">No threat events in current session.</div>
                ) : (
                  <table className="rp-table">
                    <thead>
                      <tr>
                        <th>Time</th>
                        <th>Type</th>
                        <th>Event</th>
                        <th>Source</th>
                        <th>Severity</th>
                      </tr>
                    </thead>
                    <tbody>
                      {threatState.tickerEvents.slice(-50).reverse().map(e => (
                        <tr key={e.id}>
                          <td className="rp-nowrap">{formatTime(e.timestamp)}</td>
                          <td>
                            <span className={`rp-event-type rp-event-${e.type === 'news_event' ? 'news' : 'threat'}`}>
                              {e.type === 'news_event' ? 'NEWS' : 'THREAT'}
                            </span>
                          </td>
                          <td>{e.icon} {e.text}</td>
                          <td>{e.source || '—'}</td>
                          <td><SevBadge severity={e.severity} /></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>

              {/* ═══════════ SCAN RESULTS ═══════════ */}
              <div className="rp-section">
                <h2 className="rp-section-title">6. Recent Scan Results</h2>
                <p className="rp-section-desc">
                  Results from the most recent OSINT scans performed on targets.
                </p>

                {appState.results.length === 0 ? (
                  <div className="rp-empty">No scan data available.</div>
                ) : (
                  <table className="rp-table">
                    <thead>
                      <tr>
                        <th>Plugin</th>
                        <th>Category</th>
                        <th>Target</th>
                        <th>Status</th>
                        <th>Freshness</th>
                        <th>Timestamp</th>
                      </tr>
                    </thead>
                    <tbody>
                      {appState.results.map(r => (
                        <tr key={r.pluginId}>
                          <td><strong>{r.pluginName}</strong></td>
                          <td><span className="rp-cat-badge">{r.category}</span></td>
                          <td className="rp-mono">{r.target}</td>
                          <td>
                            <span className={`rp-status-dot rp-status-${r.status}`} />
                            {r.status.toUpperCase()}
                          </td>
                          <td>{r.freshness}</td>
                          <td className="rp-nowrap">{fmtTimestamp(r.timestamp)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>

              {/* ═══════════ FOOTER ═══════════ */}
              <div className="rp-section">
                <div className="rp-divider" />
                <div className="rp-report-footer">
                  <div className="rp-footer-row">
                    <span>TRINETRA OSINT Platform v1.0</span>
                    <span>Report generated: {now}</span>
                  </div>
                  <div className="rp-footer-row">
                    <span>Data sources: ThreatFox, Feodo Tracker, AlienVault OTX, NVD, NCRB, CERT-In</span>
                  </div>
                  <div className="rp-classification-bar" style={{ marginTop: 12 }}>
                    TOP SECRET // SI // TK // NOFORN
                  </div>
                  <p className="rp-footer-disclaimer">
                    This document contains information exempt from disclosure under applicable law.
                    Unauthorized dissemination is prohibited.
                  </p>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
