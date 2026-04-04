import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Crosshair, Route, RefreshCcw, AlertTriangle, Search, Trash2,
  Upload, Zap, RotateCcw, ChevronDown, ChevronUp, Loader2, Shield,
  TrendingUp, Target, Info
} from 'lucide-react';
import type { GraphNode, CriticalNodeResult, TopCriticalPathResult, TopCriticalPath, CycleResult, BlastRadiusResult, ShortestPathResult } from '@/lib/types';

interface Props {
  nodes: GraphNode[];
  onBlastRadius: (source: string, hops: number) => Promise<void>;
  onShortestPath: (source: string, target: string) => Promise<void>;
  onDetectCycles: () => Promise<void>;
  onCriticalNode: () => Promise<void>;
  onTopCriticalPaths: (count: number) => Promise<void>;
  onSelectCriticalPath: (path: TopCriticalPath) => void;
  onRemediate: (nodeId: string) => void;
  onReset: () => void;
  onUpload: (file: File) => void;
  onShowKillChain: () => void;
  criticalNodeResult: CriticalNodeResult | null;
  topCriticalResult: TopCriticalPathResult | null;
  cycleResult: CycleResult | null;
  blastResult: BlastRadiusResult | null;
  pathResult: ShortestPathResult | null;
  loading: boolean;
  isDark: boolean;
}

