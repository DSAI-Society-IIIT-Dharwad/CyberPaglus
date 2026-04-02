import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield, AlertTriangle, Database, Key, Server, Globe, Link2, User,
  Cpu, Activity, HardDrive, FileText, ShieldOff, ShieldAlert, Network, Monitor,
  X, Crosshair, Route, ChevronRight
} from 'lucide-react';
import type { GraphNode } from '@/lib/types';

interface Props {
  node: GraphNode | null;
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

const RISK_BADGE: Record<string, { bg: string; text: string; label: string }> = {
  'crown-jewel': { bg: 'bg-yellow-500/20', text: 'text-yellow-400', label: '👑 Crown Jewel' },
  'critical': { bg: 'bg-red-500/20', text: 'text-red-400', label: '🔴 Critical' },
  'high': { bg: 'bg-orange-500/20', text: 'text-orange-400', label: '🟠 High' },
  'medium': { bg: 'bg-amber-500/20', text: 'text-amber-400', label: '🟡 Medium' },
  'low': { bg: 'bg-green-500/20', text: 'text-green-400', label: '🟢 Low' },
  'entry-point': { bg: 'bg-green-500/20', text: 'text-green-400', label: '🌐 Entry Point' },
  'info': { bg: 'bg-slate-500/20', text: 'text-slate-400', label: 'ℹ️ Info' },
};

export default function SecuritySidebar({ node, onClose, onBlastRadius, onFindPath, isDark }: Props) {
  if (!node) return null;

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
              onClick={onClose}
              className={`p-1.5 rounded-lg transition-colors ${isDark ? 'hover:bg-slate-800 text-slate-400' : 'hover:bg-slate-100 text-slate-500'}`}
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="px-5 py-4 space-y-5">
          {/* Risk Badge */}
          <motion.div initial={{ scale: 0.9 }} animate={{ scale: 1 }} className={`inline-flex px-3 py-1.5 rounded-full text-xs font-medium ${risk.bg} ${risk.text}`}>
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
            {node.metadata?.image && (
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
            {node.metadata?.ports && node.metadata.ports.length > 0 && (
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
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
