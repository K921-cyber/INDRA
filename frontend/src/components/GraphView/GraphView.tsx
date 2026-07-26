import React, { useEffect, useRef, useMemo } from 'react';
import cytoscape, { Core } from 'cytoscape';
// @ts-ignore - cytoscape-dagre has no bundled type declarations
import dagre from 'cytoscape-dagre';
import { useApp } from '../../store/AppContext';
import { ToolResult, GraphNode, GraphEdge, GraphNodeType } from '../../types';
import { DownloadIcon, CloseIcon, GraphIcon, SearchIcon } from '../Icons/Icons';
import EmptyState from '../EmptyState/EmptyState';

cytoscape.use(dagre);

// Debounce graph rebuilds during scan to avoid destroying cytoscape 19+ times
const DEBOUNCE_MS = 600;

const nodeColors: Record<string, string> = {
  target: '#3b82f6',
  ip: '#8b5cf6',
  dns: '#06b6d4',
  geo: '#22c55e',
  port: '#eab308',
  cve: '#ef4444',
  email: '#ec4899',
  domain: '#f97316',
  infrastructure: '#06b6d4',
  threat: '#ef4444',
  advanced: '#8b5cf6',
};

const styles: any[] = [
  {
    selector: 'node',
    style: {
      'label': 'data(label)',
      'text-valign': 'center',
      'text-halign': 'center',
      'color': '#e8eaf0',
      'font-size': '10px',
      'text-wrap': 'wrap',
      'text-max-width': '80px',
      'background-color': '#1a1f2e',
      'border-width': 2,
      'border-color': '#3b82f6',
      'width': 60,
      'height': 60,
      'shape': 'ellipse',
      'transition-property': 'background-color, border-color, width, height',
      'transition-duration': '0.3s',
    },
  },
  {
    selector: 'node[type="target"]',
    style: {
      'background-color': nodeColors.target,
      'width': 90,
      'height': 90,
      'font-size': '12px',
      'font-weight': 'bold',
      'border-width': 3,
      'border-color': '#60a5fa',
    },
  },
  {
    selector: 'node[type="ip"]',
    style: { 'background-color': nodeColors.ip, 'border-color': '#a78bfa', 'shape': 'diamond' },
  },
  {
    selector: 'node[type="dns"]',
    style: { 'background-color': nodeColors.dns, 'border-color': '#22d3ee', 'shape': 'round-rectangle' },
  },
  {
    selector: 'node[type="geo"]',
    style: { 'background-color': nodeColors.geo, 'border-color': '#4ade80' },
  },
  {
    selector: 'node[type="port"]',
    style: { 'background-color': nodeColors.port, 'border-color': '#facc15', 'shape': 'hexagon' },
  },
  {
    selector: 'node[type="cve"]',
    style: { 'background-color': nodeColors.cve, 'border-color': '#f87171', 'width': 80, 'height': 50, 'shape': 'round-rectangle' },
  },
  {
    selector: 'node[type="email"]',
    style: { 'background-color': nodeColors.email, 'border-color': '#f472b6', 'shape': 'round-rectangle' },
  },
  {
    selector: 'node[type="domain"]',
    style: { 'background-color': nodeColors.domain, 'border-color': '#fb923c', 'shape': 'round-rectangle' },
  },
  {
    selector: 'node[type="infrastructure"]',
    style: { 'background-color': nodeColors.infrastructure, 'border-color': '#22d3ee', 'shape': 'round-rectangle', 'width': 70, 'height': 35 },
  },
  {
    selector: 'node[type="threat"]',
    style: { 'background-color': nodeColors.threat, 'border-color': '#f87171', 'shape': 'round-rectangle', 'width': 70, 'height': 35 },
  },
  {
    selector: 'node[type="advanced"]',
    style: { 'background-color': nodeColors.advanced, 'border-color': '#a78bfa', 'shape': 'round-rectangle', 'width': 70, 'height': 35 },
  },
  {
    selector: 'edge',
    style: {
      'width': 1.5,
      'line-color': '#3a4050',
      'target-arrow-color': '#3a4050',
      'target-arrow-shape': 'triangle',
      'curve-style': 'bezier',
      'label': 'data(label)',
      'font-size': '8px',
      'color': '#64748b',
      'text-rotation': 'autorotate',
    },
  },
  {
    selector: 'edge:selected',
    style: {
      'line-color': '#3b82f6',
      'target-arrow-color': '#3b82f6',
      'width': 2.5,
    },
  },
  // Highlight edges on node hover
  {
    selector: 'node:selected',
    style: {
      'border-width': 4,
      'border-color': '#60a5fa',
    },
  },
];

// ==================== Dynamic Graph Builder ====================

let nodeIdCounter = 0;

function makeNodeId(): string {
  return `n_${nodeIdCounter++}`;
}