export default function ControlPanel({
  nodes, onBlastRadius, onShortestPath, onDetectCycles, onCriticalNode,
  onTopCriticalPaths, onSelectCriticalPath, onRemediate, onReset, onUpload, onShowKillChain,
  criticalNodeResult, topCriticalResult, cycleResult, blastResult, pathResult,
  loading, isDark,
}: Props) {
  const [blastSource, setBlastSource] = useState('');
  const [blastHops, setBlastHops] = useState(3);
  const [pathSource, setPathSource] = useState('internet');
  const [pathTarget, setPathTarget] = useState('prod-database');
  const [topCount, setTopCount] = useState(3);
  const [expanded, setExpanded] = useState<string | null>('blast');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const sectionClass = `rounded-xl border transition-all duration-300 overflow-hidden
    ${isDark ? 'bg-slate-900/50 border-slate-700/50 hover:border-slate-600/50' : 'bg-white border-slate-200 hover:border-slate-300'}`;
  const headerClass = `flex items-center justify-between w-full px-4 py-3 cursor-pointer transition-colors
    ${isDark ? 'hover:bg-slate-800/50' : 'hover:bg-slate-50'}`;
  const labelClass = `text-xs font-medium ${isDark ? 'text-slate-400' : 'text-slate-500'}`;
  const selectClass = `w-full px-3 py-2 rounded-lg text-sm border transition-colors
    ${isDark
      ? 'bg-slate-800 border-slate-700 text-slate-200 focus:border-blue-500'
      : 'bg-white border-slate-200 text-slate-700 focus:border-blue-500'} 
    outline-none focus:ring-1 focus:ring-blue-500/30`;

  const toggle = (id: string) => setExpanded(prev => prev === id ? null : id);

  return (
    <div className="space-y-3 p-4 overflow-y-auto h-full">
      {/* Title */}
      <div className="flex items-center justify-between mb-2">
        <h2 className={`text-sm font-bold uppercase tracking-wider ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
          ⚡ Analysis Tools
        </h2>
        <div className="flex gap-1.5">
          <button
            onClick={() => fileInputRef.current?.click()}
            className={`p-2 rounded-lg text-xs transition-colors ${isDark ? 'bg-slate-800 hover:bg-slate-700 text-slate-300' : 'bg-slate-100 hover:bg-slate-200 text-slate-600'}`}
            title="Upload Custom Graph"
          >
            <Upload className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={onReset}
            className={`p-2 rounded-lg text-xs transition-colors ${isDark ? 'bg-slate-800 hover:bg-slate-700 text-slate-300' : 'bg-slate-100 hover:bg-slate-200 text-slate-600'}`}
            title="Reset Graph"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept=".json"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) onUpload(f);
            e.target.value = '';
          }}
        />
      </div>

      {/* 1. Blast Radius */}
      <div className={sectionClass}>
        <button onClick={() => toggle('blast')} className={headerClass}>
          <span className="flex items-center gap-2">
            <Crosshair className="w-4 h-4 text-red-400" />
            <span className={`text-sm font-semibold ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>Blast Radius (BFS)</span>
          </span>
          {expanded === 'blast' ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
        </button>
        <AnimatePresence>
          {expanded === 'blast' && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="px-4 pb-4 space-y-3"
            >
              <p className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                Find all nodes reachable within N hops from a compromised node.
              </p>
              <div>
                <label className={labelClass}>Source Node</label>
                <select value={blastSource} onChange={e => setBlastSource(e.target.value)} className={selectClass}>
                  <option value="">Select a node...</option>
                  {nodes.map(n => (
                    <option key={n.id} value={n.id}>{n.label} ({n.type})</option>
                  ))}
                </select>
              </div>
              <div>
                <label className={labelClass}>Max Hops: {blastHops}</label>
                <input
                  type="range"
                  min={1}
                  max={8}
                  value={blastHops}
                  onChange={e => setBlastHops(Number(e.target.value))}
                  className="w-full h-1.5 rounded-full appearance-none cursor-pointer bg-slate-700 accent-red-500"
                />
                <div className="flex justify-between text-[10px] text-slate-500 mt-0.5">
                  <span>1</span><span>4</span><span>8</span>
                </div>
              </div>
              <button
                disabled={!blastSource || loading}
                onClick={() => onBlastRadius(blastSource, blastHops)}
                className="w-full py-2.5 rounded-lg text-sm font-medium transition-all
                  bg-gradient-to-r from-red-600 to-orange-600 text-white
                  hover:from-red-500 hover:to-orange-500 disabled:opacity-40 disabled:cursor-not-allowed
                  hover:shadow-lg hover:shadow-red-500/20 active:scale-[0.98]"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : 'Analyze Blast Radius'}
              </button>
              {/* Result */}
              {blastResult && (
                <motion.div
                  initial={{ y: 10, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  className={`p-3 rounded-lg border text-xs space-y-2
                    ${blastResult.risk_summary === 'CRITICAL' ? (isDark ? 'bg-red-950/30 border-red-900/40' : 'bg-red-50 border-red-200') : (isDark ? 'bg-amber-950/30 border-amber-900/40' : 'bg-amber-50 border-amber-200')}`}
                >
                  <div className="flex items-center justify-between">
                    <span className={`font-bold ${blastResult.risk_summary === 'CRITICAL' ? 'text-red-400' : 'text-amber-400'}`}>
                      {blastResult.risk_summary} RISK
                    </span>
                    <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>{blastResult.total_affected} nodes affected</span>
                  </div>
                  {blastResult.crown_jewels_reached > 0 && (
                    <p className="text-red-400">
                      ⚠️ {blastResult.crown_jewels_reached} Crown Jewel(s) reachable: {blastResult.crown_jewel_names.join(', ')}
                    </p>
                  )}
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* 2. Shortest Attack Path */}
      <div className={sectionClass}>
        <button onClick={() => toggle('path')} className={headerClass}>
          <span className="flex items-center gap-2">
            <Route className="w-4 h-4 text-blue-400" />
            <span className={`text-sm font-semibold ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>Attack Path (Dijkstra)</span>
          </span>
          {expanded === 'path' ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
        </button>
        <AnimatePresence>
          {expanded === 'path' && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="px-4 pb-4 space-y-3"
            >
              <p className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                Find the easiest attack path using CVSS-weighted edges.
              </p>
              <div>
                <label className={labelClass}>Source (Attacker Entry)</label>
                <select value={pathSource} onChange={e => setPathSource(e.target.value)} className={selectClass}>
                  {nodes.map(n => (
                    <option key={n.id} value={n.id}>{n.label} ({n.type})</option>
                  ))}
                </select>
              </div>
              <div>
                <label className={labelClass}>Target (Crown Jewel)</label>
                <select value={pathTarget} onChange={e => setPathTarget(e.target.value)} className={selectClass}>
                  {nodes.map(n => (
                    <option key={n.id} value={n.id}>{n.label} ({n.type})</option>
                  ))}
                </select>
              </div>
              <button
                disabled={!pathSource || !pathTarget || loading}
                onClick={() => onShortestPath(pathSource, pathTarget)}
                className="w-full py-2.5 rounded-lg text-sm font-medium transition-all
                  bg-gradient-to-r from-blue-600 to-cyan-600 text-white
                  hover:from-blue-500 hover:to-cyan-500 disabled:opacity-40 disabled:cursor-not-allowed
                  hover:shadow-lg hover:shadow-blue-500/20 active:scale-[0.98]"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : 'Find Shortest Path'}
              </button>
              {pathResult && pathResult.path_exists && (
                <motion.div
                  initial={{ y: 10, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  className={`p-3 rounded-lg border text-xs space-y-2 ${isDark ? 'bg-blue-950/30 border-blue-900/40' : 'bg-blue-50 border-blue-200'}`}
                >
                  <div className="flex items-center justify-between">
                    <span className={`font-bold ${pathResult.difficulty === 'TRIVIAL' || pathResult.difficulty === 'EASY' ? 'text-red-400' : 'text-blue-400'}`}>
                      {pathResult.difficulty} Attack
                    </span>
                    <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>
                      {pathResult.hop_count} hops • Weight: {pathResult.total_weight}
                    </span>
                  </div>
                  <div className={`flex flex-wrap items-center gap-1 ${isDark ? 'text-slate-300' : 'text-slate-600'}`}>
                    {pathResult.path.map((p, i) => (
                      <span key={p} className="flex items-center gap-1">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono ${isDark ? 'bg-slate-800' : 'bg-slate-200'}`}>{p}</span>
                        {i < pathResult.path.length - 1 && <span className="text-red-400">→</span>}
                      </span>
                    ))}
                  </div>
                  <button
                    onClick={onShowKillChain}
                    className="w-full mt-2 py-2 rounded-lg text-xs font-medium transition-all
                      bg-gradient-to-r from-purple-600 to-pink-600 text-white
                      hover:from-purple-500 hover:to-pink-500 hover:shadow-lg hover:shadow-purple-500/20"
                  >
                    📋 View Kill Chain Report
                  </button>
                </motion.div>
              )}
              {pathResult && !pathResult.path_exists && (
                <motion.div initial={{ y: 10, opacity: 0 }} animate={{ y: 0, opacity: 1 }}
                  className={`p-3 rounded-lg border text-xs ${isDark ? 'bg-green-950/30 border-green-900/40 text-green-400' : 'bg-green-50 border-green-200 text-green-700'}`}>
                  ✅ No attack path exists between these nodes.
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* 3. Cycle Detection */}
      <div className={sectionClass}>
        <button onClick={() => toggle('cycles')} className={headerClass}>
          <span className="flex items-center gap-2">
            <RefreshCcw className="w-4 h-4 text-amber-400" />
            <span className={`text-sm font-semibold ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>Cycle Detection (DFS)</span>
          </span>
          {expanded === 'cycles' ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
        </button>
        <AnimatePresence>
          {expanded === 'cycles' && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="px-4 pb-4 space-y-3"
            >
              <p className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                Detect circular permission loops in the RBAC graph.
              </p>
              <button
                disabled={loading}
                onClick={onDetectCycles}
                className="w-full py-2.5 rounded-lg text-sm font-medium transition-all
                  bg-gradient-to-r from-amber-600 to-yellow-600 text-white
                  hover:from-amber-500 hover:to-yellow-500 disabled:opacity-40 disabled:cursor-not-allowed
                  hover:shadow-lg hover:shadow-amber-500/20 active:scale-[0.98]"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : 'Detect Cycles'}
              </button>
              {cycleResult && (
                <motion.div
                  initial={{ y: 10, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  className={`p-3 rounded-lg border text-xs space-y-2 ${cycleResult.has_cycles ? (isDark ? 'bg-amber-950/30 border-amber-900/40' : 'bg-amber-50 border-amber-200') : (isDark ? 'bg-green-950/30 border-green-900/40' : 'bg-green-50 border-green-200')}`}
                >
                  {cycleResult.has_cycles ? (
                    <>
                      <span className="font-bold text-amber-400">⚠️ {cycleResult.total_cycles} cycle(s) found</span>
                      {cycleResult.cycles.map((c, i) => (
                        <div key={i} className={`p-2 rounded text-[11px] ${isDark ? 'bg-slate-800/50' : 'bg-slate-100'}`}>
                          <span className={`font-medium ${c.risk === 'CRITICAL' ? 'text-red-400' : 'text-amber-400'}`}>[{c.risk}]</span>{' '}
                          <span className={isDark ? 'text-slate-300' : 'text-slate-600'}>{c.description}</span>
                        </div>
                      ))}
                    </>
                  ) : (
                    <span className="text-green-400">✅ No circular permission loops detected.</span>
                  )}
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* 4. Top Critical Attack Paths */}
      <div className={sectionClass}>
        <button onClick={() => toggle('topCritical')} className={headerClass}>
          <span className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-red-500" />
            <span className={`text-sm font-semibold ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>Top Critical Paths</span>
          </span>
          {expanded === 'topCritical' ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
        </button>
        <AnimatePresence>
          {expanded === 'topCritical' && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="px-4 pb-4 space-y-3"
            >
              <p className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                Identify and analyze the most critical attack paths with mitigation suggestions.
              </p>
              <div>
                <label className={labelClass}>Number of Paths: {topCount}</label>
                <input
                  type="range"
                  min={1}
                  max={topCriticalResult?.total_paths_found ?? 10}
                  value={topCount}
                  onChange={e => setTopCount(Number(e.target.value))}
                  className="w-full h-1.5 rounded-full appearance-none cursor-pointer bg-slate-700 accent-red-500"
                />
                <div className="flex justify-between text-[10px] text-slate-500 mt-0.5">
                  <span>1</span><span>{Math.ceil((topCriticalResult?.total_paths_found ?? 10) / 2)}</span><span>{topCriticalResult?.total_paths_found ?? 10}</span>
                </div>
              </div>
              <button
                disabled={loading}
                onClick={() => onTopCriticalPaths(topCount)}
                className="w-full py-2.5 rounded-lg text-sm font-medium transition-all
                  bg-gradient-to-r from-red-600 to-pink-600 text-white
                  hover:from-red-500 hover:to-pink-500 disabled:opacity-40 disabled:cursor-not-allowed
                  hover:shadow-lg hover:shadow-red-500/20 active:scale-[0.98]"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : 'Analyze Critical Paths'}
              </button>
              {topCriticalResult && topCriticalResult.top_critical_paths.length > 0 && (
                <motion.div
                  initial={{ y: 10, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  className={`p-3 rounded-lg border text-xs space-y-2 ${isDark ? 'bg-red-950/30 border-red-900/40' : 'bg-red-50 border-red-200'}`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-red-400">🚨 {topCriticalResult.top_critical_paths.length} Critical Path(s)</span>
                    <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Total: {topCriticalResult.total_paths_found}</span>
                  </div>
                  {topCriticalResult.top_critical_paths.map((path, i) => (
                    <motion.div
                      key={i}
                      onClick={() => onSelectCriticalPath(path)}
                      whileHover={{ scale: 1.02 }}
                      className={`p-2 rounded text-[10px] space-y-1 cursor-pointer transition-all ${
                        isDark
                          ? 'bg-slate-800/50 hover:bg-slate-700/70 border border-slate-700/30 hover:border-red-500/50'
                          : 'bg-slate-100 hover:bg-slate-200 border border-slate-300/30 hover:border-red-400/50'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-red-400">#{path.rank}: {path.difficulty}</span>
                        <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Weight: {path.total_weight}</span>
                      </div>
                      <p className={isDark ? 'text-slate-300' : 'text-slate-600'} style={{ wordBreak: 'break-word' }}>
                        {path.description.substring(0, 120)}...
                      </p>
                      {path.mitigation_suggestions.length > 0 && (
                        <div className={`mt-1 pt-1 border-t ${isDark ? 'border-slate-700' : 'border-slate-200'}`}>
                          <span className={`font-semibold ${isDark ? 'text-green-400' : 'text-green-600'}`}>💡 Mitigation:</span>
                          <p className={isDark ? 'text-slate-400' : 'text-slate-500'} style={{ wordBreak: 'break-word' }}>
                            {path.mitigation_suggestions[0]}
                          </p>
                        </div>
                      )}
                    </motion.div>
                  ))}
                </motion.div>
              )}
              {topCriticalResult && topCriticalResult.top_critical_paths.length === 0 && (
                <motion.div initial={{ y: 10, opacity: 0 }} animate={{ y: 0, opacity: 1 }}
                  className={`p-3 rounded-lg border text-xs ${isDark ? 'bg-green-950/30 border-green-900/40 text-green-400' : 'bg-green-50 border-green-200 text-green-700'}`}>
                  ✅ No critical attack paths found from entry points to crown jewels.
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* 5. Critical Node */}
      <div className={sectionClass}>
        <button onClick={() => toggle('critical')} className={headerClass}>
          <span className="flex items-center gap-2">
            <Target className="w-4 h-4 text-purple-400" />
            <span className={`text-sm font-semibold ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>Critical Node Analysis</span>
          </span>
          {expanded === 'critical' ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
        </button>
        <AnimatePresence>
          {expanded === 'critical' && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="px-4 pb-4 space-y-3"
            >
              <p className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                Find the single node whose removal breaks the most attack paths.
              </p>
              <button
                disabled={loading}
                onClick={onCriticalNode}
                className="w-full py-2.5 rounded-lg text-sm font-medium transition-all
                  bg-gradient-to-r from-purple-600 to-violet-600 text-white
                  hover:from-purple-500 hover:to-violet-500 disabled:opacity-40 disabled:cursor-not-allowed
                  hover:shadow-lg hover:shadow-purple-500/20 active:scale-[0.98]"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : 'Identify Critical Node'}
              </button>
              {criticalNodeResult?.critical_node && (
                <motion.div
                  initial={{ y: 10, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  className={`space-y-3`}
                >
                  <div className={`p-3 rounded-lg border text-xs space-y-2 ${isDark ? 'bg-purple-950/30 border-purple-900/40' : 'bg-purple-50 border-purple-200'}`}>
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-purple-400">🎯 {criticalNodeResult.critical_node.label}</span>
                      <span className={`font-bold ${criticalNodeResult.critical_node.impact_percentage > 50 ? 'text-red-400' : 'text-amber-400'}`}>
                        {criticalNodeResult.critical_node.impact_percentage}% Impact
                      </span>
                    </div>
                    <p className={isDark ? 'text-slate-400' : 'text-slate-500'}>
                      Removing this node breaks {criticalNodeResult.critical_node.paths_broken}/{criticalNodeResult.baseline_paths} attack paths
                    </p>
                    <p className={isDark ? 'text-slate-300' : 'text-slate-600'}>
                      💡 {criticalNodeResult.recommendation}
                    </p>
                  </div>

                  {/* Top 5 */}
                  <div className={`p-3 rounded-lg ${isDark ? 'bg-slate-800/50' : 'bg-slate-50'}`}>
                    <span className={`text-xs font-semibold ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Top Remediation Targets</span>
                    {criticalNodeResult.top_5_nodes.map((n, i) => (
                      <div key={n.node_id} className={`flex items-center justify-between py-1.5 text-xs ${i > 0 ? (isDark ? 'border-t border-slate-700/50' : 'border-t border-slate-200') : 'mt-1'}`}>
                        <span className={isDark ? 'text-slate-300' : 'text-slate-600'}>
                          {i + 1}. {n.label}
                        </span>
                        <div className="flex items-center gap-2">
                          <div className={`w-16 h-1.5 rounded-full overflow-hidden ${isDark ? 'bg-slate-700' : 'bg-slate-200'}`}>
                            <div
                              className="h-full rounded-full bg-gradient-to-r from-purple-500 to-red-500"
                              style={{ width: `${n.impact_percentage}%` }}
                            />
                          </div>
                          <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>{n.impact_percentage}%</span>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Remediate Button */}
                  <button
                    onClick={() => onRemediate(criticalNodeResult.critical_node!.node_id)}
                    className="w-full py-2.5 rounded-lg text-sm font-medium transition-all
                      bg-gradient-to-r from-green-600 to-emerald-600 text-white
                      hover:from-green-500 hover:to-emerald-500
                      hover:shadow-lg hover:shadow-green-500/20 active:scale-[0.98]
                      flex items-center justify-center gap-2"
                  >
                    <Shield className="w-4 h-4" />
                    Remediate: Remove {criticalNodeResult.critical_node.label}
                  </button>
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
