import { useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Download, FileText, AlertTriangle, ArrowRight, Shield, ChevronRight } from 'lucide-react';
import type { ShortestPathResult } from '@/lib/types';

interface Props {
  result: ShortestPathResult | null;
  isOpen: boolean;
  onClose: () => void;
  isDark: boolean;
}

const STEP_COLORS: Record<string, string> = {
  'crown-jewel': 'from-yellow-500 to-amber-600',
  'critical': 'from-red-500 to-rose-600',
  'high': 'from-orange-500 to-red-500',
  'medium': 'from-amber-500 to-orange-500',
  'low': 'from-green-500 to-emerald-500',
  'entry-point': 'from-green-500 to-teal-500',
  'info': 'from-slate-500 to-slate-600',
};

export default function KillChainReport({ result, isOpen, onClose, isDark }: Props) {
  const reportRef = useRef<HTMLDivElement>(null);

  if (!result || !isOpen) return null;

  const handleExportPDF = async () => {
    try {
      const res = await fetch('/api/export-pdf', { method: 'POST' });
      if (!res.ok) throw new Error('PDF generation failed');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `KubePathAudit_KillChain_${new Date().toISOString().slice(0, 10)}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('PDF export failed:', err);
      alert('Failed to generate PDF. Make sure the backend is running.');
    }
  };

  const chain = result.kill_chain_summary || [];

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
      >
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-black/60 backdrop-blur-sm"
          onClick={onClose}
        />

        {/* Modal */}
        <motion.div
          initial={{ y: 40, opacity: 0, scale: 0.95 }}
          animate={{ y: 0, opacity: 1, scale: 1 }}
          exit={{ y: 40, opacity: 0, scale: 0.95 }}
          transition={{ type: 'spring', damping: 25 }}
          className={`relative z-10 flex flex-col w-full max-w-2xl max-h-[85vh] rounded-2xl shadow-2xl
            ${isDark ? 'bg-slate-900 border border-slate-700/50' : 'bg-white border border-slate-200'}
            shadow-black/30`}
        >
          {/* Header */}
          <div className={`shrink-0 z-20 flex items-center justify-between px-6 py-4 border-b rounded-t-2xl
            ${isDark ? 'bg-slate-900/95 border-slate-700/50' : 'bg-white/95 border-slate-200'}`}>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-gradient-to-br from-red-500 to-orange-500">
                <FileText className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className={`text-lg font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>Kill Chain Report</h2>
                <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                  Attack Path Analysis — {new Date().toLocaleDateString()}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 no-print">
              <button
                onClick={handleExportPDF}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all
                  bg-gradient-to-r from-blue-600 to-cyan-600 text-white
                  hover:from-blue-500 hover:to-cyan-500 hover:shadow-lg hover:shadow-blue-500/20"
              >
                <Download className="w-3.5 h-3.5" />
                Export PDF
              </button>
              <button
                onClick={onClose}
                className={`p-1.5 rounded-lg transition-colors ${isDark ? 'hover:bg-slate-800 text-slate-400' : 'hover:bg-slate-100 text-slate-500'}`}
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Report Content - Scrolling Area */}
          <div className="flex-1 overflow-y-auto printable-report">
            <div ref={reportRef} className="p-6">
            {/* Summary Banner */}
            <div className={`p-4 rounded-xl mb-6 border
              ${result.difficulty === 'TRIVIAL' || result.difficulty === 'EASY'
                ? (isDark ? 'bg-red-950/40 border-red-900/50' : 'bg-red-50 border-red-200')
                : (isDark ? 'bg-amber-950/40 border-amber-900/50' : 'bg-amber-50 border-amber-200')
              }`}
            >
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className={`w-5 h-5 ${result.difficulty === 'TRIVIAL' || result.difficulty === 'EASY' ? 'text-red-400' : 'text-amber-400'}`} />
                <span className={`text-sm font-bold ${result.difficulty === 'TRIVIAL' || result.difficulty === 'EASY' ? 'text-red-400' : 'text-amber-400'}`}>
                  {result.difficulty} Attack Path Detected
                </span>
              </div>
              <div className={`grid grid-cols-3 gap-4 mt-3 text-center`}>
                <div>
                  <p className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>{result.hop_count}</p>
                  <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Total Hops</p>
                </div>
                <div>
                  <p className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>{result.total_weight}</p>
                  <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>CVSS Weight</p>
                </div>
                <div>
                  <p className={`text-2xl font-bold ${
                    result.difficulty === 'TRIVIAL' ? 'text-red-400' :
                    result.difficulty === 'EASY' ? 'text-orange-400' :
                    result.difficulty === 'MODERATE' ? 'text-amber-400' : 'text-green-400'
                  }`}>{result.difficulty}</p>
                  <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Difficulty</p>
                </div>
              </div>
            </div>

            {/* Path Overview */}
            <div className="mb-6">
              <h3 className={`text-sm font-bold mb-3 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                Attack Path Overview
              </h3>
              <div className="flex flex-wrap items-center gap-1.5">
                {result.path.map((nodeId, i) => (
                  <span key={nodeId} className="flex items-center gap-1.5">
                    <span className={`px-2 py-1 rounded-md text-xs font-mono font-medium
                      ${isDark ? 'bg-slate-800 text-slate-200 border border-slate-700' : 'bg-slate-100 text-slate-700 border border-slate-200'}`}>
                      {nodeId}
                    </span>
                    {i < result.path.length - 1 && (
                      <ArrowRight className="w-3.5 h-3.5 text-red-400 shrink-0" />
                    )}
                  </span>
                ))}
              </div>
            </div>

            {/* Kill Chain Steps */}
            <div>
              <h3 className={`text-sm font-bold mb-4 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                Detailed Kill Chain
              </h3>
              <div className="space-y-4">
                {chain.map((step, i) => {
                  const gradient = STEP_COLORS[step.risk_level] || STEP_COLORS.info;
                  return (
                    <motion.div
                      key={step.step}
                      initial={{ x: -30, opacity: 0 }}
                      animate={{ x: 0, opacity: 1 }}
                      transition={{ delay: i * 0.08 }}
                      className="relative"
                    >
                      <div className={`flex gap-4 p-4 rounded-xl border transition-all
                        ${isDark ? 'bg-slate-800/50 border-slate-700/50 hover:bg-slate-800' : 'bg-slate-50 border-slate-200 hover:bg-white'}`}>
                        {/* Step Number */}
                        <div className={`shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br ${gradient}
                          flex items-center justify-center text-white font-bold text-sm shadow-lg`}>
                          {step.step}
                        </div>

                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className={`font-semibold text-sm ${isDark ? 'text-white' : 'text-slate-900'}`}>
                              {step.node}
                            </span>
                            <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium uppercase
                              ${isDark ? 'bg-slate-700 text-slate-300' : 'bg-slate-200 text-slate-600'}`}>
                              {step.node_type}
                            </span>
                          </div>
                          <p className={`text-xs mb-2 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                            {step.action}
                          </p>
                          <div className="flex flex-wrap items-center gap-2">
                            {step.cves_exploited.length > 0 && step.cves_exploited.map(cve => (
                              <span key={cve} className="text-[10px] px-1.5 py-0.5 rounded font-mono bg-red-500/20 text-red-400">
                                {cve}
                              </span>
                            ))}
                            {step.edge_info && step.edge_info !== '—' && (
                              <span className={`text-[10px] px-1.5 py-0.5 rounded ${isDark ? 'bg-slate-700 text-slate-400' : 'bg-slate-200 text-slate-500'}`}>
                                → {step.edge_info}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Connector */}
                      {i < chain.length - 1 && (
                        <div className="absolute left-[2.15rem] top-[3.5rem] w-0.5 h-4 bg-gradient-to-b from-red-500/50 to-transparent" />
                      )}
                    </motion.div>
                  );
                })}
              </div>
            </div>

            {/* Footer */}
            <div className={`mt-6 pt-4 border-t text-center ${isDark ? 'border-slate-700/50' : 'border-slate-200'}`}>
              <p className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                Generated by KubePathAudit • {new Date().toLocaleString()} • Confidential
              </p>
            </div>
          </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
