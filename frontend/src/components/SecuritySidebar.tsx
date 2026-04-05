import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield, AlertTriangle, Database, Key, Server, Globe, Link2, User,
  Cpu, Activity, HardDrive, FileText, ShieldOff, ShieldAlert, Network, Monitor,
  X, Crosshair, Route, ChevronRight, Zap, Lightbulb, Loader2
} from 'lucide-react';
import type { GraphNode, GraphEdge, TopCriticalPath } from '@/lib/types';

interface Props {
  node: GraphNode | null;
  edge: GraphEdge | null;
  criticalPath: TopCriticalPath | null;
  onClose: () => void;
  onBlastRadius: (nodeId: string) => void;
  onFindPath: (target: string) => void;
  isDark: boolean;
}

const ICON_MAP: Record<string, React.ReactNode> = {
  globe: <Globe className="w-5 h-5" />,
  network: <Network className="w-5 h-5" />,
  monitor: <Monitor className="w-5 h-5" />,
  server: <Server className="w-5 h-5" />,
  'user-check': <User className="w-5 h-5" />,
  user: <User className="w-5 h-5" />,
  link: <Link2 className="w-5 h-5" />,
  shield: <Shield className="w-5 h-5" />,
  'shield-alert': <ShieldAlert className="w-5 h-5" />,
  'shield-off': <ShieldOff className="w-5 h-5" />,
  key: <Key className="w-5 h-5" />,
  database: <Database className="w-5 h-5" />,
  cpu: <Cpu className="w-5 h-5" />,
  activity: <Activity className="w-5 h-5" />,
  'hard-drive': <HardDrive className="w-5 h-5" />,
  'file-text': <FileText className="w-5 h-5" />,
};

const RISK_BADGE: Record<string, { bg: string; text: string; label: string; glow?: string }> = {
  'crown-jewel': { bg: 'bg-yellow-500/20', text: 'text-yellow-400', label: '👑 Crown Jewel', glow: 'glow-gold' },
  'critical': { bg: 'bg-red-500/20', text: 'text-red-400', label: '🔴 Critical', glow: 'glow-red' },
  'high': { bg: 'bg-orange-500/20', text: 'text-orange-400', label: '🟠 High' },
  'medium': { bg: 'bg-amber-500/20', text: 'text-amber-400', label: '🟡 Medium' },
  'low': { bg: 'bg-green-500/20', text: 'text-green-400', label: '🟢 Low' },
  'entry-point': { bg: 'bg-green-500/20', text: 'text-green-400', label: '🌐 Entry Point', glow: 'glow-green' },
  'info': { bg: 'bg-slate-500/20', text: 'text-slate-400', label: 'ℹ️ Info' },
};

