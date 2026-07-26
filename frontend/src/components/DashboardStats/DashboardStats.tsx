import React, { useState, useEffect } from 'react';
import { useApp } from '../../store/AppContext';
import { useThreatContext } from '../../store/ThreatContext';
import { ShieldIcon, BoltIcon, AlertTriangleIcon, ClockIcon, CheckCircleIcon } from '../Icons/Icons';

export default function DashboardStats() {
  const { state } = useApp();
  const { state: threatState } = useThreatContext();
  const [uptime, setUptime] = useState(0);

  useEffect(() => {
    const start = Date.now();
    const interval = setInterval(() => {
      setUptime(Math.floor((Date.now() - start) / 1000));
    }, 10000);  // Update every 10s instead of 1s to reduce re-renders
    return () => clearInterval(interval);
  }, []);

  const totalAssets = threatState.attackVectors.length;
  const activeThreats = threatState.criticalThreats;
  const totalIncidents = threatState.totalIncidents;
  const completedScans = state.results.filter(r => r.status === 'completed').length;
  const failedScans = state.results.filter(r => r.status === 'failed').length;

  const formatUptime = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h}h ${m}m ${s}s`;
  };

  return (
    <div className="dashboard-stats">
      <div className="stat-card">
        <div className="stat-icon"><ShieldIcon size={14} color="var(--accent-cyan)" /></div>
        <div className="stat-info">
          <div className="stat-value">20</div>
          <div className="stat-label">Plugins</div>
        </div>
      </div>
      <div className="stat-card">
        <div className="stat-icon"><BoltIcon size={14} color="var(--accent-orange)" /></div>
        <div className="stat-info">
          <div className="stat-value">{totalAssets}</div>
          <div className="stat-label">Attack Vectors</div>
        </div>
      </div>
      <div className="stat-card critical">
        <div className="stat-icon" style={{ animation: 'pulse 1.5s infinite' }}><AlertTriangleIcon size={14} color="var(--accent-red)" /></div>
        <div className="stat-info">
          <div className="stat-value">{activeThreats}</div>
          <div className="stat-label">Critical</div>
        </div>
      </div>
      <div className="stat-card">
        <div className="stat-icon"><BoltIcon size={14} color="var(--accent-yellow)" /></div>
        <div className="stat-info">
          <div className="stat-value">{totalIncidents.toLocaleString()}</div>
          <div className="stat-label">Events</div>
        </div>
      </div>
      {state.isSearching && (
        <div className="stat-card scanning">
          <div className="stat-icon" style={{ animation: 'spin 2s linear infinite' }}><BoltIcon size={14} color="var(--accent-blue)" /></div>
          <div className="stat-info">
            <div className="stat-value">{completedScans}/{state.totalPlugins || '...'}</div>
            <div className="stat-label">Progress</div>
          </div>
        </div>
      )}
      {!state.isSearching && completedScans > 0 && (
        <div className="stat-card">
          <div className="stat-icon"><CheckCircleIcon size={14} color="var(--accent-green)" /></div>
          <div className="stat-info">
            <div className="stat-value">{completedScans}{failedScans > 0 && <span className="stat-failed"> +{failedScans}✗</span>}</div>
            <div className="stat-label">Last Scan</div>
          </div>
        </div>
      )}
      <div className="stat-card">
        <div className="stat-icon"><ClockIcon size={14} color="var(--text-muted)" /></div>
        <div className="stat-info">
          <div className="stat-value">{formatUptime(uptime)}</div>
          <div className="stat-label">Uptime</div>
        </div>
      </div>
    </div>
  );
}
