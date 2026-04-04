import { useCallback, useRef, useEffect, useMemo } from 'react';
import ForceGraph2D, { type ForceGraphMethods } from 'react-force-graph-2d';
import type { GraphNode, GraphEdge, HighlightState } from '@/lib/types';

interface Props {
  nodes: GraphNode[];
  links: GraphEdge[];
  highlight: HighlightState;
  onNodeClick: (node: GraphNode) => void;
  onLinkClick: (link: GraphEdge) => void;
  selectedNode?: GraphNode | null;
  selectedEdge?: GraphEdge | null;
  isDark: boolean;
}

const NODE_COLORS: Record<string, string> = {
  internet: '#22c55e',
  ingress: '#3b82f6',
  pod: '#6366f1',
  service: '#8b5cf6',
  serviceaccount: '#06b6d4',
  rolebinding: '#f59e0b',
  role: '#f59e0b',
  clusterrole: '#ef4444',
  secret: '#eab308',
  database: '#eab308',
  configmap: '#64748b',
  networkpolicy: '#64748b',
  namespace: '#94a3b8',
};

const RISK_COLORS: Record<string, string> = {
  'crown-jewel': '#eab308',   // Yellow (Crown Jewel)
  'critical': '#ef4444',     // Red (Critical Risk)
  'high': '#f97316',         // Orange
  'medium': '#f59e0b',       // Amber
  'low': '#64748b',          // Slate/Grey (Low Risk / Utility)
  'entry-point': '#22c55e',  // Green (Internet / Entry Point)
  'info': '#6366f1',         // Indigo (Standard Entity)
};

const NODE_ICONS: Record<string, string> = {
  internet: '🌐',
  ingress: '🔀',
  pod: '📦',
  service: '🔌',
  serviceaccount: '👤',
  rolebinding: '🔗',
  role: '🛡️',
  clusterrole: '⚔️',
  secret: '🔑',
  database: '🗄️',
  configmap: '📋',
  networkpolicy: '🚧',
};

