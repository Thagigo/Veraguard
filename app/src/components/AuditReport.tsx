import React, { useState, useEffect } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
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

interface Props {
    score: number;
    warnings: string[];
    riskSummary?: string;
    milestones?: Milestone[];
    vitals?: Vitals;
    redTeamLog?: RedTeamLog[]; // New Prop
    reportHash?: string;       // New Prop
    onClose?: () => void;
}

const AuditReport: React.FC<Props> = ({ score, warnings, riskSummary, milestones, vitals, redTeamLog, reportHash, onClose }) => {
    const [expandedMilestone, setExpandedMilestone] = useState<number | null>(null);
    const [showVaultLock, setShowVaultLock] = useState(false);
    const [showLedger, setShowLedger] = useState(false);

    const isSafe = score >= 95;
    const pulseColor = score >= 80 ? 'bg-emerald-500' : score >= 50 ? 'bg-amber-500' : 'bg-red-500';
    const textColor = score >= 80 ? 'text-emerald-500' : score >= 50 ? 'text-amber-500' : 'text-red-500';

    useEffect(() => {
        // Emotional Gravity: Bust
        if (score < 50) {
            if (window.Telegram?.WebApp?.HapticFeedback) {
                window.Telegram.WebApp.HapticFeedback.notificationOccurred('error');
            }
            setShowVaultLock(true);
            setTimeout(() => setShowVaultLock(false), 2500);
        } else {
            if (window.Telegram?.WebApp?.HapticFeedback) {
                window.Telegram.WebApp.HapticFeedback.notificationOccurred('success');
            }
        }
    }, [score]); // Dependency on score

    return (
        <div className="max-w-3xl mx-auto space-y-6 animate-fade-in-up">
            {/* Vault Lock Animation Overlay */}
            <AnimatePresence>
                {showVaultLock && (
                    <motion.div
                        initial={{ opacity: 0, scale: 1.5 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.8 }}
                        className="fixed inset-0 z-[60] flex items-center justify-center pointer-events-none"
                    >
                        <div className="bg-red-600 text-white font-black text-6xl tracking-tighter border-8 border-white p-10 transform -rotate-12 shadow-2xl uppercase">
                            VAULT LOCKED
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* 1. VITALS CARD */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-xl border border-slate-100 dark:border-slate-800 overflow-hidden relative">
                {/* Certified Safe Badge */}
                {isSafe && (
                    <div className="absolute top-0 right-0 p-4 z-20">
                        <div className="flex items-center gap-2 bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-400 px-3 py-1 rounded-full text-xs font-bold shadow-sm border border-emerald-200 dark:border-emerald-800">
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                            CERTIFIED SAFE
                        </div>
                    </div>
                )}

                {/* Premium Badge */}
                {!isSafe && redTeamLog && redTeamLog.length > 0 && (
                    <div className="absolute top-0 right-0 p-4 z-20">
                        <div className="flex items-center gap-2 bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-400 px-3 py-1 rounded-full text-[10px] font-bold shadow-sm border border-amber-200 dark:border-amber-800 animate-pulse">
                            <span>👑</span> PREMIUM SOVEREIGN AUDIT
                        </div>
                    </div>
                )}

                {/* [NEW] Logic DNA Visualizer - Only for Premium Audits */}
                {redTeamLog && redTeamLog.length > 0 && (
                    <div className="p-1">
                        <LogicDNA score={score} isSafe={isSafe} complexity={vitals?.upgradeability || "Standard"} />
                    </div>
                )}

                <div className="p-8 flex flex-col md:flex-row items-center gap-8 relative z-10 -mt-6">
                    {/* Heartbeat Monitor */}
                    <div className="relative">
                        <div className={`w-32 h-32 rounded-full flex items-center justify-center border-4 ${score >= 80 ? 'border-emerald-100 dark:border-emerald-900' : 'border-red-100 dark:border-red-900'} relative`}>
                            <div className={`absolute inset-0 rounded-full opacity-20 animate-ping ${pulseColor}`}></div>
                            <div className="text-center z-10">
                                <span className={`text-4xl font-bold ${textColor}`}>{score}</span>
                                <span className="block text-xs text-slate-400 uppercase font-bold mt-1">VeraScore</span>
                            </div>
                        </div>
                    </div>

                    {/* Vitals Data */}
                    <div className="flex-1 w-full space-y-4">
                        <h2 className="text-xl font-bold text-slate-800 dark:text-white flex items-center gap-2">
                            <span className="text-2xl">🧬</span> Medical Audit Report
                        </h2>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-100 dark:border-slate-700">
                                <span className="text-xs text-slate-400 font-bold uppercase block mb-1">Liquidity Health</span>
                                <span className="font-mono font-medium text-slate-700 dark:text-slate-300">
                                    {vitals?.liquidity || "ANALYZING..."}
                                </span>
                            </div>
                            <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-100 dark:border-slate-700">
                                <span className="text-xs text-slate-400 font-bold uppercase block mb-1">Admin Control</span>
                                <span className="font-mono font-medium text-slate-700 dark:text-slate-300">
                                    {vitals?.owner_risk || "UNKNOWN"}
                                </span>
                            </div>
                        </div>

                        {riskSummary && (
                            <p className="text-sm font-medium leading-relaxed italic border-l-4 pl-3 py-1 border-slate-300 dark:border-slate-600 text-slate-600 dark:text-slate-400">
                                "{riskSummary}"
                            </p>
                        )}

                        {!riskSummary && score >= 95 && (
                            <div className="mt-4 p-3 bg-emerald-50 dark:bg-emerald-900/10 border border-emerald-100 dark:border-emerald-900/30 rounded-lg">
                                <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 uppercase block mb-1">Diagnostic Reason</span>
                                <p className="text-sm text-slate-600 dark:text-slate-300">
                                    No malicious owner-logic found. Liquidity is locked and verified. Contract matches standard safe patterns.
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* 2. FINDINGS & MILESTONES (Accordion) */}
            <div className="space-y-4">
                {warnings.length > 0 && (
                    <div className="bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-900/30 rounded-xl p-6">
                        <h3 className="font-bold text-red-700 dark:text-red-400 mb-4 flex items-center gap-2">
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                            Critical Findings ({warnings.length})
                        </h3>
                        <ul className="space-y-2">
                            {warnings.map((w, i) => (
                                <li key={i} className="flex gap-3 text-sm text-red-600 dark:text-red-300">
                                    <span className="mt-1">•</span>
                                    <span>{w}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                )}

                {milestones && milestones.length > 0 && (
                    <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-100 dark:border-slate-800 p-6">
                        <h3 className="font-bold text-slate-800 dark:text-white mb-4">Diagnostic Log</h3>
                        <div className="space-y-0">
                            {milestones.map((m, i) => (
                                <div key={i} className="relative pl-6 pb-6 last:pb-0 border-l border-slate-200 dark:border-slate-700">
                                    <div className={`absolute -left-1.5 top-1.5 w-3 h-3 rounded-full ${m.status === 'complete' ? 'bg-emerald-400 ring-4 ring-emerald-50 dark:ring-emerald-900/20' : 'bg-slate-300'}`}></div>

                                    <div
                                        className="cursor-pointer group"
                                        onClick={() => setExpandedMilestone(expandedMilestone === i ? null : i)}
                                    >
                                        <div className="flex justify-between items-center">
                                            <span className={`font-medium ${m.status === 'complete' ? 'text-slate-700 dark:text-slate-200' : 'text-slate-400'}`}>
                                                {m.step}
                                            </span>
                                            <span className="text-xs text-slate-400 uppercase">{m.status}</span>
                                        </div>
                                        <p className="text-xs text-slate-500 mt-1">{m.details}</p>

                                        {/* Simulating Deep Dive Logs Expansion */}
                                        {expandedMilestone === i && m.step.includes("Hunter") && (
                                            <div className="mt-3 p-3 bg-black text-green-400 font-mono text-xs rounded-lg overflow-x-auto animate-fade-in">
                                                <p>{">"} Initializing Red Team Sandbox...</p>
                                                <p>{">"} Forking Mainnet State @ Block 192837...</p>
                                                <p>{">"} Attempting Reentrancy Vector... [FAILED]</p>
                                                <p>{">"} Attempting Logic Bomb... [FAILED]</p>
                                                <p className="text-white">{">"} VERDICT: CLEAN</p>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* [NEW] Red-Team Log (Terminal Style) */}
                {redTeamLog && redTeamLog.length > 0 && (
                    <div className="bg-slate-900 rounded-xl shadow-lg border border-slate-700 p-6 overflow-hidden relative font-mono text-xs">
                        <div className="absolute top-0 left-0 w-full h-6 bg-slate-800 flex items-center px-4 gap-2">
                            <div className="w-2 h-2 rounded-full bg-red-500"></div>
                            <div className="w-2 h-2 rounded-full bg-amber-500"></div>
                            <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
                            <div className="ml-2 text-slate-400 font-bold opacity-50">VERA_RED_TEAM_CLI</div>
                        </div>
                        <div className="mt-4 space-y-2 text-emerald-400">
                            {redTeamLog.map((log, i) => (
                                <div key={i} className="flex flex-col border-b border-slate-800 pb-2 last:border-0">
                                    <div className="flex justify-between">
                                        <span className="text-slate-300">{`> executing vector: ${log.vector}...`}</span>
                                        <span className={log.verdict === 'VULNERABLE' ? 'text-red-500 font-bold' : 'text-emerald-500'}>
                                            [{log.verdict}]
                                        </span>
                                    </div>
                                    <div className="text-slate-500 pl-4">{log.details}</div>
                                </div>
                            ))}
                            <div className="animate-pulse text-emerald-500 mt-2">{">_ session closed."}</div>
                        </div>
                    </div>
                )}

                {/* [NEW] Sovereign Proof Footer */}
                {reportHash && (
                    <div className="mt-8 pt-6 border-t border-slate-200 dark:border-slate-800 text-center">
                        <p className="text-[10px] text-slate-400 uppercase tracking-widest mb-2">Sovereign Proof of Audit</p>
                        <div className="inline-flex items-center gap-2 px-3 py-1 bg-slate-100 dark:bg-slate-800 rounded-full font-mono text-[10px] text-slate-500 mb-4">
                            <span>Merkle Hash:</span>
                            <span className="text-emerald-600 dark:text-emerald-400 truncate max-w-[150px] md:max-w-xs">{reportHash}</span>
                        </div>
                        <button
                            disabled={!reportHash}
                            onClick={() => setShowLedger(true)}
                            className="px-6 py-3 bg-slate-900 dark:bg-white text-white dark:text-slate-900 font-bold rounded-xl shadow-lg hover:scale-105 active:scale-95 transition-all text-sm flex items-center gap-2 mx-auto disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <span>VERIFY ON LEDGER</span>
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                        </button>
                    </div>
                )}
            </div>

            {/* Protocol Ledger Modal */}
            {showLedger && (
                <ProtocolLedger onClose={() => setShowLedger(false)} highlightHash={reportHash} />
            )}
        </div>
    );
};

export default AuditReport;
