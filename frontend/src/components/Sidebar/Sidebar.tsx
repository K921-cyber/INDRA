import React, { useState, useEffect, useCallback } from 'react';
import { useApp } from '../../store/AppContext';
import { ToolPlugin, ToolCategory } from '../../types';
import { GlobeIcon, AlertTriangleIcon, CrosshairIcon, ChevronRightIcon, ChevronDownIcon } from '../Icons/Icons';
import { api } from '../../utils/api';



const CATEGORY_ORDER: ToolCategory[] = ['infrastructure', 'threat', 'advanced'];

const CATEGORY_LABELS: Record<ToolCategory, string> = {
  infrastructure: 'Infrastructure',
  threat: 'Threat Intel',
  advanced: 'Advanced Scan',
};

const CATEGORY_ICONS: Record<ToolCategory, React.ReactNode> = {
  infrastructure: <GlobeIcon size={13} />,
  threat: <AlertTriangleIcon size={13} />,
  advanced: <CrosshairIcon size={13} />,
};

export default function Sidebar() {
  const { state, dispatch } = useApp();
  const [collapsedCategories, setCollapsedCategories] = useState<Set<string>>(new Set());
  const [plugins, setPlugins] = useState<ToolPlugin[]>([]);
  const [loadingPlugins, setLoadingPlugins] = useState(true);

  // Fetch real plugin list from backend (uses auth headers via api module)
  useEffect(() => {
    api.listPlugins()
      .then(data => {
        if (data.plugins) {
          const mapped: ToolPlugin[] = data.plugins.map((p: any) => ({
            id: p.id,
            name: p.name,
            description: p.description || '',
            category: p.category as ToolCategory,
            icon: p.icon || '🔌',
            inputTypes: p.input_types || [],
            enabled: true,
          }));
          setPlugins(mapped);
        }
      })
      .catch(() => {
        // Backend not available — empty list
        setPlugins([]);
      })
      .finally(() => setLoadingPlugins(false));
  }, []);

  const toggleCategory = (cat: string) => {
    setCollapsedCategories(prev => {
      const next = new Set(prev);
      if (next.has(cat)) next.delete(cat);
      else next.add(cat);
      return next;
    });
  };

  const handleToolClick = (pluginId: string) => {
    dispatch({ type: 'SET_ACTIVE_TOOL', payload: pluginId === state.activeToolId ? null : pluginId });
  };

  const getToolStatus = (pluginId: string): 'completed' | 'running' | 'failed' | 'pending' => {
    const result = state.results.find(r => r.pluginId === pluginId);
    if (result) {
      if (result.status === 'completed') return 'completed';
      if (result.status === 'running') return 'running';
      return 'failed';
    }
    return 'pending';
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        OSINT Tools ({state.results.length}/{plugins.length || '…'})
      </div>
      <div className="sidebar-categories">
        {loadingPlugins ? (
          <div className="sidebar-loading">Loading plugins...</div>
        ) : (
          CATEGORY_ORDER.map(cat => {
          const toolsInCat = plugins.filter(t => t.category === cat);
          const completedInCat = state.results.filter(r => r.category === cat).length;
          const isCollapsed = collapsedCategories.has(cat);

          return (
            <div key={cat} className="category-group">
              <div className="category-header" onClick={() => toggleCategory(cat)}>
                <span className="category-icon">
                  {isCollapsed ? <ChevronRightIcon size={10} /> : <ChevronDownIcon size={10} />}
                </span>
                {CATEGORY_ICONS[cat]}
                <span>{CATEGORY_LABELS[cat]}</span>
                <span className="category-count">{completedInCat}/{toolsInCat.length}</span>
              </div>
              {!isCollapsed && (
                <div className="tool-list">
                  {toolsInCat.map(tool => {
                    const status = getToolStatus(tool.id);
                    const isActive = state.activeToolId === tool.id;
                    return (
                      <button
                        key={tool.id}
                        className={`tool-item ${isActive ? 'active' : ''}`}
                        onClick={() => handleToolClick(tool.id)}
                        title={tool.description}
                      >
                        <span className="tool-icon">
                          {tool.icon}
                        </span>
                        <span className="tool-name">{tool.name}</span>
                        <span className={`tool-status ${status}`} />
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          );
        }))}
      </div>
    </div>
  );
}
