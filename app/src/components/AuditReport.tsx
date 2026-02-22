import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import LogicDNA from './LogicDNA';
import ProtocolLedger from './ProtocolLedger';

interface Milestone {
    step: string;
    status: string;
    details: string;
}

interface Vitals {
    liquidity: string;
    owner_risk: string;
    upgradeability?: string;
}

interface RedTeamLog {
    vector: string;
    status: string;
    verdict: string;
    details: string;
}

interface InitialDetection {
    score: number;
    source: string;
    detected_at: number;
}

interface Props {
    score: number;
    warnings: string[];
    riskSummary?: string;
    milestones?: Milestone[];
    vitals?: Vitals;
    redTeamLog?: RedTeamLog[];
    reportHash?: string;
    onClose?: () => void;
    cost?: number;
    creditSource?: string;
    initialDetection?: InitialDetection;  // [NEW] History of Suspicion
}

const AuditReport: React.FC<Props> = ({ score, warnings, riskSummary, milestones, vitals, redTeamLog, reportHash, onClose, cost, creditSource, initialDetection }) => {
    const [showLedger, setShowLedger] = useState(false);
    const [expandedMilestone, setExpandedMilestone] = useState<number | null>(null);

    const isSafe = score > 80;
    const isMedium = score > 50 && score <= 80;
    const colorClass = isSafe ? 'text-emerald-500' : isMedium ? 'text-amber-500' : 'text-red-500';
    const bgClass = isSafe ? 'bg-emerald-500' : isMedium ? 'bg-amber-500' : 'bg-red-500';
    const borderClass = isSafe ? 'border-emerald-500' : isMedium ? 'border-amber-500' : 'border-red-500';

    return (
        <div className="max-w-3xl mx-auto space-y-6 animate-fade-in-up">

            {/* 1. Header & Logic DNA */}
            <div className="bg-slate-900/50 rounded-2xl p-1 border border-slate-800 shadow-2xl backdrop-blur-sm">
                <div className="flex justify-between items-center px-4 py-2 border-b border-slate-800">
                    <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${bgClass} animate-pulse`}></div>
                        <span className="text-xs font-mono text-slate-400 uppercase tracking-widest">Audit Complete</span>
                    </div>
                    {reportHash && (
                        <div className="text-[10px] font-mono text-slate-600">
                            HASH: {reportHash.substring(0, 10)}...
                        </div>
                    )}
                </div>

                <div className="p-6">
                    <LogicDNA score={score} isSafe={isSafe} complexity={vitals?.upgradeability ? "High" : "Standard"} />

                    <div className="text-center mb-8">
                        <h2 className="text-3xl font-bold text-white mb-2">
                            Trust Score: <span className={colorClass}>{score}/100</span>
                        </h2>
                        <p className="text-slate-400 max-w-md mx-auto leading-relaxed">
                            {riskSummary || "Analysis complete. Review findings below."}
                        </p>
                    </div>

                    {/* Vitals Grid */}
                    {vitals && (
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-8">
                            <div className="bg-slate-800/50 p-3 rounded-xl border border-slate-700/50">
                                <div className="text-[10px] text-slate-500 uppercase font-bold">Liquidity</div>
                                <div className="text-white font-mono text-sm">{vitals.liquidity}</div>
                            </div>
                            <div className="bg-slate-800/50 p-3 rounded-xl border border-slate-700/50">
                                <div className="text-[10px] text-slate-500 uppercase font-bold">Owner Risk</div>
                                <div className="text-white font-mono text-sm">{vitals.owner_risk}</div>
                            </div>
                            <div className="bg-slate-800/50 p-3 rounded-xl border border-slate-700/50">
                                <div className="text-[10px] text-slate-500 uppercase font-bold">Proxy State</div>
                                <div className="text-white font-mono text-sm">{vitals.upgradeability || "Immutable"}</div>
                            </div>
                        </div>
                    )}

                    {/* Action Buttons */}
                    <div className="flex gap-3 justify-center">
                        <button
                            onClick={() => setShowLedger(true)}
                            className="px-6 py-2 bg-slate-800 hover:bg-slate-700 text-white text-sm font-bold rounded-lg border border-slate-700 flex items-center gap-2 transition-colors"
                        >
                            <span>🧾</span> View Ledger Receipt
                        </button>
                        <button className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-bold rounded-lg shadow-lg shadow-indigo-500/20 transition-colors">
                            Download PDF
                        </button>
                    </div>
                </div>
            </div>

            {/* [NEW] History of Suspicion Banner */}
            {initialDetection && (
                <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl px-4 py-3 flex items-start gap-3">
                    <span className="text-amber-400 text-lg mt-0.5">📡</span>
                    <div className="flex-1 min-w-0">
                        <div className="text-[10px] font-bold text-amber-400 uppercase tracking-widest mb-0.5">History of Suspicion</div>
                        <p className="text-sm text-amber-200">
                            Initial Detection:{' '}
                            <span className="font-bold font-mono">{Math.round(initialDetection.score)}%</span>
                            {' '}({initialDetection.source === 'chain' ? 'Auto-Scan / Chain Listener' : 'Userbot Scan'})
                            {' '}·{' '}
                            <span className="text-amber-300/70 text-xs">
                                {new Date(initialDetection.detected_at * 1000).toLocaleString()}
                            </span>
                        </p>
                        <p className="text-[11px] text-slate-400 mt-0.5">
                            Current Logic Score: <span className="font-bold text-white">{score}%</span>
                        </p>
                    </div>
                </div>
            )}

            {/* 2. Critical Warnings */}
            {warnings && warnings.length > 0 && (
                <div className="bg-red-500/5 border border-red-500/20 rounded-2xl p-6 relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4 opacity-10">
                        <svg className="w-24 h-24 text-red-500" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" /></svg>
                    </div>
                    <h3 className="text-red-400 font-bold uppercase tracking-widest text-sm mb-4 flex items-center gap-2">
                        <span className="w-2 h-2 bg-red-500 rounded-full animate-ping"></span>
                        Critical Findings
                    </h3>
                    <ul className="space-y-2 relative z-10">
                        {warnings.map((w, i) => (
                            <li key={i} className="flex items-start gap-2 text-red-200 text-sm bg-red-500/10 p-2 rounded-lg border border-red-500/20">
                                <span className="text-red-500 font-bold">!</span>
                                {w}
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {/* 3. Red Team Logs (Terminal) */}
            {redTeamLog && redTeamLog.length > 0 && (
                <div className="rounded-2xl overflow-hidden border border-slate-800 shadow-2xl bg-[#0d1117]">
                    <div className="bg-slate-900 px-4 py-2 flex items-center gap-2 border-b border-slate-800">
                        <div className="flex gap-1.5">
                            <div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500/50"></div>
                            <div className="w-3 h-3 rounded-full bg-amber-500/20 border border-amber-500/50"></div>
                            <div className="w-3 h-3 rounded-full bg-emerald-500/20 border border-emerald-500/50"></div>
                        </div>
                        <div className="text-[10px] font-mono text-slate-500 ml-2">red_team_execution_log.txt</div>
                    </div>
                    <div className="p-4 font-mono text-xs space-y-3 max-h-64 overflow-y-auto custom-scrollbar">
                        {redTeamLog.map((log, i) => (
                            <div key={i} className="group">
                                <div className="flex gap-2">
                                    <span className="text-slate-600 select-none">$</span>
                                    <span className="text-purple-400">simulate_exploit</span>
                                    <span className="text-slate-400">--target</span>
                                    <span className="text-amber-300">"{log.vector}"</span>
                                </div>
                                <div className={`pl-4 mt-1 border-l-2 ${log.status === 'BLOCKED' ? 'border-emerald-500/30 text-emerald-400' : 'border-red-500/30 text-red-400'}`}>
                                    <span className={`font-bold ${log.status === 'BLOCKED' ? 'bg-emerald-500/10' : 'bg-red-500/10'} px-1 rounded`}>
                                        [{log.status}]
                                    </span>
                                    <span className="ml-2 text-slate-300">{log.details}</span>
                                </div>
                            </div>
                        ))}
                        <div className="animate-pulse text-emerald-500 font-bold">_</div>
                    </div>
                </div>
            )}

            {/* 4. Milestones */}
            {milestones && milestones.length > 0 && (
                <div className="space-y-2">
                    <h3 className="text-slate-500 font-bold uppercase tracking-widest text-xs mb-2 ml-1">Universal Ledger Checks</h3>
                    {milestones.map((m, i) => (
                        <div
                            key={i}
                            onClick={() => setExpandedMilestone(expandedMilestone === i ? null : i)}
                            className="bg-white/5 border border-white/5 rounded-xl overflow-hidden cursor-pointer hover:bg-white/10 transition-colors"
                        >
                            <div className="p-3 flex justify-between items-center">
                                <div className="flex items-center gap-3">
                                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold ${m.status === 'pass' ? 'bg-emerald-500/20 text-emerald-400' :
                                        m.status === 'warn' ? 'bg-amber-500/20 text-amber-400' : 'bg-red-500/20 text-red-400'
                                        }`}>
                                        {m.status === 'pass' ? '✓' : m.status === 'warn' ? '!' : '✕'}
                                    </div>
                                    <span className="text-sm font-medium text-slate-200">{m.step}</span>
                                </div>
                                <span className="text-slate-500 text-xs">{expandedMilestone === i ? '−' : '+'}</span>
                            </div>
                            <AnimatePresence>
                                {expandedMilestone === i && (
                                    <motion.div
                                        initial={{ height: 0, opacity: 0 }}
                                        animate={{ height: 'auto', opacity: 1 }}
                                        exit={{ height: 0, opacity: 0 }}
                                        className="bg-black/20 px-4 pb-4 pt-0"
                                    >
                                        <p className="text-xs text-slate-400 pl-9 pt-2 border-t border-white/5">
                                            {m.details}
                                        </p>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    ))}
                </div>
            )}

            {/* Protocol Ledger Modal */}
            <AnimatePresence>
                {showLedger && (
                    <ProtocolLedger onClose={() => setShowLedger(false)} highlightHash={reportHash} amount={cost} source={creditSource} />
                )}
            </AnimatePresence>

        </div>
    );
};

export default AuditReport;
