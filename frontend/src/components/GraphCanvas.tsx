import { useCallback, useRef, useEffect, useMemo } from 'react';
import ForceGraph2D, { type ForceGraphMethods } from 'react-force-graph-2d';
import type { GraphNode, GraphEdge, HighlightState } from '@/lib/types';

interface Props {
  nodes: GraphNode[];
  links: GraphEdge[];
  highlight: HighlightState;
  onNodeClick: (node: GraphNode) => void;
  width: number;
  height: number;
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
  'crown-jewel': '#eab308',
  'critical': '#ef4444',
  'high': '#f97316',
  'medium': '#f59e0b',
  'low': '#22c55e',
  'entry-point': '#22c55e',
  'info': '#64748b',
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

export default function GraphCanvas({ nodes, links, highlight, onNodeClick, width, height, isDark }: Props) {
  const fgRef = useRef<ForceGraphMethods | undefined>();

  const graphData = useMemo(() => {
    return {
      nodes: nodes.map(n => ({ ...n })),
      links: links.map(l => ({ ...l })),
    };
  }, [nodes, links]);

  useEffect(() => {
    const fg = fgRef.current;
    if (fg) {
      fg.d3Force('charge')?.strength(-300);
      fg.d3Force('link')?.distance(80);
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

    // Outer glow for highlighted / critical nodes
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
  }, [getNodeColor, getNodeSize, highlight, isDark]);

  const getLinkColor = useCallback((link: { source: GraphNode | string; target: GraphNode | string }) => {
    const sourceId = typeof link.source === 'string' ? link.source : link.source.id;
    const targetId = typeof link.target === 'string' ? link.target : link.target.id;
    const edgeKey = `${sourceId}->${targetId}`;

    if (highlight.edges.size > 0 && highlight.edges.has(edgeKey)) {
      return '#ef4444';
    }
    if (highlight.nodes.size > 0) {
      if (highlight.nodes.has(sourceId) && highlight.nodes.has(targetId)) {
        return isDark ? 'rgba(99,102,241,0.5)' : 'rgba(99,102,241,0.4)';
      }
      return isDark ? 'rgba(30,41,59,0.3)' : 'rgba(203,213,225,0.3)';
    }
    return isDark ? 'rgba(71,85,105,0.4)' : 'rgba(148,163,184,0.3)';
  }, [highlight, isDark]);

  const getLinkWidth = useCallback((link: { source: GraphNode | string; target: GraphNode | string }) => {
    const sourceId = typeof link.source === 'string' ? link.source : link.source.id;
    const targetId = typeof link.target === 'string' ? link.target : link.target.id;
    const edgeKey = `${sourceId}->${targetId}`;
    if (highlight.edges.size > 0 && highlight.edges.has(edgeKey)) {
      return 3;
    }
    return 1;
  }, [highlight]);

  const handleNodeClick = useCallback((node: GraphNode) => {
    onNodeClick(node);
    const fg = fgRef.current;
    if (fg) {
      fg.centerAt(node.x, node.y, 600);
      fg.zoom(2.5, 600);
    }
  }, [onNodeClick]);

  return (
    <div className="graph-container relative w-full h-full">
      <ForceGraph2D
        ref={fgRef as any}
        graphData={graphData}
        width={width}
        height={height}
        nodeCanvasObject={paintNode as any}
        nodePointerAreaPaint={(node: any, color: string, ctx: CanvasRenderingContext2D) => {
          const size = getNodeSize(node);
          ctx.beginPath();
          ctx.arc(node.x ?? 0, node.y ?? 0, size + 2, 0, 2 * Math.PI);
          ctx.fillStyle = color;
          ctx.fill();
        }}
        linkColor={getLinkColor as any}
        linkWidth={getLinkWidth as any}
        linkDirectionalArrowLength={4}
        linkDirectionalArrowRelPos={0.85}
        linkDirectionalParticles={(link: any) => {
          const sourceId = typeof link.source === 'string' ? link.source : link.source.id;
          const targetId = typeof link.target === 'string' ? link.target : link.target.id;
          const edgeKey = `${sourceId}->${targetId}`;
          return highlight.edges.has(edgeKey) ? 3 : 0;
        }}
        linkDirectionalParticleSpeed={0.006}
        linkDirectionalParticleWidth={3}
        linkDirectionalParticleColor={() => '#ef4444'}
        linkCurvature={0.1}
        onNodeClick={handleNodeClick as any}
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
