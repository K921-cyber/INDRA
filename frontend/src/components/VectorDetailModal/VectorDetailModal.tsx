import React from 'react';
import { AttackVector } from '../../types';

// ==================== VectorLike Type ====================

export type VectorLike = Pick<AttackVector, 'id' | 'from' | 'fromLat' | 'fromLng' | 'to' | 'toLat' | 'toLng' | 'attackType' | 'severity' | 'sourceIp' | 'isp' | 'org' | 'source' | 'malware'> & { modeledTarget?: boolean; note?: string | null };

// ==================== Country Flag Mapping ====================

const COUNTRY_FLAGS: Record<string, string> = {
  'Pakistan': '🇵🇰',
  'China': '🇨🇳',
  'North Korea': '🇰🇵',
  'Russia': '🇷🇺',
  'Iran': '🇮🇷',
  'USA': '🇺🇸',
  'India': '🇮🇳',
  'Unknown': '🏴',
};

// ==================== Vector Detail Modal ====================

export function VectorDetailModal({ vector, onClose }: { vector: VectorLike | null; onClose: () => void }) {
  if (!vector) return null;

  const severityColor = vector.severity === 'critical' ? 'var(--accent-red)' : vector.severity === 'medium' ? 'var(--accent-yellow)' : 'var(--accent-green)';

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      // Fallback for non-HTTPS
      const ta = document.createElement('textarea');
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
    }
  };

  const reportUrls = {
    abuseIpdb: vector.sourceIp ? `https://www.abuseipdb.com/check/${vector.sourceIp}` : '#',
    certIn: 'mailto:incident@cert-in.org.in?subject=' + encodeURIComponent('Cybersecurity Incident Report - Malicious IP ' + (vector.sourceIp || '')) + '&body=' + encodeURIComponent(
      '=== CERT-In Incident Report ===\n' +
      '\n--- Incident Details ---' +
      '\nMalicious IP: ' + (vector.sourceIp || 'N/A') +
      '\nAttack Type: ' + (vector.attackType || 'N/A') +
      '\nSeverity: ' + (vector.severity || 'N/A').toUpperCase() +
      '\nOrigin Country: ' + (vector.from || 'N/A') +
      '\nTarget (India): ' + (vector.to || 'N/A') +
      '\nSource Feed: ' + (vector.source || 'N/A') +
      '\nMalware: ' + (vector.malware || 'N/A') +
      '\nISP: ' + (vector.isp || 'N/A') +
      '\nOrganization: ' + (vector.org || 'N/A') +
      '\nVector ID: ' + (vector.id || 'N/A') +
      '\n\n--- Threat Intelligence Context ---' +
      '\nThis IP was flagged by ' + (vector.source || 'a threat intelligence feed') + ' as participating in ' + (vector.attackType || 'malicious') + ' activity targeting Indian infrastructure.' +
      '\n\n--- Reporter Info ---' +
      '\nReported via: TRINETRA OSINT Intelligence Dashboard' +
      '\n\n(Please attach any additional logs, timestamps, and affected system details)'
    ),
    alienVault: vector.sourceIp ? `https://otx.alienvault.com/indicator/ip/${vector.sourceIp}` : '#',
  };

  return (
    <div className="vector-detail-overlay" onClick={onClose}>
      <div className="vector-detail-modal" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="vd-header">
          <div className="vd-header-left">
            <span className="vd-header-icon">🛡️</span>
            <div>
              <div className="vd-header-title">Attack Vector Details</div>
              <div className="vd-header-id">ID: {vector.id}</div>
            </div>
          </div>
          <button className="vd-close-btn" onClick={onClose}>✕</button>
        </div>

        <div className="vd-body">
          {/* IP Info Card */}
          <div className="vd-card vd-card-ip">
            <div className="vd-card-header">SOURCE IP</div>
            <div className="vd-ip-display">
              <code className="vd-ip-value">{vector.sourceIp || 'N/A'}</code>
              {vector.sourceIp && (
                <button className="vd-copy-btn" onClick={() => copyToClipboard(vector.sourceIp!)} title="Copy IP">
                  📋 Copy
                </button>
              )}
            </div>
            <div className="vd-meta-grid">
              <div className="vd-meta-item">
                <span className="vd-meta-label">ISP</span>
                <span className="vd-meta-value">{vector.isp || 'Unknown'}</span>
              </div>
              <div className="vd-meta-item">
                <span className="vd-meta-label">Organization</span>
                <span className="vd-meta-value">{vector.org || 'N/A'}</span>
              </div>
            </div>
          </div>

          {/* Attack Info Card */}
          <div className="vd-card">
            <div className="vd-card-header">ATTACK ROUTE</div>
            <div className="vd-route-display">
              <div className="vd-route-origin">
                <span className="vd-route-flag">{COUNTRY_FLAGS[vector.from] || '🏴'}</span>
                <div>
                  <div className="vd-route-label">Origin</div>
                  <div className="vd-route-value">{vector.from}</div>
                </div>
              </div>
              <span className="vd-route-arrow">→</span>
              <div className="vd-route-target">
                <div>
                  <div className="vd-route-label">Target</div>
                  <div className="vd-route-value">{vector.to}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Classification Card */}
          <div className="vd-card">
            <div className="vd-card-header">CLASSIFICATION</div>
            <div className="vd-classification-row">
              <div className="vd-class-item">
                <span className="vd-meta-label">Attack Type</span>
                <span className="vd-class-badge type">{vector.attackType}</span>
              </div>
              <div className="vd-class-item">
                <span className="vd-meta-label">Severity</span>
                <span className={`vd-class-badge severity ${vector.severity}`} style={{ background: `${severityColor}18`, color: severityColor, border: `1px solid ${severityColor}30` }}>
                  {vector.severity.toUpperCase()}
                </span>
              </div>
            </div>
            {(vector.malware || vector.source) && (
              <div className="vd-classification-row" style={{ marginTop: 8 }}>
                {vector.malware && (
                  <div className="vd-class-item">
                    <span className="vd-meta-label">Malware</span>
                    <span className="vd-class-badge" style={{ background: 'rgba(249, 115, 22, 0.08)', color: 'var(--accent-orange)', border: '1px solid rgba(249, 115, 22, 0.15)' }}>
                      {vector.malware}
                    </span>
                  </div>
                )}
                {vector.source && (
                  <div className="vd-class-item">
                    <span className="vd-meta-label">Source Feed</span>
                    <span className="vd-class-badge" style={{ background: vector.source === 'ThreatFox' ? 'rgba(139, 92, 246, 0.08)' : vector.source === 'Feodo' ? 'rgba(6, 182, 212, 0.08)' : 'rgba(100, 116, 139, 0.08)', color: vector.source === 'ThreatFox' ? 'var(--accent-purple)' : vector.source === 'Feodo' ? 'var(--accent-cyan)' : 'var(--text-secondary)', border: `1px solid ${vector.source === 'ThreatFox' ? 'rgba(139, 92, 246, 0.15)' : vector.source === 'Feodo' ? 'rgba(6, 182, 212, 0.15)' : 'rgba(100, 116, 139, 0.15)'}` }}>
                      {vector.source}
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Data Transparency Note */}
          <div className="vd-card" style={{ borderLeft: '3px solid var(--accent-yellow)', background: 'rgba(234, 179, 8, 0.02)' }}>
            <div className="vd-card-header">🔍 DATA TRANSPARENCY</div>
            <div style={{ fontSize: 10, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              <div style={{ display:'flex', gap:8, marginBottom:4 }}>
                <span style={{ color:'var(--accent-green)', fontWeight:600 }}>✅ Source IP</span>
                <span style={{ color:'var(--text-muted)' }}>Real (from {vector.source || 'threat feed'})</span>
              </div>
              <div style={{ display:'flex', gap:8, marginBottom:4 }}>
                <span style={{ color:'var(--accent-green)', fontWeight:600 }}>✅ Geo-location</span>
                <span style={{ color:'var(--text-muted)' }}>Real (from ip-api.com)</span>
              </div>
              <div style={{ display:'flex', gap:8, marginBottom:4 }}>
                <span style={{ color:'var(--accent-yellow)', fontWeight:600 }}>⚠️ Target city</span>
                <span style={{ color:'var(--text-muted)' }}>Statistically modeled based on NCRB crime data</span>
              </div>
              {vector.note && (
                <div style={{ display:'flex', gap:8, marginBottom:4 }}>
                  <span style={{ color:'var(--accent-yellow)', fontWeight:600 }}>⚠️ {vector.note.includes('severity') ? 'Severity' : 'Attack type'}</span>
                  <span style={{ color:'var(--text-muted)' }}>{vector.note}</span>
                </div>
              )}
            </div>
          </div>

          {/* Report Actions */}
          <div className="vd-card vd-card-actions">
            <div className="vd-card-header">REPORT THIS THREAT</div>
            <p className="vd-actions-desc">Submit this malicious IP to threat intelligence platforms:</p>
            <div className="vd-actions-grid">
              <a href={reportUrls.abuseIpdb} target="_blank" rel="noopener noreferrer" className={`vd-action-btn ${!vector.sourceIp ? 'disabled' : ''}`}>
                <span className="vd-action-icon">🛡️</span>
                <div className="vd-action-text">
                  <span className="vd-action-name">AbuseIPDB</span>
                  <span className="vd-action-desc">Check IP reputation & report abuse</span>
                </div>
              </a>
              <a href={reportUrls.alienVault} target="_blank" rel="noopener noreferrer" className={`vd-action-btn ${!vector.sourceIp ? 'disabled' : ''}`}>
                <span className="vd-action-icon">👾</span>
                <div className="vd-action-text">
                  <span className="vd-action-name">AlienVault OTX</span>
                  <span className="vd-action-desc">Open Threat Exchange pulse</span>
                </div>
              </a>
              <a href={reportUrls.certIn} className={`vd-action-btn ${!vector.sourceIp ? 'disabled' : ''}`}>
                <span className="vd-action-icon">🇮🇳</span>
                <div className="vd-action-text">
                  <span className="vd-action-name">CERT-In (Email Report)</span>
                  <span className="vd-action-desc">Opens email to incident@cert-in.org.in with pre-filled details</span>
                </div>
              </a>
              <button className="vd-action-btn vd-action-copy" onClick={() => copyToClipboard(JSON.stringify({
                ip: vector.sourceIp,
                country: vector.from,
                attackType: vector.attackType,
                severity: vector.severity,
                target: vector.to,
                isp: vector.isp,
                org: vector.org,
              }, null, 2))}>
                <span className="vd-action-icon">📋</span>
                <div className="vd-action-text">
                  <span className="vd-action-name">Copy JSON Report</span>
                  <span className="vd-action-desc">Raw intelligence data</span>
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
