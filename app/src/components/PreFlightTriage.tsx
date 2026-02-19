import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface PreFlightTriageProps {
    address: string;
    complexity: 'Standard' | 'High';
    isProxy: boolean;
    cost: number;
    onMainAction: () => void;
    onBypass?: () => void; // For downgrading Deep Dive to Standard
    onCancel: () => void;
    isMember: boolean;
}

const PreFlightTriage: React.FC<PreFlightTriageProps> = ({
    address, complexity, isProxy, cost, onMainAction, onBypass, onCancel, isMember
}) => {

    // Determine Recommendation
    const isDeepDive = complexity === 'High' || isProxy;
    const recommendedTier = isDeepDive ? "Deep Scan" : "X-Ray";
    const recommendedCost = isMember ? (isDeepDive ? 2 : 0) : (isDeepDive ? 3 : 1);

    const reason = isProxy ? "Proxy Detected (Logic Upgradability)" :
        complexity === 'High' ? "High Bytecode Complexity (>24KB)" :
            "Standard Contract Schema";

    return (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/80 backdrop-blur-sm sm:p-4 animate-fade-in">
            <motion.div
                initial={{ opacity: 0, scale: 0.9, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9, y: 20 }}
                className="bg-slate-900 w-full sm:max-w-md rounded-t-2xl sm:rounded-2xl p-6 shadow-2xl border border-slate-700 relative overflow-hidden"
            >
                {/* Header Band */}
                <div className={`absolute top-0 left-0 right-0 h-1.5 ${isDeepDive ? 'bg-amber-500' : 'bg-emerald-500'}`} />

                <div className="flex justify-between items-start mb-6 mt-2">
                    <div>
                        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">PRE-FLIGHT TRIAGE</div>
                        <h3 className="text-xl font-bold text-white flex items-center gap-2">
                            {isDeepDive ? "⚠️ Deep Scan Recommended" : "✅ X-Ray Scan"}
                        </h3>
                    </div>
                    <button onClick={onCancel} className="text-slate-500 hover:text-white transition-colors">✕</button>
                </div>

                <div className="bg-slate-800/50 rounded-xl p-4 mb-6 border border-slate-700/50">
                    <p className="text-xs text-slate-400 font-mono mb-2">TARGET: {address.substring(0, 8)}...{address.substring(address.length - 6)}</p>
                    <div className="flex items-center gap-2 text-sm font-medium text-slate-200">
                        <span className="text-emerald-500">Analysis:</span> {reason}
                    </div>
                </div>

                <div className="space-y-3">
                    <button
                        onClick={onMainAction}
                        className={`w-full py-4 font-bold rounded-xl shadow-lg active:scale-95 transition-all flex justify-between px-6 items-center
                            ${isDeepDive
                                ? 'bg-amber-600 hover:bg-amber-700 text-white shadow-amber-900/20'
                                : 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-emerald-900/20'}`}
                    >
                        <span>{isDeepDive ? "Perform Deep Scan" : "Start X-Ray"}</span>
                        <div className="flex flex-col items-end leading-tight">
                            <span className="text-sm bg-black/20 px-2 py-0.5 rounded">
                                {recommendedCost === 0 ? "FREE" : `${recommendedCost} CRD`}
                            </span>
                            {isMember && recommendedCost > 0 && <span className="text-[9px] opacity-70 line-through">{(isDeepDive ? 3 : 1)} CRD</span>}
                        </div>
                    </button>

                    {isDeepDive && onBypass && (
                        <button
                            onClick={onBypass}
                            className="w-full py-3 bg-slate-800 text-slate-400 font-bold rounded-xl hover:bg-slate-700 hover:text-slate-200 transition-all text-xs flex justify-between px-6 items-center"
                        >
                            <span>Bypass & Run Standard X-Ray</span>
                            <span>{isMember ? "FREE" : "1 CRD"}</span>
                        </button>
                    )}
                </div>

            </motion.div>
        </div>
    );
};

export default PreFlightTriage;
