import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface PreFlightPreviewProps {
    amount: number;
    costEth: number;
    onConfirm: () => void;
    onCancel: () => void;
}

export default function PreFlightPreview({ amount, costEth, onConfirm, onCancel }: PreFlightPreviewProps) {
    const [acceptedTerms, setAcceptedTerms] = useState(false);

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
            >
                <motion.div
                    initial={{ scale: 0.9, y: 20 }}
                    animate={{ scale: 1, y: 0 }}
                    className="bg-slate-900 border border-slate-700 rounded-2xl p-8 max-w-md w-full shadow-2xl relative overflow-hidden"
                >
                    {/* Background decoration */}
                    <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 blur-3xl rounded-full"></div>

                    <h2 className="text-2xl font-bold text-white mb-6 tracking-tight">Trust Contract Initialization</h2>

                    <div className="space-y-4 mb-8">
                        <div className="flex items-center justify-between p-4 bg-slate-800/50 rounded-xl border border-slate-700">
                            <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded bg-emerald-500/20 flex items-center justify-center text-emerald-400">⚡</div>
                                <div>
                                    <div className="text-sm font-bold text-slate-300">Security Injection</div>
                                    <div className="text-xs text-slate-500">Protocol Credits</div>
                                </div>
                            </div>
                            <div className="text-right">
                                <div className="text-xl font-bold text-white">+{amount}</div>
                                <div className="text-xs text-emerald-400">CRD</div>
                            </div>
                        </div>

                        <div className="flex items-center justify-between p-4 bg-slate-800/50 rounded-xl border border-slate-700">
                            <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded bg-amber-500/20 flex items-center justify-center text-amber-400">🛡️</div>
                                <div>
                                    <div className="text-sm font-bold text-slate-300">War Chest</div>
                                    <div className="text-xs text-slate-500">Security Research Fund</div>
                                </div>
                            </div>
                            <div className="text-right">
                                <div className="text-sm font-bold text-white">15%</div>
                                <div className="text-xs text-slate-500">Allocation</div>
                            </div>
                        </div>

                        <div className="flex justify-between items-center px-2 pt-2 border-t border-slate-800">
                            <span className="text-slate-400 text-sm">Total Contribution</span>
                            <span className="text-xl font-mono text-white">{costEth.toFixed(6)} ETH</span>
                        </div>
                    </div>

                    <div className="mb-4 bg-slate-800/30 p-3 rounded-lg border border-slate-700/50">
                        <label className="flex items-start gap-3 cursor-pointer group">
                            <div className="relative flex items-center">
                                <input
                                    type="checkbox"
                                    checked={acceptedTerms}
                                    onChange={(e) => setAcceptedTerms(e.target.checked)}
                                    className="peer h-5 w-5 cursor-pointer appearance-none rounded border border-slate-500 bg-slate-800 transition-all checked:border-emerald-500 checked:bg-emerald-500 hover:border-emerald-400"
                                />
                                <svg className="pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white opacity-0 peer-checked:opacity-100 transition-opacity" viewBox="0 0 14 14" fill="none">
                                    <path d="M3 8L6 11L11 3.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                </svg>
                            </div>
                            <span className="text-xs text-slate-400 leading-tight select-none">
                                I acknowledge the <a href="/Whitepaper.md" target="_blank" rel="noopener noreferrer" className="text-emerald-400 hover:underline font-bold" onClick={(e) => e.stopPropagation()}>Sovereign Utility Terms</a>: Credits are non-refundable and dedicated to audit services under the Service-Level Guarantee.
                            </span>
                        </label>
                    </div>

                    <div className="flex gap-3">
                        <button
                            onClick={onCancel}
                            className="flex-1 py-3 bg-slate-800 hover:bg-slate-700 text-white font-bold rounded-xl transition-colors"
                        >
                            Abort
                        </button>
                        <button
                            onClick={onConfirm}
                            disabled={!acceptedTerms}
                            className={`flex-1 py-3 font-bold rounded-xl shadow-lg transition-all active:scale-95 ${acceptedTerms
                                ? 'bg-emerald-500 hover:bg-emerald-600 text-white shadow-emerald-500/20'
                                : 'bg-slate-700 text-slate-500 cursor-not-allowed'}`}
                        >
                            Sign & Inject
                        </button>
                    </div>

                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
}
