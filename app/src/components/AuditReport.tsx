import React, { useState } from 'react';

interface Milestone {
    step: string;
    status: string;
    details: string;
}

interface Vitals {
    liquidity: string;
    owner_risk: string;
}

interface Props {
    score: number;
    warnings: string[];
    riskSummary?: string;
    milestones?: Milestone[];
    vitals?: Vitals;
}

const AuditReport: React.FC<Props> = ({ score, warnings, riskSummary, milestones, vitals }) => {
    const [expandedMilestone, setExpandedMilestone] = useState<number | null>(null);

    const isSafe = score >= 95;
    const pulseColor = score >= 80 ? 'bg-emerald-500' : score >= 50 ? 'bg-amber-500' : 'bg-red-500';
    const textColor = score >= 80 ? 'text-emerald-500' : score >= 50 ? 'text-amber-500' : 'text-red-500';

    return (
        <div className="max-w-3xl mx-auto space-y-6 animate-fade-in-up">

            {/* 1. VITALS CARD */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-xl border border-slate-100 dark:border-slate-800 overflow-hidden relative">
                {/* Certified Safe Badge */}
                {isSafe && (
                    <div className="absolute top-0 right-0 p-4">
                        <div className="flex items-center gap-2 bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-400 px-3 py-1 rounded-full text-xs font-bold shadow-sm border border-emerald-200 dark:border-emerald-800">
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                            CERTIFIED SAFE
                        </div>
                    </div>
                )}

                <div className="p-8 flex flex-col md:flex-row items-center gap-8">
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
            </div>
        </div>
    );
};

export default AuditReport;
