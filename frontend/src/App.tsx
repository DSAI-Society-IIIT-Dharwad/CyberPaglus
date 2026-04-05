import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield, Moon, Sun, AlertTriangle, Activity, Database, Server,
  Lock, Wifi, WifiOff, Loader2, BarChart3, GitBranch, Search
} from 'lucide-react';
import GraphCanvas from './components/GraphCanvas';
import SecuritySidebar from './components/SecuritySidebar';
import ControlPanel from './components/ControlPanel';
import KillChainReport from './components/KillChainReport';
import { api } from './lib/api';
import type {
  GraphNode, GraphEdge, GraphData, HighlightState,
  BlastRadiusResult, ShortestPathResult, CycleResult, CriticalNodeResult,
  TopCriticalPathResult, TopCriticalPath,
} from './lib/types';

function App() {
  // ── Theme ────────────────────────────────
  const [isDark, setIsDark] = useState(() => {
    const saved = localStorage.getItem('kubeinsights-theme');
    return saved ? saved === 'dark' : true;
  });
  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark);
    localStorage.setItem('kubeinsights-theme', isDark ? 'dark' : 'light');
  }, [isDark]);

  // ── Graph State ──────────────────────────
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [links, setLinks] = useState<GraphEdge[]>([]);
  const [loading, setLoading] = useState(true);
  const [apiLoading, setApiLoading] = useState(false);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<{ text: string; type: 'success' | 'error' | 'info' } | null>(null);

  // ── UI State ─────────────────────────────
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<GraphEdge | null>(null);
  const [selectedCriticalPath, setSelectedCriticalPath] = useState<TopCriticalPath | null>(null);
  const [highlight, setHighlight] = useState<HighlightState>({
    nodes: new Set(), edges: new Set(), path: [], mode: 'none',
  });
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);
  const [hoverHighlight, setHoverHighlight] = useState<{ nodes: Set<string>; edges: Set<string> }>({
    nodes: new Set(), edges: new Set(),
  });
  const [showKillChain, setShowKillChain] = useState(false);

  // ── Analysis Results ─────────────────────
  const [blastResult, setBlastResult] = useState<BlastRadiusResult | null>(null);
  const [pathResult, setPathResult] = useState<ShortestPathResult | null>(null);
  const [cycleResult, setCycleResult] = useState<CycleResult | null>(null);
  const [criticalResult, setCriticalResult] = useState<CriticalNodeResult | null>(null);
  const [topCriticalResult, setTopCriticalResult] = useState<TopCriticalPathResult | null>(null);

  // ── Graph container sizing ───────────────
  const graphContainerRef = useRef<HTMLDivElement>(null);
  // ── Load Graph ───────────────────────────
  const loadGraph = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getGraph();
      setGraphData(data);
      setNodes(data.nodes);
      setLinks(data.links);
      setConnected(true);
      setLoading(false);
    } catch (err: any) {
      setError(err.message || 'Failed to connect to backend');
      setConnected(false);
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadGraph();
  }, [loadGraph]);

  // ── Auto-analyze critical paths on graph load ─
  useEffect(() => {
    if (graphData && !topCriticalResult) {
      // Auto-analyze with a default count to discover total paths
      (async () => {
        try {
          const result = await api.topCriticalPaths(3);
          setTopCriticalResult(result);
        } catch (err) {
          // Silent fail - user can still manually trigger analysis
        }
      })();
    }
  }, [graphData, topCriticalResult]);

  // ── Flash status ─────────────────────────
  const flash = (text: string, type: 'success' | 'error' | 'info') => {
    setStatusMessage({ text, type });
    setTimeout(() => setStatusMessage(null), 4000);
  };

  // ── Clear Highlights ─────────────────────
  const clearHighlight = () => {
    setHighlight({ nodes: new Set(), edges: new Set(), path: [], mode: 'none' });
    setHoveredNode(null);
    setHoverHighlight({ nodes: new Set(), edges: new Set() });
    setBlastResult(null);
    setPathResult(null);
    setCycleResult(null);
    setCriticalResult(null);
    setSelectedEdge(null);
    setTopCriticalResult(null);
    setSelectedCriticalPath(null);
  };

  // ── Hover Insights ──────────────────────
  const adjacencyList = useMemo(() => {
    const list: Record<string, string[]> = {};
    links.forEach(l => {
      const s = typeof l.source === 'string' ? l.source : (l.source as any).id;
      const t = typeof l.target === 'string' ? l.target : (l.target as any).id;
      if (!list[s]) list[s] = [];
      list[s].push(t);
    });
    return list;
  }, [links]);

  const handleNodeHover = useCallback((node: GraphNode | null) => {
    setHoveredNode((prev) => {
      const prevId = prev?.id;
      const nextId = node?.id;
      
      if (prevId === nextId) return prev;
      
      // Node changed, update highlights
      if (!node) {
        setHoverHighlight({ nodes: new Set(), edges: new Set() });
      } else {
        const reachableNodes = new Set([node.id]);
        const reachableEdges = new Set<string>();
        const queue = [node.id];
        
        while (queue.length > 0) {
          const curr = queue.shift()!;
          const neighbors = adjacencyList[curr] || [];
          neighbors.forEach((next: string) => {
            if (!reachableNodes.has(next)) {
              reachableNodes.add(next);
              reachableEdges.add(`${curr}->${next}`);
              queue.push(next);
            }
          });
        }
        setHoverHighlight({ nodes: reachableNodes, edges: reachableEdges });
      }
      return node;
    });
  }, [adjacencyList]);

  // ── Algorithm Handlers ───────────────────
  const handleBlastRadius = async (source: string, hops: number) => {
    setApiLoading(true);
    try {
      const result = await api.blastRadius(source, hops);
      setBlastResult(result);

      const nodeIds = new Set(result.affected_nodes.map(n => n.id));
      const edgeIds = new Set(result.affected_edges.map(e => `${e.source}->${e.target}`));
      setHighlight({ nodes: nodeIds, edges: edgeIds, path: [], mode: 'blast-radius' });
      flash(`Blast radius: ${result.total_affected} nodes in danger zone`, result.risk_summary === 'CRITICAL' ? 'error' : 'info');
    } catch (err: any) {
      flash(err.message, 'error');
    }
    setApiLoading(false);
  };

  const handleShortestPath = async (source: string, target: string) => {
    setApiLoading(true);
    try {
      const result = await api.shortestPath(source, target);
      setPathResult(result);

      if (result.path_exists) {
        const nodeIds = new Set(result.path);
        const edgeIds = new Set<string>();
        for (let i = 0; i < result.path.length - 1; i++) {
          edgeIds.add(`${result.path[i]}->${result.path[i + 1]}`);
        }
        setHighlight({ nodes: nodeIds, edges: edgeIds, path: result.path, mode: 'shortest-path' });
        flash(`${result.difficulty} attack path found: ${result.hop_count} hops, weight ${result.total_weight}`,
          result.difficulty === 'TRIVIAL' || result.difficulty === 'EASY' ? 'error' : 'info');
      } else {
        clearHighlight();
        flash('No attack path exists between these nodes ✓', 'success');
      }
    } catch (err: any) {
      flash(err.message, 'error');
    }
    setApiLoading(false);
  };

  const handleDetectCycles = async () => {
    setApiLoading(true);
    try {
      const result = await api.detectCycles();
      setCycleResult(result);

      if (result.has_cycles) {
        const nodeIds = new Set<string>();
        const edgeIds = new Set<string>();
        result.cycles.forEach(c => {
          c.cycle.forEach(n => nodeIds.add(n));
          for (let i = 0; i < c.cycle.length; i++) {
            const next = c.cycle[(i + 1) % c.cycle.length];
            edgeIds.add(`${c.cycle[i]}->${next}`);
          }
        });
        setHighlight({ nodes: nodeIds, edges: edgeIds, path: [], mode: 'cycles' });
        flash(`${result.total_cycles} circular permission loop(s) detected`, 'error');
      } else {
        clearHighlight();
        flash('No circular permission loops found ✓', 'success');
      }
    } catch (err: any) {
      flash(err.message, 'error');
    }
    setApiLoading(false);
  };

  const handleCriticalNode = async () => {
    setApiLoading(true);
    try {
      const result = await api.criticalNode();
      setCriticalResult(result);
      setTopCriticalResult(null);

      if (result.critical_node) {
        const nodeIds = new Set([result.critical_node.node_id]);
        setHighlight({ nodes: nodeIds, edges: new Set(), path: [], mode: 'critical-node' });
        flash(`Critical node: ${result.critical_node.label} (${result.critical_node.impact_percentage}% impact)`, 'info');
      }
    } catch (err: any) {
      flash(err.message, 'error');
    }
    setApiLoading(false);
  };

  const handleTopCriticalPaths = async (count: number) => {
    setApiLoading(true);
    try {
      const result = await api.topCriticalPaths(count);
      setTopCriticalResult(result);
      setCriticalResult(null);
      setBlastResult(null);
      setPathResult(null);
      setCycleResult(null);

      if (result?.top_critical_paths?.[0]) {
        const path = result.top_critical_paths[0].path;
        const nodeIds = new Set(path);
        const edgeIds = new Set<string>();
        for (let i = 0; i < path.length - 1; i++) {
          edgeIds.add(`${path[i]}->${path[i + 1]}`);
        }
        setHighlight({ nodes: nodeIds, edges: edgeIds, path, mode: 'top-critical-paths' });
        flash(`Top critical path loaded: ${result.top_critical_paths[0].difficulty} (${result.top_critical_paths[0].total_weight} weight)`, 'info');
      } else {
        setHighlight({ nodes: new Set(), edges: new Set(), path: [], mode: 'none' });
        flash('No critical attack paths found', 'success');
      }
    } catch (err: any) {
      flash(err.message, 'error');
    }
    setApiLoading(false);
  };

  const handleSelectCriticalPath = (path: TopCriticalPath) => {
    setSelectedCriticalPath(path);
    setSelectedNode(null);

    // Highlight the path on the graph
    const nodeIds = new Set(path.path);
    const edgeIds = new Set<string>();
    for (let i = 0; i < path.path.length - 1; i++) {
      edgeIds.add(`${path.path[i]}->${path.path[i + 1]}`);
    }
    setHighlight({ nodes: nodeIds, edges: edgeIds, path: path.path, mode: 'top-critical-paths' });
    flash(`Critical path selected: ${path.rank} (${path.difficulty})`, 'info');
  };

  const handleRemediate = async (nodeId: string) => {
    setApiLoading(true);
    try {
      const result = await api.remediate(nodeId);
      const newGraph = result.updated_graph;
      setGraphData(newGraph);
      setNodes(newGraph.nodes);
      setLinks(newGraph.links);
      clearHighlight();
      setSelectedNode(null);
      setSelectedEdge(null);
      setTopCriticalResult(null);
      setSelectedCriticalPath(null);
      setCriticalResult(null);
      flash(result.message, 'success');
    } catch (err: any) {
      flash(err.message, 'error');
    }
    setApiLoading(false);
  };

  const handleReset = async () => {
    setApiLoading(true);
    try {
      const result = await api.reset();
      setGraphData(result.graph);
      setNodes(result.graph.nodes);
      setLinks(result.graph.links);
      clearHighlight();
      setSelectedNode(null);
      setSelectedEdge(null);
      setSelectedCriticalPath(null);
      flash('Graph reset to original state', 'success');
    } catch (err: any) {
      flash(err.message, 'error');
    }
    setApiLoading(false);
  };

  const handleUpload = async (file: File) => {
    setApiLoading(true);
    try {
      const result = await api.uploadGraph(file);
      setGraphData(result.graph);
      setNodes(result.graph.nodes);
      setLinks(result.graph.links);
      clearHighlight();
      setSelectedNode(null);
      setSelectedNode(null);
      setSelectedEdge(null);
      setTopCriticalResult(null);
      setSelectedCriticalPath(null);
      flash(result.message, 'success');
    } catch (err: any) {
      flash(err.message, 'error');
    }
    setApiLoading(false);
  };

  const handleNodeClick = (node: GraphNode) => {
    setSelectedNode(node);
    setSelectedEdge(null);
  };

  const handleLinkClick = (link: GraphEdge) => {
    setSelectedEdge(link);
    setSelectedNode(null);
  };

  const handleFindPathToNode = (targetId: string) => {
    handleShortestPath('internet', targetId);
  };

  // ── Loading Screen ───────────────────────
  if (loading) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${isDark ? 'bg-[#0a0f1e]' : 'bg-slate-50'}`}>
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center space-y-4"
        >
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          >
            <Shield className={`w-16 h-16 mx-auto ${isDark ? 'text-blue-400' : 'text-blue-600'}`} />
          </motion.div>
          <h1 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>KubeInsights</h1>
          <p className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Connecting to analysis engine...</p>
          <Loader2 className={`w-5 h-5 mx-auto animate-spin ${isDark ? 'text-blue-400' : 'text-blue-600'}`} />
        </motion.div>
      </div>
    );
  }

  // ── Error Screen ─────────────────────────
  if (error && !graphData) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${isDark ? 'bg-[#0a0f1e]' : 'bg-slate-50'}`}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center space-y-4 max-w-md px-6"
        >
          <WifiOff className="w-16 h-16 mx-auto text-red-400" />
          <h1 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>Connection Failed</h1>
          <p className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>{error}</p>
          <div className={`text-xs p-4 rounded-xl ${isDark ? 'bg-slate-800/50 text-slate-400' : 'bg-slate-100 text-slate-500'}`}>
            <p className="font-mono mb-2">Make sure the backend is running:</p>
            <code className={`block p-2 rounded ${isDark ? 'bg-slate-900' : 'bg-white'}`}>
              cd backend && uvicorn main:app --reload
            </code>
          </div>
          <button
            onClick={loadGraph}
            className="px-6 py-2.5 rounded-xl text-sm font-medium bg-gradient-to-r from-blue-600 to-cyan-600 text-white
              hover:from-blue-500 hover:to-cyan-500 transition-all hover:shadow-lg hover:shadow-blue-500/20"
          >
            Retry Connection
          </button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen flex flex-col ${isDark ? 'bg-[#0a0f1e]' : 'bg-slate-50'}`}>
      {/* ─── Header ─────────────────────────── */}
      <header className={`shrink-0 flex items-center justify-between px-5 py-3 border-b z-40
        ${isDark ? 'bg-slate-900/80 border-slate-700/50' : 'bg-white/80 border-slate-200'}
        backdrop-blur-xl`}>
        <div className="flex items-center gap-3">
          <motion.div
            whileHover={{ rotate: 15, scale: 1.1 }}
            className="p-2 rounded-xl bg-gradient-to-br from-blue-600 to-cyan-500 shadow-lg shadow-blue-500/20"
          >
            <Shield className="w-5 h-5 text-white" />
          </motion.div>
          <div>
            <h1 className={`text-lg font-bold tracking-tight ${isDark ? 'text-white' : 'text-slate-900'}`}>
              KubeInsights
            </h1>
            <p className={`text-[11px] ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
              Kubernetes Security Analysis Dashboard
            </p>
          </div>
        </div>

        {/* Center - Stats */}
        {graphData && (
          <div className="hidden md:flex items-center gap-6">
            <div className="flex items-center gap-2 px-2 py-1 rounded-lg">
              <Server className={`w-3.5 h-3.5 ${isDark ? 'text-slate-500' : 'text-slate-400'}`} />
              <span className={`text-xs font-medium ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                {graphData.stats.total_nodes} Nodes
              </span>
            </div>
            <div className="flex items-center gap-2 px-2 py-1 rounded-lg">
              <GitBranch className={`w-3.5 h-3.5 ${isDark ? 'text-slate-500' : 'text-slate-400'}`} />
              <span className={`text-xs font-medium ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                {graphData.stats.total_edges} Edges
              </span>
            </div>
            <button 
              onClick={() => {
                const criticalNodes = new Set(nodes.filter(n => n.risk_level === 'critical').map(n => n.id));
                setHighlight({
                  nodes: criticalNodes,
                  edges: new Set(),
                  path: [],
                  mode: 'group-critical'
                });
                setSelectedNode(null); // Clear active sidebar to focus on the group
              }}
              className="flex items-center gap-2 px-2 py-1 rounded-lg hover:bg-red-500/10 cursor-pointer transition-colors"
              title="Highlight all Critical Risk nodes"
            >
              <AlertTriangle className="w-3.5 h-3.5 text-red-400" />
              <span className="text-xs font-medium text-red-400">
                {graphData.stats.critical_nodes} Critical
              </span>
            </button>
            <button 
              onClick={() => {
                const jewelNodes = new Set(nodes.filter(n => n.risk_level === 'crown-jewel').map(n => n.id));
                setHighlight({
                  nodes: jewelNodes,
                  edges: new Set(),
                  path: [],
                  mode: 'group-crown-jewel'
                });
                setSelectedNode(null); // Clear active sidebar to focus on the group
              }}
              className="flex items-center gap-2 px-2 py-1 rounded-lg hover:bg-yellow-500/10 cursor-pointer transition-colors"
              title="Highlight all Crown Jewel nodes"
            >
              <Database className="w-3.5 h-3.5 text-yellow-400" />
              <span className="text-xs font-medium text-yellow-400">
                {graphData.stats.crown_jewels} Crown Jewels
              </span>
            </button>
          </div>
        )}

        {/* Right */}
        <div className="flex items-center gap-3">
          {/* Connection status */}
          <div className="flex items-center gap-1.5">
            <div className={`w-2 h-2 rounded-full status-dot ${connected ? 'bg-green-400' : 'bg-red-400'}`} />
            <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
              {connected ? 'Connected' : 'Offline'}
            </span>
          </div>

          {/* Cluster name */}
          {graphData?.metadata?.cluster_name && (
            <span className={`text-xs px-2.5 py-1 rounded-full font-mono
              ${isDark ? 'bg-slate-800 text-cyan-400 border border-slate-700' : 'bg-slate-100 text-blue-600 border border-slate-200'}`}>
              {graphData.metadata.cluster_name}
            </span>
          )}

          {/* Theme toggle */}
          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={() => setIsDark(!isDark)}
            className={`p-2 rounded-xl transition-colors ${isDark ? 'bg-slate-800 hover:bg-slate-700 text-yellow-400' : 'bg-slate-100 hover:bg-slate-200 text-slate-600'}`}
          >
            {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </motion.button>
        </div>
      </header>

      {/* ─── Status Message ─────────────────── */}
      <AnimatePresence>
        {statusMessage && (
          <motion.div
            initial={{ y: -40, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -40, opacity: 0 }}
            className={`absolute top-[60px] left-1/2 -translate-x-1/2 z-50 px-4 py-2 rounded-xl shadow-lg text-xs font-medium flex items-center gap-2
              ${statusMessage.type === 'error' ? 'bg-red-500/90 text-white' :
                statusMessage.type === 'success' ? 'bg-green-500/90 text-white' :
                  'bg-blue-500/90 text-white'}
              backdrop-blur-sm`}
          >
            {statusMessage.type === 'error' && <AlertTriangle className="w-3.5 h-3.5" />}
            {statusMessage.type === 'success' && <Lock className="w-3.5 h-3.5" />}
            {statusMessage.type === 'info' && <Activity className="w-3.5 h-3.5" />}
            {statusMessage.text}
          </motion.div>
        )}
      </AnimatePresence>

      {/* ─── Main Layout ────────────────────── */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left Panel: Controls */}
        <div className={`shrink-0 w-[320px] border-r overflow-hidden flex flex-col
          ${isDark ? 'bg-slate-900/50 border-slate-700/50' : 'bg-white border-slate-200'}`}>
          {/* Scenario Badge */}
          {graphData?.metadata?.scenario && (
            <div className={`mx-4 mt-3 px-3 py-2 rounded-xl text-xs border animate-border-pulse
              ${isDark ? 'bg-red-950/30 border-red-900/40 text-red-300' : 'bg-red-50 border-red-200 text-red-700'}`}>
              <span className="font-semibold">🎯 Active Scenario:</span> {graphData.metadata.scenario}
            </div>
          )}

          {/* Node Search Map */}
          <div className="px-4 mt-4">
            <div className="relative group">
              <Search className={`w-4 h-4 absolute left-3 top-2.5 transition-colors ${isDark ? 'text-slate-500 group-focus-within:text-blue-400' : 'text-slate-400 group-focus-within:text-blue-500'}`} />
              <input
                type="text"
                list="node-search-list"
                placeholder="Search to locate node..."
                onChange={(e) => {
                  const val = e.target.value;
                  if (!val) return;
                  const found = nodes.find(n => n.id === val || n.label === val);
                  if (found) {
                    handleNodeClick(found);
                    setTimeout(() => { e.target.value = ''; }, 100);
                  }
                }}
                className={`w-full pl-9 pr-3 py-2 text-sm rounded-xl border outline-none transition-all
                  ${isDark 
                    ? 'bg-slate-800/40 border-slate-700/50 text-slate-200 focus:bg-slate-800/80 focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/50 placeholder:text-slate-500' 
                    : 'bg-white border-slate-200 text-slate-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 placeholder:text-slate-400'}`}
              />
              <datalist id="node-search-list">
                {nodes.map(n => (
                  <option key={n.id} value={n.label || n.id} />
                ))}
              </datalist>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto">
            <ControlPanel
              nodes={nodes}
              onBlastRadius={handleBlastRadius}
              onShortestPath={handleShortestPath}
              onDetectCycles={handleDetectCycles}
              onCriticalNode={handleCriticalNode}
              onTopCriticalPaths={handleTopCriticalPaths}
              onSelectCriticalPath={handleSelectCriticalPath}
              onRemediate={handleRemediate}
              onReset={handleReset}
              onUpload={handleUpload}
              onShowKillChain={() => setShowKillChain(true)}
              criticalNodeResult={criticalResult}
              topCriticalResult={topCriticalResult}
              cycleResult={cycleResult}
              blastResult={blastResult}
              pathResult={pathResult}
              loading={apiLoading}
              isDark={isDark}
              selectedNode={selectedNode}
            />
          </div>
        </div>

        {/* Center: Graph Canvas */}
        <div
          ref={graphContainerRef}
          className={`flex-1 relative overflow-hidden cyber-grid ${isDark ? '' : ''}`}
        >
          {/* Clear highlight button */}
          <AnimatePresence>
            {highlight.mode !== 'none' && (
              <motion.button
                initial={{ y: -20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                exit={{ y: -20, opacity: 0 }}
                onClick={clearHighlight}
                className={`absolute top-3 left-3 z-20 px-3 py-1.5 rounded-full text-xs font-medium flex items-center gap-1.5 transition-all
                  ${isDark ? 'bg-slate-800/80 text-slate-300 hover:bg-slate-700 border border-slate-700' : 'bg-white/80 text-slate-600 hover:bg-white border border-slate-200'}
                  backdrop-blur-sm`}
              >
                <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
                {highlight.mode === 'blast-radius' && 'Blast Radius Active'}
                {highlight.mode === 'shortest-path' && 'Attack Path Active'}
                {highlight.mode === 'cycles' && 'Cycles Highlighted'}
                {highlight.mode === 'critical-node' && 'Critical Node Highlighted'}
                <span className="ml-1">✕</span>
              </motion.button>
            )}
          </AnimatePresence>

          {/* Legend */}
          <div className={`absolute bottom-3 left-3 z-20 p-3 rounded-xl text-[10px] space-y-1.5
            ${isDark ? 'bg-slate-900/80 border border-slate-700/50' : 'bg-white/80 border border-slate-200'}
            backdrop-blur-sm`}>
            <button
              onClick={() => {
                const filtered = new Set(nodes.filter(n => n.type === 'internet' || n.risk_level === 'entry-point').map(n => n.id));
                setHighlight({ nodes: filtered, edges: new Set(), path: [], mode: 'group-entry-point' });
                setSelectedNode(null);
              }}
              className="flex items-center gap-2 w-full hover:bg-slate-500/10 px-2 py-1 -mx-2 rounded transition-colors text-left"
            >
              <span className="w-3 h-3 rounded-full bg-green-500 shrink-0" />
              <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Internet / Entry Point</span>
            </button>
            <button
              onClick={() => {
                const filtered = new Set(nodes.filter(n => n.risk_level === 'critical').map(n => n.id));
                setHighlight({ nodes: filtered, edges: new Set(), path: [], mode: 'group-critical' });
                setSelectedNode(null);
              }}
              className="flex items-center gap-2 w-full hover:bg-slate-500/10 px-2 py-1 -mx-2 rounded transition-colors text-left"
            >
              <span className="w-3 h-3 rounded-full bg-red-500 shrink-0" />
              <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Critical Risk</span>
            </button>
            <button
              onClick={() => {
                const filtered = new Set(nodes.filter(n => n.risk_level === 'crown-jewel').map(n => n.id));
                setHighlight({ nodes: filtered, edges: new Set(), path: [], mode: 'group-crown-jewel' });
                setSelectedNode(null);
              }}
              className="flex items-center gap-2 w-full hover:bg-slate-500/10 px-2 py-1 -mx-2 rounded transition-colors text-left"
            >
              <span className="w-3 h-3 rounded-full bg-yellow-500 shrink-0" />
              <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Crown Jewel</span>
            </button>
            <button
              onClick={() => {
                // Info or medium risks, or typical pods
                const filtered = new Set(nodes.filter(n => n.risk_level === 'info' || n.risk_level === 'medium' || n.type === 'pod' || n.type === 'service').map(n => n.id));
                setHighlight({ nodes: filtered, edges: new Set(), path: [], mode: 'group-standard' });
                setSelectedNode(null);
              }}
              className="flex items-center gap-2 w-full hover:bg-slate-500/10 px-2 py-1 -mx-2 rounded transition-colors text-left"
            >
              <span className="w-3 h-3 rounded-full bg-indigo-500 shrink-0" />
              <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Standard Entity</span>
            </button>
            <button
              onClick={() => {
                const filtered = new Set(nodes.filter(n => n.risk_level === 'low').map(n => n.id));
                setHighlight({ nodes: filtered, edges: new Set(), path: [], mode: 'group-low' });
                setSelectedNode(null);
              }}
              className="flex items-center gap-2 w-full hover:bg-slate-500/10 px-2 py-1 -mx-2 rounded transition-colors text-left"
            >
              <span className="w-3 h-3 rounded-full bg-slate-500 shrink-0" />
              <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Low Risk / Utility</span>
            </button>
          </div>

          <GraphCanvas
            nodes={nodes}
            links={links}
            highlight={highlight}
            onNodeClick={handleNodeClick}
            onLinkClick={setSelectedEdge}
            selectedNode={selectedNode}
            selectedEdge={selectedEdge}
            hoveredNode={hoveredNode}
            hoverHighlight={hoverHighlight}
            onNodeHover={handleNodeHover}
            isDark={isDark}
          />

          {/* Security Sidebar (overlays right side of graph) */}
          <SecuritySidebar
            node={selectedNode}
            edge={selectedEdge}
            criticalPath={selectedCriticalPath}
            onClose={() => {
              setSelectedNode(null);
              setSelectedEdge(null);
              setSelectedCriticalPath(null);
            }}
            onBlastRadius={(nodeId) => handleBlastRadius(nodeId, 3)}
            onFindPath={handleFindPathToNode}
            isDark={isDark}
          />
        </div>
      </div>

      {/* ─── Kill Chain Report Modal ────────── */}
      <KillChainReport
        result={pathResult}
        isOpen={showKillChain}
        onClose={() => setShowKillChain(false)}
        isDark={isDark}
      />
    </div>
  );
}

export default App;
