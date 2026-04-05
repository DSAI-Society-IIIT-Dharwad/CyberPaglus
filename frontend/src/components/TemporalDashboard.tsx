import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Clock, Shield, GitCompare, X, PlusCircle, MinusCircle, AlertTriangle, Route, ExternalLink, Activity, Loader2, Save } from 'lucide-react';
import { api } from '@/lib/api';
import type { SnapshotMetadata, TemporalDiffResult, GraphNode } from '@/lib/types';
import ReactMarkdown from 'react-markdown';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  isDark: boolean;
  refreshTrigger?: number; // Optional prop to force reload snapshots
}

export default function TemporalDashboard({ isOpen, onClose, isDark, refreshTrigger }: Props) {
  const [snapshots, setSnapshots] = useState<SnapshotMetadata[]>([]);
  const [selectedPath, setSelectedPath] = useState<string>('');
  const [diffResult, setDiffResult] = useState<TemporalDiffResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadSnapshots();
    } else {
      // Clear state when closed
      setDiffResult(null);
      setSelectedPath('');
      setError(null);
    }
  }, [isOpen, refreshTrigger]);

  const loadSnapshots = async () => {
    setLoading(true);
    try {
      const res = await api.listSnapshots();
      setSnapshots(res.snapshots);
    } catch (err: any) {
      setError(err.message || 'Failed to load snapshots.');
    }
    setLoading(false);
  };

  const handleSaveSnapshot = async () => {
    setSaving(true);
    try {
      const label = prompt('Enter a label for this snapshot (optional):', 'baseline');
      if (label !== null) {
        await api.saveSnapshot(label);
        await loadSnapshots();
      }
    } catch (err: any) {
      setError(err.message || 'Failed to save snapshot.');
    }
    setSaving(false);
  };

  const handleDiff = async () => {
    if (!selectedPath) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.diffSnapshot(selectedPath);
      setDiffResult(res);
    } catch (err: any) {
      setError(err.message || 'Failed to compare snapshots.');
    }
    setLoading(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-6 pb-20 pointer-events-auto">
      {/* Backdrop */}
      <AnimatePresence>
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm"
        />
      </AnimatePresence>

      <AnimatePresence>
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className={`relative w-full max-w-5xl h-[85vh] flex flex-col rounded-2xl shadow-2xl overflow-hidden border
            ${isDark ? 'bg-slate-900 border-slate-700/50' : 'bg-white border-slate-200'}`}
        >
          {/* Header */}
          <div className={`shrink-0 flex items-center justify-between px-6 py-4 border-b
            ${isDark ? 'border-slate-800 bg-slate-900' : 'border-slate-100 bg-white'}`}>
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg ${isDark ? 'bg-indigo-500/20' : 'bg-indigo-100'}`}>
                <Clock className={`w-5 h-5 ${isDark ? 'text-indigo-400' : 'text-indigo-600'}`} />
              </div>
              <div>
                <h2 className={`text-lg font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>
                  Temporal Analysis (Time-Travel)
                </h2>
                <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                  Track infrastructure drift and security regressions over time.
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className={`p-2 rounded-lg transition-colors ${isDark ? 'hover:bg-slate-800 text-slate-400' : 'hover:bg-slate-100 text-slate-500'}`}
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="flex-1 overflow-hidden flex flex-col md:flex-row divide-y md:divide-y-0 md:divide-x border-slate-800">
            {/* Left Sidebar - Controls */}
            <div className={`shrink-0 w-full md:w-80 p-5 overflow-y-auto ${isDark ? 'bg-slate-900/50' : 'bg-slate-50'}`}>
              <button
                onClick={handleSaveSnapshot}
                disabled={saving}
                className={`w-full flex items-center justify-center gap-2 px-4 py-3 mb-6 rounded-xl text-sm font-semibold transition-all shadow-md active:scale-[0.98]
                  ${isDark ? 'bg-indigo-600 hover:bg-indigo-500 text-white' : 'bg-indigo-600 hover:bg-indigo-700 text-white'}
                  disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                Save Current Graph State
              </button>

              <h3 className={`text-xs font-semibold uppercase tracking-wider mb-3 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                Compare Against Baseline
              </h3>

              {snapshots.length === 0 ? (
                <div className={`p-4 rounded-xl text-center text-sm border border-dashed ${isDark ? 'border-slate-700 text-slate-500' : 'border-slate-300 text-slate-400'}`}>
                  No snapshots recorded yet.
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="space-y-1 relative">
                    <select
                      value={selectedPath}
                      onChange={(e) => setSelectedPath(e.target.value)}
                      className={`w-full p-3 rounded-lg text-sm border focus:outline-none focus:ring-2 appearance-none
                        ${isDark 
                          ? 'bg-slate-800 border-slate-700 text-slate-200 focus:border-indigo-500 focus:ring-indigo-500/20' 
                          : 'bg-white border-slate-200 text-slate-700 focus:border-indigo-500 focus:ring-indigo-500/20'}`}
                    >
                      <option value="" disabled>Select Baseline Snapshot...</option>
                      {snapshots.map(s => (
                        <option key={s.filepath} value={s.filepath}>
                          {new Date(s.timestamp).toLocaleString()} {s.label ? `- ${s.label}` : ''}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  <div className="flex justify-center my-2">
                    <div className={`p-1.5 rounded-full ${isDark ? 'bg-slate-800 border border-slate-700 text-slate-500' : 'bg-white border border-slate-200 text-slate-400'}`}>
                      <GitCompare className="w-4 h-4" />
                    </div>
                  </div>
                  
                  <div className={`w-full p-3 rounded-lg text-sm border text-center font-medium
                    ${isDark ? 'bg-slate-800/50 border-slate-700 text-slate-400' : 'bg-slate-100 border-slate-200 text-slate-500'}`}>
                    Live Active State
                  </div>

                  <button
                    onClick={handleDiff}
                    disabled={!selectedPath || loading}
                    className={`w-full flex items-center justify-center gap-2 mt-4 px-4 py-2.5 rounded-xl text-sm font-bold transition-all shadow-lg shadow-cyan-500/20 active:scale-[0.98]
                      bg-gradient-to-r from-cyan-600 to-blue-600 text-white hover:from-cyan-500 hover:to-blue-500
                      disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none`}
                  >
                    {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Activity className="w-4 h-4" />}
                    Analyze Risk Delta
                  </button>
                  
                  {error && (
                    <p className="mt-3 text-xs text-red-500 font-medium p-2 bg-red-500/10 rounded border border-red-500/20">
                      {error}
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* Right Pane - Results */}
            <div className={`flex-1 overflow-y-auto p-6 ${isDark ? 'bg-[#0a0f1e]' : 'bg-white'}`}>
              {!diffResult ? (
                <div className="h-full flex flex-col items-center justify-center text-center opacity-50">
                  <GitCompare className={`w-16 h-16 mb-4 ${isDark ? 'text-slate-600' : 'text-slate-300'}`} />
                  <h3 className={`text-lg font-semibold ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Select a baseline</h3>
                  <p className={`text-sm ${isDark ? 'text-slate-500' : 'text-slate-400'} max-w-sm`}>
                    Choose a snapshot on the left to see how your security posture has changed.
                  </p>
                </div>
              ) : diffResult.has_changes === false ? (
                <div className="h-full flex flex-col items-center justify-center text-center">
                  <div className="w-16 h-16 mb-4 rounded-full bg-green-500/20 flex items-center justify-center border border-green-500/30">
                    <Shield className="w-8 h-8 text-green-500" />
                  </div>
                  <h3 className={`text-lg font-bold ${isDark ? 'text-green-400' : 'text-green-600'}`}>No Structural Changes</h3>
                  <p className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-500'} mt-2`}>
                    The cluster graph is perfectly identical to the baseline snapshot.
                  </p>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Summary row */}
                  <div className="grid grid-cols-2 lg:grid-cols-6 gap-4">
                    <StatCard icon={<PlusCircle className="text-green-500 w-4 h-4" />} label="Nodes Added" value={diffResult.summary.nodes_added} isDark={isDark} color="green" />
                    <StatCard icon={<MinusCircle className="text-red-500 w-4 h-4" />} label="Nodes Removed" value={diffResult.summary.nodes_removed} isDark={isDark} color="red" />
                    <StatCard icon={<PlusCircle className="text-blue-500 w-4 h-4" />} label="Edges Added" value={diffResult.summary.edges_added} isDark={isDark} color="blue" />
                    <StatCard icon={<MinusCircle className="text-slate-500 w-4 h-4" />} label="Edges Removed" value={diffResult.summary.edges_removed} isDark={isDark} color="slate" />
                    <StatCard icon={<AlertTriangle className="text-orange-500 w-4 h-4" />} label="Escalations" value={diffResult.risk_changes.filter(r => r.escalation).length} isDark={isDark} color="orange" />
                    <StatCard icon={<Route className="text-purple-500 w-4 h-4" />} label="New Paths" value={diffResult.summary.new_attack_paths} isDark={isDark} color="purple" />
                  </div>

                  {/* Highlights section */}
                  {diffResult.has_new_threats && (
                    <div className={`p-4 rounded-xl border border-red-500/30 bg-red-500/10 text-red-500 flex gap-3 items-start`}>
                      <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
                      <div>
                        <h4 className="font-bold text-sm">Security Posture Degraded</h4>
                        <p className="text-xs opacity-90 mt-1">
                          Changes introduced since the baseline have structurally increased attack surface. Pay attention to new attack paths.
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Details Grid */}
                  <div className="grid md:grid-cols-2 gap-6">
                    {/* Added Nodes */}
                    {diffResult.added_nodes.length > 0 && (
                      <div className="space-y-3">
                        <h4 className={`text-sm font-bold flex items-center gap-2 ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>
                          <PlusCircle className="w-4 h-4 text-green-500" /> New Infrastructure
                        </h4>
                        <div className={`rounded-xl border overflow-hidden ${isDark ? 'border-slate-800' : 'border-slate-200'}`}>
                          {diffResult.added_nodes.map(n => (
                            <div key={n.id} className={`p-3 text-xs flex items-center justify-between border-b last:border-0 ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-100'}`}>
                              <div className="flex flex-col">
                                <span className={`font-mono font-medium ${isDark ? 'text-cyan-400' : 'text-blue-600'}`}>{n.label || n.id}</span>
                                <span className={`opacity-60 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>{n.type}</span>
                              </div>
                              <RiskBadge level={n.risk_level} />
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Removed Nodes */}
                    {diffResult.removed_nodes.length > 0 && (
                      <div className="space-y-3">
                        <h4 className={`text-sm font-bold flex items-center gap-2 ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>
                          <MinusCircle className="w-4 h-4 text-slate-500" /> Removed Infrastructure
                        </h4>
                        <div className={`rounded-xl border overflow-hidden ${isDark ? 'border-slate-800' : 'border-slate-200'}`}>
                          {diffResult.removed_nodes.map(n => (
                            <div key={n.id} className={`p-3 text-xs flex items-center justify-between border-b last:border-0 ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-100'}`}>
                              <div className="flex flex-col opacity-60 line-through">
                                <span className={`font-mono font-medium ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>{n.label || n.id}</span>
                              </div>
                              <span className={`px-2 py-0.5 rounded text-[10px] ${isDark ? 'bg-slate-800 text-slate-500' : 'bg-slate-100 text-slate-400'}`}>DELETED</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {/* Added Edges */}
                    {diffResult.added_edges.length > 0 && (
                      <div className="space-y-3">
                        <h4 className={`text-sm font-bold flex items-center gap-2 ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>
                          <PlusCircle className="w-4 h-4 text-blue-500" /> New Connections (Edges)
                        </h4>
                        <div className={`rounded-xl border overflow-hidden ${isDark ? 'border-slate-800' : 'border-slate-200'}`}>
                          {diffResult.added_edges.map((e, idx) => (
                            <div key={idx} className={`p-3 text-xs flex items-center justify-between border-b last:border-0 ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-100'}`}>
                              <div className="flex items-center gap-2 font-mono">
                                <span className={isDark ? 'text-slate-300' : 'text-slate-600'}>{e.source}</span>
                                <span className={`opacity-60 px-1 py-0.5 rounded ${isDark ? 'bg-slate-800' : 'bg-slate-100'}`}>→</span>
                                <span className={isDark ? 'text-slate-300' : 'text-slate-600'}>{e.target}</span>
                              </div>
                              <span className={`opacity-80 text-[10px] uppercase font-bold ${isDark ? 'text-blue-400' : 'text-blue-600'}`}>{e.relationship}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Removed Edges */}
                    {diffResult.removed_edges.length > 0 && (
                      <div className="space-y-3">
                        <h4 className={`text-sm font-bold flex items-center gap-2 ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>
                          <MinusCircle className="w-4 h-4 text-slate-500" /> Removed Connections
                        </h4>
                        <div className={`rounded-xl border overflow-hidden ${isDark ? 'border-slate-800' : 'border-slate-200'}`}>
                          {diffResult.removed_edges.map((e, idx) => (
                            <div key={idx} className={`p-3 text-xs flex items-center justify-between border-b last:border-0 ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-100'}`}>
                              <div className="flex items-center gap-2 font-mono opacity-60 line-through">
                                <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>{e.source}</span>
                                <span>→</span>
                                <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>{e.target}</span>
                              </div>
                              <span className={`px-2 py-0.5 rounded text-[10px] ${isDark ? 'bg-slate-800 text-slate-500' : 'bg-slate-100 text-slate-400'}`}>SEVERED</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Risk Escalations */}
                    {diffResult.risk_changes.filter(r => r.escalation).length > 0 && (
                      <div className="space-y-3 md:col-span-2">
                        <h4 className={`text-sm font-bold flex items-center gap-2 ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>
                          <Activity className="w-4 h-4 text-orange-500" /> Risk Escalations
                        </h4>
                        <div className={`grid sm:grid-cols-2 gap-3`}>
                          {diffResult.risk_changes.filter(r => r.escalation).map(r => (
                            <div key={r.node_id} className={`p-3 rounded-xl border flex items-center justify-between ${isDark ? 'bg-slate-900 border-orange-900/40' : 'bg-orange-50 border-orange-200'}`}>
                               <span className={`font-mono text-xs font-medium ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>{r.label}</span>
                               <div className="flex items-center gap-2 text-xs">
                                 <RiskBadge level={r.old_risk} />
                                 <span className={isDark ? 'text-slate-600' : 'text-slate-400'}>→</span>
                                 <RiskBadge level={r.new_risk} />
                               </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* New Attack Paths */}
                    {diffResult.new_attack_paths.length > 0 && (
                      <div className="space-y-3 md:col-span-2">
                        <h4 className={`text-sm font-bold flex items-center gap-2 ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>
                          <Route className="w-4 h-4 text-purple-500" /> New Attack Paths Created
                        </h4>
                        <div className="space-y-4">
                          {diffResult.new_attack_paths.map((path, idx) => (
                             <div key={idx} className={`p-4 rounded-xl border ${isDark ? 'bg-slate-900/50 border-purple-900/30' : 'bg-purple-50 border-purple-200'}`}>
                               <div className="flex items-center justify-between mb-2">
                                  <span className={`text-xs font-bold uppercase ${isDark ? 'text-purple-400' : 'text-purple-700'}`}>Path #{idx + 1} ({path.difficulty})</span>
                                  <span className={`text-[10px] ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>{path.hop_count} hops</span>
                               </div>
                               <p className={`text-xs mb-3 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>{path.description}</p>
                               <div className="flex flex-wrap items-center gap-1.5 text-[10px] font-mono">
                                 {path.path.map((node, stepIdx) => (
                                   <div key={stepIdx} className="flex items-center gap-1.5">
                                      <span className={`px-1.5 py-0.5 rounded ${isDark ? 'bg-slate-800 text-slate-300' : 'bg-white border text-slate-600'}`}>
                                        {node}
                                      </span>
                                      {stepIdx < path.path.length - 1 && <span className="opacity-50">→</span>}
                                   </div>
                                 ))}
                               </div>
                             </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

function StatCard({ icon, label, value, isDark, color }: { icon: React.ReactNode, label: string, value: number, isDark: boolean, color: string }) {
  const bg = isDark ? 'bg-slate-800/60' : 'bg-slate-50';
  const border = isDark ? 'border-slate-800/80' : 'border-slate-200';
  const valueColor = isDark ? 'text-white' : 'text-slate-900';
  return (
    <div className={`p-4 rounded-2xl border ${bg} ${border} flex items-center gap-4`}>
       <div className={`p-2 rounded-xl bg-${color}-500/10`}>
         {icon}
       </div>
       <div>
         <p className={`text-xs uppercase tracking-wider ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>{label}</p>
         <p className={`text-2xl font-bold ${valueColor}`}>{value}</p>
       </div>
    </div>
  );
}

function RiskBadge({ level }: { level: string }) {
   if (level === 'critical' || level === 'crown-jewel') return <span className="px-1.5 py-0.5 rounded bg-red-500/20 text-red-500 uppercase tracking-tighter">Critical</span>;
   if (level === 'high') return <span className="px-1.5 py-0.5 rounded bg-orange-500/20 text-orange-500 uppercase tracking-tighter">High</span>;
   if (level === 'medium') return <span className="px-1.5 py-0.5 rounded bg-yellow-500/20 text-yellow-500 uppercase tracking-tighter">Medium</span>;
   return <span className="px-1.5 py-0.5 rounded bg-slate-500/20 text-slate-500 uppercase tracking-tighter">{level}</span>;
}