export default function SecuritySidebar({ node, edge, criticalPath, onClose, onBlastRadius, onFindPath, isDark }: Props) {
  const [aiSuggestion, setAiSuggestion] = useState<string | null>(null);
  const [isAiLoading, setIsAiLoading] = useState(false);

  const handleAskAI = async (nodeId: string) => {
    if (isAiLoading) return;
    setIsAiLoading(true);
    setAiSuggestion(null);
    try {
      const res = await fetch('http://localhost:8000/api/ai-remediation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ node_id: nodeId })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to fetch AI advice');
      setAiSuggestion(data.advice);
    } catch (err: any) {
      setAiSuggestion(`❌ **Error:** ${err.message}`);
    } finally {
      setIsAiLoading(false);
    }
  };

  const handleClose = () => {
    setAiSuggestion(null);
    setIsAiLoading(false);
    onClose();
  };

  if (!node && !edge && !criticalPath) return null;

  // If showing critical path
  if (criticalPath) {
    return (
      <AnimatePresence>
        <motion.div
          initial={{ x: 400, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 400, opacity: 0 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          className={`absolute top-0 right-0 w-[380px] h-full z-30 overflow-y-auto
            ${isDark 
              ? 'bg-slate-900/95 border-l border-slate-700/50' 
              : 'bg-white/95 border-l border-slate-200'}
            backdrop-blur-xl`}
        >
          {/* Header */}
          <div className={`sticky top-0 z-10 px-5 py-4 border-b backdrop-blur-xl
            ${isDark ? 'border-slate-700/50 bg-slate-900/90' : 'border-slate-200 bg-white/90'}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${isDark ? 'bg-slate-800' : 'bg-slate-100'} glow-red`}>
                  <Route className="w-5 h-5 text-red-400" />
                </div>
                <div>
                  <h3 className={`font-semibold text-sm ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>
                    Attack Path #{criticalPath.rank}
                  </h3>
                  <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                    {criticalPath.difficulty} Risk
                  </p>
                </div>
              </div>
              <button
                onClick={handleClose}
                className={`p-1.5 rounded-lg transition-colors ${isDark ? 'hover:bg-slate-800 text-slate-400' : 'hover:bg-slate-100 text-slate-500'}`}
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="px-5 py-4 space-y-5">
            {/* Difficulty Badge */}
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              className={`inline-flex px-3 py-1.5 rounded-full text-xs font-medium
                ${criticalPath.difficulty === 'HARD' ? 'bg-red-500/20 text-red-400' :
                  criticalPath.difficulty === 'MODERATE' ? 'bg-orange-500/20 text-orange-400' :
                  'bg-yellow-500/20 text-yellow-400'}`}
            >
              📊 {criticalPath.difficulty} Difficulty
            </motion.div>

            {/* Path Stats */}
            <div className={`grid grid-cols-2 gap-3 p-3 rounded-xl ${isDark ? 'bg-slate-800/50' : 'bg-slate-50'}`}>
              <div>
                <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Hop Count</span>
                <p className={`text-sm font-medium ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>{criticalPath.hop_count}</p>
              </div>
              <div>
                <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Total Weight</span>
                <p className={`text-sm font-medium ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>{criticalPath.total_weight.toFixed(2)}</p>
              </div>
              <div>
                <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Vulnerabilities</span>
                <p className="text-sm font-medium text-red-400">⚠️ {criticalPath.vulnerabilities_found}</p>
              </div>
              <div>
                <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Criticality</span>
                <p className="text-sm font-medium text-amber-400">🎯 {criticalPath.criticality_score.toFixed(1)}</p>
              </div>
            </div>

            {/* Full Description */}
            <div>
              <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                Attack Description
              </h4>
              <p className={`text-sm leading-relaxed ${isDark ? 'text-slate-300' : 'text-slate-600'}`}>
                {criticalPath.description}
              </p>
            </div>

            {/* Attack Path */}
            <div>
              <h4 className={`text-xs font-semibold uppercase tracking-wider mb-3 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                📍 Attack Path ({criticalPath.path.length} nodes)
              </h4>
              <div className="space-y-2">
                {criticalPath.path.map((nodeId, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <div className={`px-2 py-1 rounded text-xs font-mono font-medium
                      ${idx === 0 ? 'bg-green-500/20 text-green-400' :
                        idx === criticalPath.path.length - 1 ? 'bg-yellow-500/20 text-yellow-400' :
                        isDark ? 'bg-slate-800 text-cyan-400' : 'bg-slate-100 text-blue-600'}`}>
                      {nodeId}
                    </div>
                    {idx < criticalPath.path.length - 1 && (
                      <ChevronRight className={`w-4 h-4 ${isDark ? 'text-slate-600' : 'text-slate-300'}`} />
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Risk Factors */}
            {criticalPath.risk_factors.length > 0 && (
              <div>
                <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 flex items-center gap-1.5 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                  <AlertTriangle className="w-3.5 h-3.5 text-red-400" />
                  Risk Factors
                </h4>
                <div className="space-y-1">
                  {criticalPath.risk_factors.map((factor, i) => (
                    <div key={i} className={`text-xs p-2 rounded ${isDark ? 'bg-red-950/30 text-red-300' : 'bg-red-50 text-red-700'}`}>
                      • {factor}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Mitigation Suggestions */}
            {criticalPath.mitigation_suggestions.length > 0 && (
              <div>
                <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 flex items-center gap-1.5 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                  <Zap className="w-3.5 h-3.5 text-green-400" />
                  Mitigation Suggestions
                </h4>
                <div className="space-y-2">
                  {criticalPath.mitigation_suggestions.map((suggestion, i) => (
                    <motion.div
                      key={i}
                      initial={{ x: -20, opacity: 0 }}
                      animate={{ x: 0, opacity: 1 }}
                      transition={{ delay: i * 0.1 }}
                      className={`flex gap-2 p-2.5 rounded-lg text-xs ${isDark ? 'bg-green-950/30 border border-green-900/30 text-green-300' : 'bg-green-50 border border-green-200 text-green-700'}`}
                    >
                      <span className="font-bold shrink-0">{i + 1}.</span>
                      <span>{suggestion}</span>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </motion.div>
      </AnimatePresence>
    );
  }

  // Original node display logic
  if (node) {
    const risk = RISK_BADGE[node.risk_level] || RISK_BADGE.info;
    const icon = ICON_MAP[node.metadata?.icon || ''] || <Server className="w-5 h-5" />;
    const cves = node.metadata?.cves || [];
    const cvssScores = node.metadata?.cvss_scores || [];

    return (
      <AnimatePresence>
        <motion.div
          initial={{ x: 400, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 400, opacity: 0 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          className={`absolute top-0 right-0 w-[380px] h-full z-30 overflow-y-auto
            ${isDark 
              ? 'bg-slate-900/95 border-l border-slate-700/50' 
              : 'bg-white/95 border-l border-slate-200'}
            backdrop-blur-xl`}
        >
          {/* Header */}
          <div className={`sticky top-0 z-10 px-5 py-4 border-b backdrop-blur-xl
            ${isDark ? 'border-slate-700/50 bg-slate-900/90' : 'border-slate-200 bg-white/90'}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${isDark ? 'bg-slate-800' : 'bg-slate-100'}
                  ${node.risk_level === 'critical' ? 'glow-red' : node.risk_level === 'crown-jewel' ? 'glow-gold' : ''}`}>
                  {icon}
                </div>
                <div>
                  <h3 className={`font-semibold text-sm ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>
                    {node.label}
                  </h3>
                  <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                    {node.type.toUpperCase()}
                  </p>
                </div>
              </div>
              <button
                onClick={handleClose}
                className={`p-1.5 rounded-lg transition-colors ${isDark ? 'hover:bg-slate-800 text-slate-400' : 'hover:bg-slate-100 text-slate-500'}`}
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="px-5 py-4 space-y-5">
            {/* Risk Badge */}
            <motion.div initial={{ scale: 0.9 }} animate={{ scale: 1 }} className={`inline-flex px-3 py-1.5 rounded-full text-xs font-medium ${risk.bg} ${risk.text} ${risk.glow || ''}`}>
              {risk.label}
            </motion.div>

            {/* Description */}
            {node.metadata?.description && (
              <div>
                <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                  Description
                </h4>
                <p className={`text-sm leading-relaxed ${isDark ? 'text-slate-300' : 'text-slate-600'}`}>
                  {node.metadata.description}
                </p>
              </div>
            )}

            {/* Properties */}
            <div className={`grid grid-cols-2 gap-3 p-3 rounded-xl ${isDark ? 'bg-slate-800/50' : 'bg-slate-50'}`}>
              <div>
                <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Namespace</span>
                <p className={`text-sm font-medium ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>{node.namespace}</p>
              </div>
              <div>
                <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Type</span>
                <p className={`text-sm font-medium ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>{node.type}</p>
              </div>
              {!node.metadata?.containers && node.metadata?.image && (
                <div className="col-span-2">
                  <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Image</span>
                  <p className={`text-xs font-mono break-all ${isDark ? 'text-cyan-400' : 'text-blue-600'}`}>{node.metadata.image}</p>
                </div>
              )}
              {node.metadata?.version && (
                <div>
                  <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Version</span>
                  <p className={`text-sm font-medium ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>{node.metadata.version}</p>
                </div>
              )}
              {!node.metadata?.containers && node.metadata?.ports && node.metadata.ports.length > 0 && (
                <div>
                  <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Ports</span>
                  <p className={`text-sm font-medium ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>{node.metadata.ports.join(', ')}</p>
                </div>
              )}
              {node.metadata?.engine && (
                <div className="col-span-2">
                  <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Engine</span>
                  <p className={`text-sm font-medium ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>{node.metadata.engine}</p>
                </div>
              )}
              {node.metadata?.records && (
                <div className="col-span-2">
                  <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Data Volume</span>
                  <p className={`text-sm font-medium text-amber-400`}>{node.metadata.records}</p>
                </div>
              )}
              {node.metadata?.data_classification && (
                <div className="col-span-2">
                  <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Classification</span>
                  <p className="text-sm font-medium text-red-400">⚠️ {node.metadata.data_classification}</p>
                </div>
              )}
            </div>

            {/* Detailed Containers */}
            {node.metadata?.containers && (node.metadata.containers as any[]).length > 0 && (
              <div>
                <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 flex items-center gap-1.5 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                  <Cpu className="w-3.5 h-3.5" />
                  Containers ({(node.metadata.containers as any[]).length})
                </h4>
                <div className="space-y-2">
                  {(node.metadata.containers as any[]).map((c, i) => (
                    <div key={i} className={`p-3 rounded-xl border ${isDark ? 'bg-slate-800/80 border-slate-700/50' : 'bg-white border-slate-200'} shadow-sm`}>
                      <div className="flex items-center justify-between mb-1">
                        <span className={`text-xs font-bold ${isDark ? 'text-cyan-400' : 'text-blue-600'}`}>{c.name}</span>
                        {c.score !== undefined && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-500/10 text-red-400 font-bold">
                            Risk: {c.score}
                          </span>
                        )}
                      </div>
                      <p className={`text-[10px] font-mono break-all mb-1 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>{c.image}</p>
                      {c.ports && c.ports.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1">
                          {c.ports.map((p: number) => (
                            <span key={p} className={`text-[9px] px-1.5 py-0.5 rounded ${isDark ? 'bg-slate-700 text-slate-300' : 'bg-slate-100 text-slate-600'}`}>
                              Port {p}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* CVEs */}
            {cves.length > 0 && (
              <div>
                <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 flex items-center gap-1.5 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                  <AlertTriangle className="w-3.5 h-3.5 text-red-400" />
                  Vulnerabilities ({cves.length})
                </h4>
                <div className="space-y-2">
                  {cves.map((cve, i) => (
                    <motion.div
                      key={cve}
                      initial={{ x: -20, opacity: 0 }}
                      animate={{ x: 0, opacity: 1 }}
                      transition={{ delay: i * 0.1 }}
                      className={`flex items-center justify-between p-2.5 rounded-lg ${isDark ? 'bg-red-950/30 border border-red-900/30' : 'bg-red-50 border border-red-200'}`}
                    >
                      <span className={`text-xs font-mono font-medium ${isDark ? 'text-red-300' : 'text-red-700'}`}>{cve}</span>
                      {cvssScores[i] !== undefined && (
                        <span className={`text-xs font-bold px-2 py-0.5 rounded ${cvssScores[i]! >= 7 ? 'bg-red-500/20 text-red-400' : 'bg-amber-500/20 text-amber-400'}`}>
                          CVSS {cvssScores[i]}
                        </span>
                      )}
                    </motion.div>
                  ))}
                </div>
              </div>
            )}

            {/* RBAC Rules */}
            {node.metadata?.rules && (
              <div>
                <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                  RBAC Rules
                </h4>
                <div className="space-y-1">
                  {(node.metadata.rules as string[]).map((rule, i) => (
                    <div key={i} className={`text-xs font-mono p-2 rounded ${isDark ? 'bg-slate-800 text-cyan-400' : 'bg-slate-100 text-blue-600'}`}>
                      {rule}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Secret Keys */}
            {node.metadata?.keys && (
              <div>
                <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                  Secret Keys
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {(node.metadata.keys as string[]).map((key) => (
                    <span key={key} className={`text-xs font-mono px-2 py-1 rounded ${isDark ? 'bg-amber-900/30 text-amber-300 border border-amber-800/30' : 'bg-amber-50 text-amber-700 border border-amber-200'}`}>
                      {key}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Labels */}
            {node.metadata?.labels && Object.keys(node.metadata.labels).length > 0 && (
              <div>
                <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                  Labels
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {Object.entries(node.metadata.labels).map(([k, v]) => (
                    <span key={k} className={`text-xs font-mono px-2 py-1 rounded ${isDark ? 'bg-slate-800 text-slate-300' : 'bg-slate-100 text-slate-600'}`}>
                      {k}={v}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="space-y-2 pt-2">
              <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                Analysis Actions
              </h4>
              <button
                onClick={() => onBlastRadius(node.id)}
                className="w-full flex items-center justify-between px-4 py-3 rounded-xl text-sm font-medium transition-all
                  bg-gradient-to-r from-red-600 to-orange-600 text-white hover:from-red-500 hover:to-orange-500
                  hover:shadow-lg hover:shadow-red-500/20 active:scale-[0.98]"
              >
                <span className="flex items-center gap-2">
                  <Crosshair className="w-4 h-4" />
                  Run Blast Radius
                </span>
                <ChevronRight className="w-4 h-4" />
              </button>
              <button
                onClick={() => onFindPath(node.id)}
                className={`w-full flex items-center justify-between px-4 py-3 rounded-xl text-sm font-medium transition-all
                  ${isDark 
                    ? 'bg-slate-800 text-slate-200 hover:bg-slate-700 border border-slate-700' 
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200'}
                  hover:shadow-lg active:scale-[0.98]`}
              >
                <span className="flex items-center gap-2">
                  <Route className="w-4 h-4" />
                  Find Attack Path to This Node
                </span>
                <ChevronRight className="w-4 h-4" />
              </button>
              <button
                onClick={() => handleAskAI(node.id)}
                disabled={isAiLoading}
                className={`w-full flex items-center justify-between px-4 py-3 rounded-xl text-sm font-medium transition-all
                  ${isDark 
                    ? 'bg-indigo-900/40 text-indigo-300 hover:bg-indigo-800/60 border border-indigo-700/50' 
                    : 'bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200'}
                  hover:shadow-lg active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                <span className="flex items-center gap-2">
                  {isAiLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Lightbulb className="w-4 h-4" />}
                  {isAiLoading ? 'Analyzing Context...' : 'Ask AI Advisor'}
                </span>
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>

            {/* AI Suggestion Box */}
            <AnimatePresence>
              {aiSuggestion && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 10 }}
                  className={`mt-4 p-4 rounded-xl border z-20 relative overflow-hidden
                    ${isDark ? 'bg-indigo-950/40 border-indigo-500/30' : 'bg-indigo-50/80 border-indigo-200'} shadow-lg backdrop-blur-md`}
                >
                  <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 blur-3xl rounded-full" />
                  <div className="absolute bottom-0 left-0 w-24 h-24 bg-purple-500/10 blur-2xl rounded-full" />
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <Lightbulb className={`w-4 h-4 ${isDark ? 'text-indigo-400' : 'text-indigo-600'}`} />
                      <h4 className={`text-sm font-bold ${isDark ? 'text-indigo-300' : 'text-indigo-800'}`}>
                        AI Remediation Strategy
                      </h4>
                    </div>
                    <button onClick={() => setAiSuggestion(null)} className="text-indigo-400 hover:text-indigo-300"><X className="w-4 h-4" /></button>
                  </div>
                  <div className={`text-sm prose prose-sm max-w-none 
                    ${isDark ? 'prose-invert prose-p:text-indigo-200/90 prose-li:text-indigo-200/90 prose-strong:text-indigo-100' : 'prose-p:text-indigo-900 prose-li:text-indigo-900 prose-strong:text-indigo-800'}
                    pointer-events-auto`}
                  >
                    <ReactMarkdown>{aiSuggestion}</ReactMarkdown>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </motion.div>
      </AnimatePresence>
    );
  }

  // ── Edge Rendering Logic ────────────────
  if (edge) {
    const sourceLabel = typeof edge.source === 'string' ? edge.source : (edge.source as any).label || (edge.source as any).id;
    const targetLabel = typeof edge.target === 'string' ? edge.target : (edge.target as any).label || (edge.target as any).id;

    return (
      <AnimatePresence>
        <motion.div
          initial={{ x: 400, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 400, opacity: 0 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          className={`absolute top-0 right-0 w-[380px] h-full z-30 overflow-y-auto
            ${isDark 
              ? 'bg-slate-900/95 border-l border-slate-700/50' 
              : 'bg-white/95 border-l border-slate-200'}
            backdrop-blur-xl`}
        >
          {/* Header */}
          <div className={`sticky top-0 z-10 px-5 py-4 border-b backdrop-blur-xl
            ${isDark ? 'border-slate-700/50 bg-slate-900/90' : 'border-slate-200 bg-white/90'}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${isDark ? 'bg-slate-800' : 'bg-slate-100'} glow-blue`}>
                  <Link2 className="w-5 h-5 text-blue-400" />
                </div>
                <div>
                  <h3 className={`font-semibold text-sm ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>
                    Relationship
                  </h3>
                  <p className={`text-[10px] font-mono tracking-wider ${isDark ? 'text-blue-400' : 'text-blue-600'}`}>
                    {edge.relationship.toUpperCase()}
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                className={`p-1.5 rounded-lg transition-colors ${isDark ? 'hover:bg-slate-800 text-slate-400' : 'hover:bg-slate-100 text-slate-500'}`}
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="px-5 py-6 space-y-6">
            {/* Connection Visualizer */}
            <div className="flex items-center justify-between gap-4 p-4 rounded-2xl bg-gradient-to-br from-slate-800/30 to-slate-900/30 border border-slate-700/30">
              <div className="text-center flex-1 min-w-0">
                <p className={`text-[10px] mb-1 uppercase tracking-tighter ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Source</p>
                <p className={`text-xs font-bold truncate ${isDark ? 'text-white' : 'text-slate-900'}`}>{sourceLabel}</p>
              </div>
              <div className="flex flex-col items-center gap-1">
                <div className="w-12 h-px bg-slate-700 mt-2 relative">
                  <div className="absolute right-0 top-1/2 -translate-y-1/2 border-y-4 border-y-transparent border-l-4 border-l-slate-700" />
                </div>
              </div>
              <div className="text-center flex-1 min-w-0">
                <p className={`text-[10px] mb-1 uppercase tracking-tighter ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Target</p>
                <p className={`text-xs font-bold truncate ${isDark ? 'text-white' : 'text-slate-900'}`}>{targetLabel}</p>
              </div>
            </div>

            {/* Details */}
            <div className="space-y-4">
              <div>
                <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                  Relationship Type
                </h4>
                <div className={`p-3 rounded-xl text-sm font-mono ${isDark ? 'bg-slate-800 text-blue-400' : 'bg-slate-100 text-blue-600'}`}>
                  {edge.relationship}
                </div>
              </div>

              <div>
                <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                  Difficulty Weight
                </h4>
                <div className="flex items-center gap-3">
                  <div className={`flex-1 h-2 rounded-full ${isDark ? 'bg-slate-800' : 'bg-slate-200'} overflow-hidden`}>
                    <motion.div 
                      initial={{ width: 0 }}
                      animate={{ width: `${(1 - edge.weight / 5) * 100}%` }}
                      className="h-full bg-gradient-to-r from-blue-500 to-cyan-500"
                    />
                  </div>
                  <span className={`text-xs font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>
                    {edge.weight}
                  </span>
                </div>
                <p className={`text-[10px] mt-1.5 ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                  Lower weight represents an easier attack path/permission grant.
                </p>
              </div>

              {/* Edge Metadata */}
              {edge.metadata && Object.keys(edge.metadata).length > 0 && (
                <div>
                  <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                    Metadata
                  </h4>
                  <div className={`divide-y ${isDark ? 'divide-slate-700/50 bg-slate-800/40' : 'divide-slate-200 bg-slate-50'} rounded-xl border border-transparent overflow-hidden`}>
                    {Object.entries(edge.metadata).map(([k, v]) => (
                      <div key={k} className="p-3">
                        <span className={`text-[10px] uppercase tracking-wider ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>{k.replace(/_/g, ' ')}</span>
                        <p className={`text-sm ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>{String(v)}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Analysis Note */}
            <div className={`p-4 rounded-2xl border ${isDark ? 'bg-blue-900/10 border-blue-800/30 text-blue-300' : 'bg-blue-50 border-blue-200 text-blue-700'}`}>
              <div className="flex gap-3">
                <Activity className="w-4 h-4 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <p className="text-xs font-bold leading-none">Permission Trace</p>
                  <p className="text-[10px] leading-relaxed opacity-80">
                    This edge represents a {edge.relationship} relationship between {sourceLabel} and {targetLabel}. 
                    Attackers can leverage this path to traverse the cluster.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </AnimatePresence>
    );
  }

  return null;
}