/**
 * Build a dynamic graph from the actual search results.
 * Each completed result becomes a category node connected to the target,
 * and key findings from guiData become detail nodes.
 */
function buildGraphFromResults(searchQuery: string, results: ToolResult[]): { nodes: GraphNode[]; edges: GraphEdge[] } {
  nodeIdCounter = 0;

  if (results.length === 0) {
    // No results yet — return empty graph
    return { nodes: [], edges: [] };
  }

  const nodes: GraphNode[] = [];
  const edges: GraphEdge[] = [];
  const seen = new Set<string>();

  // Target node (the search query)
  const targetId = 'target';
  nodes.push({ id: targetId, label: searchQuery, type: 'target' });

  // Group results by category
  const categories = ['infrastructure', 'threat', 'advanced'] as const;
  const categoryLabels: Record<string, string> = {
    infrastructure: 'Infrastructure',
    threat: 'Threat Intel',
    advanced: 'Advanced',
  };

  for (const cat of categories) {
    const catResults = results.filter(r => r.category === cat && r.status === 'completed');
    if (catResults.length === 0) continue;

    // Category group node
    const catNodeId = `cat_${cat}`;
    nodes.push({ id: catNodeId, label: categoryLabels[cat], type: cat });
    edges.push({ id: `e_target_${cat}`, source: targetId, target: catNodeId, label: catResults.length + ' tools' });

    for (const result of catResults) {
      // Plugin result node
      const pluginNodeId = makeNodeId();
      const shortLabel = result.pluginName.length > 16
        ? result.pluginName.substring(0, 14) + '…'
        : result.pluginName;
      nodes.push({ id: pluginNodeId, label: shortLabel, type: result.category });
      edges.push({ id: `e_${catNodeId}_${pluginNodeId}`, source: catNodeId, target: pluginNodeId, label: '' });

      // Extract key findings from guiData (max 3 per result to keep graph readable)
      const entries = Object.entries(result.guiData).slice(0, 3);
      for (const [key, value] of entries) {
        const valStr = Array.isArray(value) ? value[0] : String(value);
        // Only add interesting values (skip empty/dash values)
        if (!valStr || valStr === '—' || valStr === 'None' || valStr.length > 40) continue;

        const dedupKey = `${key}:${valStr}`.toLowerCase();
        if (seen.has(dedupKey)) continue;
        seen.add(dedupKey);

        // Determine node type from the value content
        let nodeType: GraphNodeType = result.category;
        if (/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(valStr)) nodeType = 'ip';
        else if (/\.gov|\.com|\.org|\.in|\.net/i.test(valStr) && valStr.includes('.')) {
          if (key.toLowerCase().includes('subdomain') || key.includes('.')) nodeType = 'domain';
          else if (key.toLowerCase().includes('ns') || key.toLowerCase().includes('name server')) nodeType = 'dns';
          else nodeType = 'domain';
        }
        else if (/@/.test(valStr)) nodeType = 'email';
        else if (/CVE-\d+/i.test(key) || /CVE-\d+/i.test(valStr)) nodeType = 'cve';
        else if (/port|tcp|udp/i.test(key)) nodeType = 'port';
        else if (/country|city|location|lat|lon/i.test(key)) nodeType = 'geo';

        const detailNodeId = makeNodeId();
        const detailLabel = valStr.length > 18 ? valStr.substring(0, 16) + '…' : valStr;
        nodes.push({ id: detailNodeId, label: detailLabel, type: nodeType });
        edges.push({ id: `e_${pluginNodeId}_${detailNodeId}`, source: pluginNodeId, target: detailNodeId, label: key.length > 12 ? key.substring(0, 10) + '…' : key });
      }
    }
  }

  return { nodes, edges };
}

// ==================== Fallback: static graph for when no results ====================

function getGraphData(searchQuery: string, results: ToolResult[]): { nodes: GraphNode[]; edges: GraphEdge[] } {
  const dynamic = buildGraphFromResults(searchQuery, results);

  // If no results yet, show a placeholder graph centered on the query
  if (dynamic.nodes.length <= 1) {
    return {
      nodes: [
        { id: 'target', label: searchQuery || 'Search a target', type: 'target' },
      ],
      edges: [],
    };
  }

  return dynamic;
}

// ==================== Component ====================