export default function GraphCanvas({ nodes, links, highlight, onNodeClick, onLinkClick, selectedNode, selectedEdge, isDark }: Props) {
  const fgRef = useRef<ForceGraphMethods | null>(null);

  const graphData = useMemo(() => {
    return {
      nodes: nodes.map(n => ({ ...n })),
      links: links.map(l => ({ ...l })),
    };
  }, [nodes, links]);

  // Tune layout forces
  useEffect(() => {
    const fg = fgRef.current;
    if (fg) {
      // Increase negative charge so nodes repel each other horizontally
      fg.d3Force('charge')?.strength(-400);
      // Let the link distances be flexible
      fg.d3Force('link')?.distance(60);
      
      (fg as any).d3ReheatSimulation?.();
    }
  }, [graphData]);

  const getNodeColor = useCallback((node: GraphNode) => {
    if (highlight.nodes.size > 0) {
      if (highlight.nodes.has(node.id)) {
        if (highlight.path.includes(node.id)) {
          return '#ef4444';
        }
        return RISK_COLORS[node.risk_level] || NODE_COLORS[node.type] || '#6366f1';
      }
      return isDark ? '#1e293b' : '#cbd5e1';
    }
    return RISK_COLORS[node.risk_level] || NODE_COLORS[node.type] || '#6366f1';
  }, [highlight, isDark]);

  const getNodeSize = useCallback((node: GraphNode) => {
    const baseSize = node.type === 'internet' ? 10 :
      node.risk_level === 'crown-jewel' ? 9 :
        node.risk_level === 'critical' ? 8 :
          node.type === 'pod' ? 7 : 6;

    if (highlight.nodes.size > 0 && highlight.nodes.has(node.id)) {
      return baseSize * 1.4;
    }
    if (highlight.nodes.size > 0 && !highlight.nodes.has(node.id)) {
      return baseSize * 0.6;
    }
    return baseSize;
  }, [highlight]);

  const paintNode = useCallback((node: GraphNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const size = getNodeSize(node);
    const color = getNodeColor(node);
    const x = node.x ?? 0;
    const y = node.y ?? 0;
    const isHighlighted = highlight.nodes.size === 0 || highlight.nodes.has(node.id);
    const isOnPath = highlight.path.includes(node.id);
    const isSelected = selectedNode?.id === node.id;
    const isLinkSelected = selectedEdge && (
      (typeof selectedEdge.source === 'string' ? selectedEdge.source : (selectedEdge.source as any).id) === node.id ||
      (typeof selectedEdge.target === 'string' ? selectedEdge.target : (selectedEdge.target as any).id) === node.id
    );
    const isGroupGlow = 
      (highlight.mode === 'group-critical' && node.risk_level === 'critical') || 
      (highlight.mode === 'group-crown-jewel' && node.risk_level === 'crown-jewel') ||
      (highlight.mode === 'group-entry-point' && (node.type === 'internet' || node.risk_level === 'entry-point')) ||
      (highlight.mode === 'group-standard' && (node.risk_level === 'info' || node.risk_level === 'medium' || node.type === 'pod' || node.type === 'service')) ||
      (highlight.mode === 'group-low' && node.risk_level === 'low');

    // Draw native-colored glowing halo for selected node or filtered group
    if (isSelected || isGroupGlow || isLinkSelected) {
      ctx.beginPath();
      ctx.arc(x, y, size + (isSelected || isGroupGlow ? 6 : 4), 0, 2 * Math.PI);
      
      // Use standard transparent base mapping matching the node's true color natively!
      ctx.globalAlpha = isDark ? (isLinkSelected && !isSelected ? 0.2 : 0.35) : (isLinkSelected && !isSelected ? 0.15 : 0.25);
      ctx.fillStyle = color;
      ctx.fill();
      ctx.globalAlpha = 1.0;
      
      // Add glowing shadow effect tied to the node's specific color
      if (isSelected || isGroupGlow) {
        ctx.shadowColor = color;
        ctx.shadowBlur = 20;
      }
      
      // Apply exact border
      ctx.strokeStyle = color;
      ctx.lineWidth = isSelected ? 2 : 1;
      ctx.stroke();
      
      // Reset shadow so it doesn't affect other elements
      ctx.shadowBlur = 0;
    }

    // Outer faint glow for generic highlighted nodes
    if (isHighlighted && (node.risk_level === 'critical' || node.risk_level === 'crown-jewel' || isOnPath)) {
      const glowSize = size + 4;
      const gradient = ctx.createRadialGradient(x, y, size * 0.5, x, y, glowSize);
      gradient.addColorStop(0, color + '60');
      gradient.addColorStop(1, color + '00');
      ctx.beginPath();
      ctx.arc(x, y, glowSize, 0, 2 * Math.PI);
      ctx.fillStyle = gradient;
      ctx.fill();
    }

    // Main node circle
    ctx.beginPath();
    ctx.arc(x, y, size, 0, 2 * Math.PI);
    ctx.fillStyle = isHighlighted ? color : (isDark ? '#1e293b' : '#e2e8f0');
    ctx.fill();

    // Border
    ctx.strokeStyle = isHighlighted ? color : (isDark ? '#334155' : '#94a3b8');
    ctx.lineWidth = isOnPath ? 2 : 1;
    ctx.stroke();

    // Icon (if zoomed in enough)
    if (globalScale > 0.8) {
      const icon = NODE_ICONS[node.type] || '⚪';
      ctx.font = `${Math.max(size * 0.9, 6)}px Arial`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(icon, x, y);
    }

    // Label (if zoomed in)
    if (globalScale > 1.2) {
      ctx.font = `${Math.max(11 / globalScale, 3)}px Inter, sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillStyle = isHighlighted
        ? (isDark ? '#f1f5f9' : '#1e293b')
        : (isDark ? '#475569' : '#94a3b8');
      ctx.fillText(node.label || node.id, x, y + size + 3);
    }
  }, [getNodeColor, getNodeSize, highlight, isDark, selectedNode, selectedEdge]);

  const getLinkColor = useCallback((link: { source: GraphNode | string; target: GraphNode | string }) => {
    const sourceId = typeof link.source === 'string' ? link.source : (link.source as any).id;
    const targetId = typeof link.target === 'string' ? link.target : (link.target as any).id;
    const edgeKey = `${sourceId}->${targetId}`;

    const isSelected = selectedEdge && (
      (typeof selectedEdge.source === 'string' ? selectedEdge.source : (selectedEdge.source as any).id) === sourceId &&
      (typeof selectedEdge.target === 'string' ? selectedEdge.target : (selectedEdge.target as any).id) === targetId
    );

    if (isSelected) return '#ef4444';

    if (highlight.edges.size > 0 && highlight.edges.has(edgeKey)) {
      return '#ef4444';
    }
    if (highlight.nodes.size > 0) {
      if (highlight.nodes.has(sourceId) && highlight.nodes.has(targetId)) {
        return isDark ? 'rgba(99,102,241,0.8)' : 'rgba(99,102,241,0.7)';
      }
      return isDark ? 'rgba(15,23,42,0.6)' : 'rgba(203,213,225,0.4)';
    }
    // High contrast professional lines (slate-400 equivalent for dark, slate-600 equivalent for light)
    return isDark ? 'rgba(148,163,184,0.75)' : 'rgba(71,85,105,0.8)';
  }, [highlight, isDark, selectedEdge]);

  const getLinkWidth = useCallback((link: { source: GraphNode | string; target: GraphNode | string }) => {
    const sourceId = typeof link.source === 'string' ? link.source : (link.source as any).id;
    const targetId = typeof link.target === 'string' ? link.target : (link.target as any).id;
    const edgeKey = `${sourceId}->${targetId}`;

    const isSelected = selectedEdge && (
      (typeof selectedEdge.source === 'string' ? selectedEdge.source : (selectedEdge.source as any).id) === sourceId &&
      (typeof selectedEdge.target === 'string' ? selectedEdge.target : (selectedEdge.target as any).id) === targetId
    );

    if (isSelected) return 4;

    if (highlight.edges.size > 0 && highlight.edges.has(edgeKey)) {
      return 3;
    }
    return 1;
  }, [highlight, selectedEdge]);

  const handleNodeClick = useCallback((node: GraphNode) => {
    onNodeClick(node);
    const fg = fgRef.current;
    if (fg) {
      fg.centerAt(node.x, node.y, 600);
      fg.zoom(2.5, 600);
    }
  }, [onNodeClick]);

  const handleLinkClick = useCallback((link: any) => {
    onLinkClick(link as GraphEdge);
  }, [onLinkClick]);

  return (
    <div className="graph-container relative w-full h-full">
      <ForceGraph2D
        ref={fgRef as any}
        graphData={graphData}
        nodeCanvasObject={paintNode as any}
        nodePointerAreaPaint={(node: any, color: string, ctx: CanvasRenderingContext2D) => {
          const size = getNodeSize(node);
          ctx.beginPath();
          ctx.arc(node.x ?? 0, node.y ?? 0, size + 2, 0, 2 * Math.PI);
          ctx.fillStyle = color;
          ctx.fill();
        }}
        dagMode="td"
        dagLevelDistance={120}
        d3VelocityDecay={0.3}
        linkColor={getLinkColor as any}
        linkWidth={getLinkWidth as any}
        linkDirectionalArrowLength={4}
        linkDirectionalArrowRelPos={0.85}
        linkDirectionalParticles={(link: any) => {
          const sourceId = typeof link.source === 'string' ? link.source : (link.source as any).id;
          const targetId = typeof link.target === 'string' ? link.target : (link.target as any).id;
          const edgeKey = `${sourceId}->${targetId}`;

          const isSelected = selectedEdge && (
            (typeof selectedEdge.source === 'string' ? selectedEdge.source : (selectedEdge.source as any).id) === sourceId &&
            (typeof selectedEdge.target === 'string' ? selectedEdge.target : (selectedEdge.target as any).id) === targetId
          );

          return (highlight.edges.has(edgeKey) || isSelected) ? 3 : 0;
        }}
        linkDirectionalParticleSpeed={0.006}
        linkDirectionalParticleWidth={3}
        linkDirectionalParticleColor={() => '#ef4444'}
        linkCurvature={0.25}
        onNodeClick={handleNodeClick as any}
        onLinkClick={handleLinkClick as any}
        backgroundColor={isDark ? '#0a0f1e' : '#f8fafc'}
        cooldownTicks={100}
        onEngineStop={() => fgRef.current?.zoomToFit(400, 40)}
        enableNodeDrag={true}
        enableZoomInteraction={true}
        enablePanInteraction={true}
        minZoom={0.3}
        maxZoom={8}
      />
      {/* Zoom hints */}
      <div className={`absolute bottom-3 right-3 text-xs px-3 py-1.5 rounded-full
        ${isDark ? 'bg-slate-800/80 text-slate-400' : 'bg-white/80 text-slate-500'} 
        backdrop-blur-sm border ${isDark ? 'border-slate-700/50' : 'border-slate-200'}`}>
        Scroll to zoom • Drag to pan • Click nodes
      </div>
    </div>
  );
}
