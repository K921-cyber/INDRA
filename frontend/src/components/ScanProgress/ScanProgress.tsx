import React from 'react';
import { useApp } from '../../store/AppContext';
import { ToolCategory } from '../../types';

export default function ScanProgress() {
  const { state } = useApp();

  if (!state.isSearching && state.results.length === 0) return null;

  const completedCount = state.results.filter(r => r.status === 'completed').length;
  const failedCount = state.results.filter(r => r.status === 'failed').length;
  const total = state.totalPlugins || state.results.length || 1;
  const progress = total > 0 ? ((completedCount + failedCount) / total) * 100 : 0;

  // Category breakdown from actual results
  const categories: ToolCategory[] = ['infrastructure', 'threat', 'advanced'];
  const categoryLabels: Record<string, string> = {
    infrastructure: '🌐',
    threat: '🚨',
    advanced: '🔍',
  };

  return (
    <div className="scan-progress">
      <div className="scan-progress-header">
        <span className="scan-progress-title">
          {state.isSearching ? '⚡ Scanning...' : '✅ Scan Complete'}
        </span>
        <span className="scan-progress-count">
          {completedCount + failedCount}/{total}
        </span>
      </div>
      <div className="scan-progress-bar-track">
        <div
          className="scan-progress-bar-fill"
          style={{ width: `${progress}%` }}
        />
      </div>
      <div className="scan-categories">
        {categories.map(cat => {
          const resultsInCat = state.results.filter(r => r.category === cat);
          const completedInCat = resultsInCat.filter(r => r.status === 'completed').length;
          const failedInCat = resultsInCat.filter(r => r.status === 'failed').length;
          const totalInCat = resultsInCat.length || 1;
          const catProgress = totalInCat > 0 ? ((completedInCat + failedInCat) / totalInCat) * 100 : 0;

          return (
            <div key={cat} className="scan-category-item">
              <span className="scan-cat-icon">{categoryLabels[cat]}</span>
              <div className="scan-cat-bar-track">
                <div
                  className={`scan-cat-bar-fill ${catProgress === 100 ? 'done' : catProgress > 0 ? 'active' : ''}`}
                  style={{ width: `${catProgress}%` }}
                />
              </div>
              <span className="scan-cat-count">{completedInCat + failedInCat}/{totalInCat}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
