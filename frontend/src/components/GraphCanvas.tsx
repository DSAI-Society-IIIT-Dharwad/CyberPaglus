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
  hoveredNode?: GraphNode | null;
  hoverHighlight?: { nodes: Set<string>; edges: Set<string> };
  onNodeHover?: (node: GraphNode | null) => void;
  isDark: boolean;
}

const RISK_COLORS: Record<string, string> = {
  'crown-jewel': '#eab308',
  'critical': '#ef4444',
  'high': '#f97316',
  'medium': '#f59e0b',
  'low': '#64748b',
  'entry-point': '#22c55e',
  'info': '#6366f1',
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

export default function GraphCanvas({ 
  nodes, links, highlight, onNodeClick, onLinkClick, 
  selectedNode, selectedEdge, hoveredNode, hoverHighlight, onNodeHover, isDark 
}: Props) {
  const fgRef = useRef<ForceGraphMethods | null>(null);

  // Stable graph data
  const graphData = useMemo(() => ({
    nodes: nodes.map(n => ({ ...n })),
    links: links.map(l => ({ ...l })),
  }), [nodes.length, links.length]);

  // Initial Zoom-to-fit
  useEffect(() => {
    if (nodes.length > 0) {
      setTimeout(() => {
        fgRef.current?.zoomToFit(600, 80);
      }, 500);
    }
  }, [nodes.length]);

  // Forces tune
  useEffect(() => {
    const fg = fgRef.current;
    if (fg) {
      fg.d3Force('charge')?.strength(-500);
      fg.d3Force('link')?.distance(80);
      fg.d3Force('center')?.strength(0.1);
      (fg as any).d3ReheatSimulation?.();
    }
  }, [graphData]);

  // Helper check for selection
  const isSelected = useCallback((nodeId: string) => {
    if (!nodeId) return false;
    if (selectedNode?.id === nodeId) return true;
    if (selectedEdge) {
      const s = typeof selectedEdge.source === 'string' ? selectedEdge.source : (selectedEdge.source as any)?.id;
      const t = typeof selectedEdge.target === 'string' ? selectedEdge.target : (selectedEdge.target as any)?.id;
      return (s === nodeId || t === nodeId);
    }
    return false;
  }, [selectedNode, selectedEdge]);

  // Paint Node Logic
  const paintNode = useCallback((node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
    if (!node || !ctx) return;
    const x = node.x ?? 0;
    const y = node.y ?? 0;
    const id = node.id;
    if (!id) return;

    // Dimensions
    const baseSize = node.type === 'internet' ? 10 :
      node.risk_level === 'crown-jewel' ? 9 :
        node.risk_level === 'critical' ? 8 :
          node.type === 'pod' ? 7 : 6;
    
    let size = baseSize;
    if (highlight?.nodes && highlight.nodes.size > 0) {
      size = highlight.nodes.has(id) ? baseSize * 1.3 : baseSize * 0.6;
    }

    const isOnPath = !!(highlight?.path && highlight.path.includes(id));
    const isHighlighted = !highlight?.nodes || (highlight.nodes.size === 0) || highlight.nodes.has(id);
    const isHovered = hoveredNode?.id === id;
    const isHoverReachable = !!(hoverHighlight?.nodes && hoverHighlight.nodes.has(id));
    const isSelectedNode = isSelected(id);

    let color = RISK_COLORS[node.risk_level] || '#6366f1';
    if (isOnPath) color = '#ef4444';
    else if (isHoverReachable) color = '#22d3ee';
    else if ((highlight?.nodes && highlight.nodes.size > 0 && !isHighlighted) || (hoveredNode && !isHoverReachable && !isHovered)) {
      color = isDark ? '#1e293b' : '#cbd5e1';
    }

    // Glow Halo (Prioritize Selection/Hover)
    if (isSelectedNode || isHovered) {
      const haloColor = isHovered ? '#22d3ee' : (isSelectedNode ? '#ef4444' : color);
      ctx.beginPath();
      ctx.arc(x, y, size + 8, 0, 2 * Math.PI);
      ctx.globalAlpha = isDark ? 0.25 : 0.15;
      ctx.fillStyle = haloColor;
      ctx.fill();
      ctx.globalAlpha = 1.0;
      
      ctx.shadowColor = haloColor;
      ctx.shadowBlur = isHovered ? 30 : 25;
      ctx.strokeStyle = haloColor;
      ctx.lineWidth = 3;
      ctx.stroke();
      ctx.shadowBlur = 0;
    }

    // Secondary Radial Glow for Critical Nodes
    if ((isHighlighted || isHoverReachable) && (node.risk_level === 'critical' || node.risk_level === 'crown-jewel' || isHoverReachable)) {
      const glowColor = isHoverReachable ? '#22d3ee' : color;
      const glowSize = size + (isHoverReachable ? 6 : 4);
      const grad = ctx.createRadialGradient(x, y, size * 0.4, x, y, glowSize);
      grad.addColorStop(0, glowColor + '70');
      grad.addColorStop(1, glowColor + '00');
      ctx.beginPath();
      ctx.arc(x, y, glowSize, 0, 2 * Math.PI);
      ctx.fillStyle = grad;
      ctx.fill();
    }

    // Node Body
    ctx.beginPath();
    ctx.arc(x, y, size, 0, 2 * Math.PI);
    ctx.fillStyle = color;
    ctx.fill();
    
    ctx.strokeStyle = isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)';
    ctx.lineWidth = 1;
    ctx.stroke();

    // Icon
    if (globalScale > 0.8) {
      const icon = NODE_ICONS[node.type] || '⚪';
      ctx.font = `${Math.max(size * 0.9, 6)}px Arial`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = (node.risk_level === 'crown-jewel' || isOnPath) ? '#fff' : (isDark ? '#fff' : '#000');
      ctx.fillText(icon, x, y);
    }

    // Label
    if (globalScale > 1.2) {
      ctx.font = `${Math.max(10 / globalScale, 3)}px Inter, sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      const labelVisible = isHighlighted || isHoverReachable || isSelectedNode;
      ctx.fillStyle = labelVisible
        ? (isDark ? '#f1f5f9' : '#1e293b')
        : (isDark ? 'rgba(71,85,105,0.4)' : 'rgba(148,163,184,0.4)');
      ctx.fillText(node.label || id, x, y + size + 5);
    }
  }, [highlight, hoveredNode, hoverHighlight, isDark, isSelected]);

  // Link Painting Logic
  const paintLink = useCallback((link: any, ctx: CanvasRenderingContext2D) => {
    if (!link || !ctx) return;
    const start = link.source;
    const end = link.target;
    if (!start?.x || !end?.x) return;

    const sId = start.id;
    const tId = end.id;
    const key = `${sId}->${tId}`;

    const isAnalysis = !!(highlight?.edges && highlight.edges.has(key));
    const isHover = !!(hoverHighlight?.edges && hoverHighlight.edges.size > 0 && hoverHighlight.edges.has(key));
    const isFaded = (highlight?.edges && highlight.edges.size > 0 && !isAnalysis) || 
                    (hoveredNode && !isHover);

    let color = isDark ? 'rgba(148,163,184,0.2)' : 'rgba(71,85,105,0.3)';
    let width = 1.2;

    if (isAnalysis) { color = '#ef4444'; width = 3.5; }
    else if (isHover) { color = '#22d3ee'; width = 2.5; }
    else if (isFaded) { color = isDark ? 'rgba(30,41,59,0.05)' : 'rgba(203,213,225,0.1)'; }

    ctx.beginPath();
    ctx.moveTo(start.x, start.y);
    ctx.lineTo(end.x, end.y);
    
    if (isAnalysis || isHover) {
      ctx.shadowColor = color;
      ctx.shadowBlur = isAnalysis ? 12 : 8;
    }
    
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.stroke();
    ctx.shadowBlur = 0;
  }, [highlight, hoverHighlight, hoveredNode, isDark]);

  return (
    <div className="graph-container relative w-full h-full">
      <ForceGraph2D
        ref={fgRef as any}
        graphData={graphData}
        nodeCanvasObject={paintNode}
        linkCanvasObject={paintLink}
        nodePointerAreaPaint={(node: any, color: string, ctx: CanvasRenderingContext2D) => {
          const size = baseSizeForNode(node);
          ctx.beginPath();
          ctx.arc(node.x ?? 0, node.y ?? 0, size + 6, 0, 2 * Math.PI);
          ctx.fillStyle = color;
          ctx.fill();
        }}
        onNodeHover={(node: any) => onNodeHover?.(node)}
        onNodeClick={(node: any) => onNodeClick(node)}
        onLinkClick={(link: any) => onLinkClick(link as GraphEdge)}
        nodeLabel={(node: any) => node ? `
          <div class="cyber-tooltip">
            <div class="flex items-center gap-2 mb-1">
              <span style="color: #22d3ee; font-weight: bold;">${node.label || node.id}</span>
              <span style="color: #64748b; font-size: 10px; margin-left: 5px;">${node.type?.toUpperCase()}</span>
            </div>
            <div style="font-size: 11px; color: #94a3b8;">
              NS: ${node.namespace} | <span style="color: #ef4444; font-weight: bold;">${node.risk_level?.toUpperCase()}</span>
            </div>
          </div>
        ` : ''}
        backgroundColor={isDark ? '#0a0f1e' : '#f8fafc'}
        cooldownTicks={150}
        enableNodeDrag={true}
        enableZoomInteraction={true}
        enablePanInteraction={true}
        minZoom={0.1}
        maxZoom={10}
      />
      <div className={`absolute bottom-4 right-4 text-[10px] px-3 py-1.5 rounded-full
        ${isDark ? 'bg-slate-900/90 text-slate-500 border-slate-800' : 'bg-white/90 text-slate-400 border-slate-100'} 
        backdrop-blur-md border shadow-2xl pointer-events-none`}>
        SHIFT+DRAG to select • SCROLL to zoom • HOVER is automated
      </div>
    </div>
  );
}

function baseSizeForNode(node: any) {
  if (!node) return 6;
  return node.type === 'internet' ? 10 :
    node.risk_level === 'crown-jewel' ? 9 :
      node.risk_level === 'critical' ? 8 :
        node.type === 'pod' ? 7 : 6;
}
