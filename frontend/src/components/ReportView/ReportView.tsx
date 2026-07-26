import React, { useCallback, useMemo, useRef, useState } from 'react';
import { useApp } from '../../store/AppContext';
import { ViewMode } from '../../types';
import { GridIcon, TerminalIcon, ColumnsIcon, CopyIcon, DownloadIcon, ClockIcon, CloseIcon, SearchIcon } from '../Icons/Icons';

export default function ReportView() {
  const { state, dispatch } = useApp();
  const [searchInResults, setSearchInResults] = useState('');
  const reportRef = useRef<HTMLDivElement>(null);

  const activeResult = state.activeToolId
    ? state.results.find(r => r.pluginId === state.activeToolId) ?? null
    : null;

  const allCompleted = state.results.filter(r => r.status === 'completed').length;
  const allFailed = state.results.filter(r => r.status === 'failed').length;

  const activePluginIcon = useMemo(() => {
    if (!state.activeToolId) return null;
    // Find icon from completed results
    const result = state.results.find(r => r.pluginId === state.activeToolId);
    if (result) return { icon: '🔍', name: result.pluginName };
    return null;
  }, [state.activeToolId, state.results]);

  const handleViewModeChange = useCallback((mode: ViewMode) => {
    dispatch({ type: 'SET_VIEW_MODE', payload: mode });
  }, [dispatch]);

  const handleCopy = useCallback(() => {
    if (!activeResult) return;
    const text = state.viewMode === 'terminal' || state.viewMode === 'split'
      ? activeResult.terminalData
      : JSON.stringify(activeResult.guiData, null, 2);
    navigator.clipboard.writeText(text);
  }, [activeResult, state.viewMode]);

  const handleExportTxt = useCallback(() => {
    if (!activeResult) return;
    const header = `TRINETRA OSINT REPORT\n${'='.repeat(50)}\nTool: ${activeResult.pluginName}\nTarget: ${activeResult.target}\nDate: ${new Date().toISOString()}\n${'='.repeat(50)}\n\n`;
    const blob = new Blob([header + activeResult.terminalData], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `trinetra-report-${activeResult.pluginId}-${activeResult.target.replace(/[^a-zA-Z0-9]/g, '_')}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }, [activeResult]);

  const handleExportPdf = useCallback(() => {
    // Generate a print-friendly version for PDF export
    window.print();
  }, []);

  const handleClose = useCallback(() => {
    dispatch({ type: 'SET_ACTIVE_TOOL', payload: null });
  }, [dispatch]);

  // Filter guiData based on search
  const filteredGuiData = useMemo(() => {
    if (!activeResult || !searchInResults.trim()) return activeResult?.guiData || {};
    const term = searchInResults.toLowerCase();
    return Object.fromEntries(
      Object.entries(activeResult.guiData).filter(([key, value]) =>
        key.toLowerCase().includes(term) || String(value).toLowerCase().includes(term)
      )
    );
  }, [activeResult, searchInResults]);

  const freshnessClass = (freshness: string) => `freshness-${freshness}`;

  const formatTimestamp = (ts: string) => {
    const d = new Date(ts);
    return d.toLocaleString('en-IN', { 
      day: 'numeric', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  };

  const renderGuiView = (data: Record<string, any>) => (
    <table className="report-gui-table">
      <tbody>
        {Object.entries(data).length === 0 ? (
          <tr><td colSpan={2} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '24px' }}>No matching results</td></tr>
        ) : (
          Object.entries(data).map(([key, value]) => (
            <tr key={key}>
              <td className="report-gui-key">{key}</td>
              <td className="report-gui-val">{Array.isArray(value) ? value.join(', ') : String(value)}</td>
            </tr>
          ))
        )}
      </tbody>
    </table>
  );

  const renderTerminalView = (data: string) => (
    <pre className="report-terminal">{data}</pre>
  );

  if (!state.activeToolId || !activeResult) return null;

  return (
    <div className="report-overlay">
      <div className="report-document" ref={reportRef}>
        {/* Report Header Bar */}
        <div className="report-toolbar no-print">
          <div className="report-toolbar-left">
            <span className="report-toolbar-icon">{activePluginIcon?.icon || '📊'}</span>
            <div className="report-toolbar-info">
              <span className="report-toolbar-title">{activeResult.pluginName}</span>
              <span className="report-toolbar-target">Target: {activeResult.target}</span>
            </div>
            <span className={`rp-freshness ${freshnessClass(activeResult.freshness)}`}>
              <ClockIcon size={9} /> {activeResult.freshness}
            </span>
          </div>
          <div className="report-toolbar-right">
            <div className="report-view-modes">
              <button
                className={`report-mode-btn ${state.viewMode === 'gui' ? 'active' : ''}`}
                onClick={() => handleViewModeChange('gui')}
              ><GridIcon size={10} /> GUI</button>
              <button
                className={`report-mode-btn ${state.viewMode === 'terminal' ? 'active' : ''}`}
                onClick={() => handleViewModeChange('terminal')}
              ><TerminalIcon size={10} /> Terminal</button>
              <button
                className={`report-mode-btn ${state.viewMode === 'split' ? 'active' : ''}`}
                onClick={() => handleViewModeChange('split')}
              ><ColumnsIcon size={10} /> Split</button>
            </div>
            <div className="report-actions">
              <button className="report-action-btn" onClick={handleCopy} title="Copy to clipboard">
                <CopyIcon size={10} /> Copy
              </button>
              <button className="report-action-btn" onClick={handleExportTxt} title="Export as text file">
                <DownloadIcon size={10} /> .txt
              </button>
              <button className="report-action-btn" onClick={handleExportPdf} title="Print / Save as PDF">
                <DownloadIcon size={10} /> PDF
              </button>
              <button className="report-close-btn" onClick={handleClose} title="Close report">
                <CloseIcon size={12} color="var(--text-muted)" />
              </button>
            </div>
          </div>
        </div>

        {/* Report Body - Professional Document Layout */}
        <div className="report-body">
          {/* Report Header */}
          <div className="report-header-section">
            <div className="report-header-badge">OSINT Intelligence Report</div>
            <h1 className="report-title">
              <span className="report-title-icon">{activePluginIcon?.icon || '🔍'}</span>
              {activeResult.pluginName}
            </h1>
            <div className="report-meta-grid">
              <div className="report-meta-item">
                <span className="report-meta-label">Target</span>
                <span className="report-meta-value">{activeResult.target}</span>
              </div>
              <div className="report-meta-item">
                <span className="report-meta-label">Tool</span>
                <span className="report-meta-value">{activeResult.pluginName}</span>
              </div>
              <div className="report-meta-item">
                <span className="report-meta-label">Category</span>
                <span className="report-meta-value report-cat-badge">{activeResult.category}</span>
              </div>
              <div className="report-meta-item">
                <span className="report-meta-label">Timestamp</span>
                <span className="report-meta-value">{formatTimestamp(activeResult.timestamp)}</span>
              </div>
              <div className="report-meta-item">
                <span className="report-meta-label">Freshness</span>
                <span className="report-meta-value">{activeResult.freshness}</span>
              </div>
              <div className="report-meta-item">
                <span className="report-meta-label">Status</span>
                <span className={`report-meta-value report-status-${activeResult.status}`}>
                  {activeResult.status.toUpperCase()}
                </span>
              </div>
            </div>
          </div>

          {/* Divider */}
          <div className="report-divider" />

          {/* Search within results */}
          <div className="report-search no-print">
            <SearchIcon size={11} color="var(--text-muted)" />
            <input
              id="report-search-input"
              className="report-search-input"
              type="text"
              placeholder="Search within results..."
              value={searchInResults}
              onChange={e => setSearchInResults(e.target.value)}
            />
            {searchInResults && (
              <button className="report-search-clear" onClick={() => setSearchInResults('')}>
                <CloseIcon size={8} color="var(--text-muted)" />
              </button>
            )}
          </div>

          {/* Results Content */}
          <div className="report-content">
            {/* Classification bar */}
            <div className="report-classification">UNCLASSIFIED // FOR AUTHORIZED USE ONLY</div>

            {state.viewMode === 'gui' && (
              <div className="report-section">
                <div className="report-section-title">
                  <span className="report-section-icon">📊</span>
                  Structured Data
                </div>
                <div className="report-section-body">
                  {renderGuiView(filteredGuiData)}
                </div>
              </div>
            )}

            {state.viewMode === 'terminal' && (
              <div className="report-section">
                <div className="report-section-title">
                  <span className="report-section-icon">💻</span>
                  Raw Output
                </div>
                <div className="report-section-body">
                  {renderTerminalView(activeResult.terminalData)}
                </div>
              </div>
            )}

            {state.viewMode === 'split' && (
              <>
                <div className="report-section">
                  <div className="report-section-title">
                    <span className="report-section-icon">📊</span>
                    Structured Data
                  </div>
                  <div className="report-section-body">
                    {renderGuiView(filteredGuiData)}
                  </div>
                </div>
                <div className="report-section" style={{ marginTop: 16 }}>
                  <div className="report-section-title">
                    <span className="report-section-icon">💻</span>
                    Raw Output
                  </div>
                  <div className="report-section-body">
                    {renderTerminalView(activeResult.terminalData)}
                  </div>
                </div>
              </>
            )}

            {/* Footer */}
            <div className="report-footer">
              <div className="report-divider" />
              <div className="report-footer-text">
                <span>TRINETRA OSINT Platform • Report generated {new Date().toLocaleString()}</span>
                <span>Target: {activeResult.target}</span>
              </div>
              <div className="report-classification" style={{ marginTop: 8 }}>UNCLASSIFIED // FOR AUTHORIZED USE ONLY</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