export default function GraphView() {
  const { state, dispatch } = useApp();
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);

  const graphData = useMemo(
    () => getGraphData(state.searchQuery, state.results),
    [state.searchQuery, state.results]
  );

  const noSearchYet = !state.searchQuery && state.results.length === 0;

  const handleGoToSearch = () => {
    dispatch({ type: 'TOGGLE_GRAPH_VIEW' });
    dispatch({ type: 'SET_ACTIVE_TAB', payload: 'search' });
    setTimeout(() => document.getElementById('search-input')?.focus(), 0);
  };

  useEffect(() => {
    if (!containerRef.current || !state.showGraphView) return;

    const timer = setTimeout(() => {
      if (cyRef.current) {
        cyRef.current.destroy();
      }

      const cy = cytoscape({
      container: containerRef.current,
      elements: [
        ...graphData.nodes.map(n => ({
          data: { id: n.id, label: n.label, type: n.type, ...n.data },
        })),
        ...graphData.edges.map(e => ({
          data: { id: e.id, source: e.source, target: e.target, label: e.label },
        })),
      ],
      style: styles,
      layout: {
        name: 'dagre',
        // @ts-ignore - dagre-specific layout options
        rankDir: 'TB',
        nodeSep: 45,
        rankSep: 90,
        edgeSep: 20,
        animate: true,
        animationDuration: 400,
        fit: true,
        padding: 40,
      },
      minZoom: 0.05,
      maxZoom: 3,
      userZoomingEnabled: true,
      userPanningEnabled: true,
    });

    cyRef.current = cy;

    // Always fit the whole graph into view once layout settles,
    // so the user never opens the modal needing to manually zoom out.
    cy.on('layoutstop', () => {
      cy.fit(undefined, 40);
    });

    // Click handler for nodes
    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      const type = node.data('type');
      if (type === 'target') {
        // Could open domain record
      }
    });

      cyRef.current = cy;
    }, DEBOUNCE_MS);

    return () => {
      clearTimeout(timer);
      if (cyRef.current) {
        cyRef.current.destroy();
        cyRef.current = null;
      }
    };
  }, [state.showGraphView, graphData]);

  const handleExportPNG = () => {
    if (cyRef.current) {
      const blob = cyRef.current.png({ output: 'blob', scale: 2, bg: '#0a0e1a' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `trinetra-graph-${state.searchQuery || 'untitled'}.png`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  const handleExportSVG = async () => {
    if (cyRef.current) {
      const text = `TRINETRA Graph Export — ${state.searchQuery}\n\nNodes: ${graphData.nodes.length}\nEdges: ${graphData.edges.length}\nGenerated: ${new Date().toISOString()}`;
      await navigator.clipboard.writeText(text);
    }
  };

  if (!state.showGraphView) return null;

  return (
    <div className="graph-overlay">
      <div className="graph-header">
        <h2>
          <span style={{ fontSize: '16px' }}>🧠</span>
          Relationship Graph — {state.searchQuery || 'No target'}
          <span style={{ fontSize: '11px', fontWeight: 400, color: 'var(--text-muted)', marginLeft: 8 }}>
            {graphData.nodes.length} nodes · {graphData.edges.length} edges
          </span>
        </h2>
        <div className="graph-controls">
          <button
            className="result-action-btn"
            onClick={() => cyRef.current?.fit(undefined, 40)}
          >
            <GraphIcon size={10} /> Fit to Screen
          </button>
          <button className="result-action-btn" onClick={handleExportPNG}>
            <DownloadIcon size={10} /> Export PNG
          </button>
          <button className="result-action-btn" onClick={handleExportSVG}>
            <DownloadIcon size={10} /> Copy Info
          </button>
          <button
            className="result-action-btn"
            style={{ background: 'rgba(239,68,68,0.15)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.3)' }}
            onClick={() => dispatch({ type: 'TOGGLE_GRAPH_VIEW' })}
          >
            <CloseIcon size={12} color="#ef4444" /> Close
          </button>
        </div>
      </div>
      {noSearchYet ? (
        <EmptyState
          icon={<GraphIcon size={44} color="var(--text-muted)" />}
          title="No graph yet"
          message="Run a search on a domain, IP, email, or phone number and TRINETRA will map the relationships between findings here."
          ctaLabel="Run a search"
          ctaIcon={<SearchIcon size={13} />}
          onCta={handleGoToSearch}
        />
      ) : (
        <>
          <div ref={containerRef} className="graph-container" />

          <div className="graph-legend-overlay">
            <div className="graph-legend-item">
              <div className="graph-legend-color" style={{ background: '#3b82f6' }} /> Target
            </div>
            <div className="graph-legend-item">
              <div className="graph-legend-color" style={{ background: '#06b6d4' }} /> Infrastructure
            </div>
            <div className="graph-legend-item">
              <div className="graph-legend-color" style={{ background: '#ef4444' }} /> Threat
            </div>
            <div className="graph-legend-item">
              <div className="graph-legend-color" style={{ background: '#8b5cf6' }} /> Advanced
            </div>
            <div className="graph-legend-item">
              <div className="graph-legend-color" style={{ background: '#f97316' }} /> Domain
            </div>
            <div className="graph-legend-item">
              <div className="graph-legend-color" style={{ background: '#22c55e' }} /> Geo
            </div>
          </div>
        </>
      )}
    </div>
  );
}