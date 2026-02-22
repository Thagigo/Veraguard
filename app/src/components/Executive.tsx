import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface ExecutiveStats {
    total_carry_usd: number;
    active_vouchers_usd: number;
    vault_balance_eth: number;
    neurons_active: number;
    efficiency_rate?: number;
    staged_signatures?: number;
}

interface ExecutiveProps {
    isOpen: boolean;
    onClose: () => void;
    userId: string;
}

const Executive: React.FC<ExecutiveProps> = ({ isOpen, onClose, userId }) => {
    const [stats, setStats] = useState<ExecutiveStats | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (isOpen) {
            setLoading(true);
            fetch(`http://localhost:8000/api/executive?user_id=${userId}`)
                .then(res => res.json())
                .then(data => {
                    setStats(data);
                    setLoading(false);
                })
                .catch(err => {
                    console.error("Exec Verify Failed:", err);
                    setLoading(false);
                });
        }
    }, [isOpen, userId]);

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-xl"
            >
                <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10 pointer-events-none"></div>

                <motion.div
                    initial={{ scale: 0.9, y: 20 }}
                    animate={{ scale: 1, y: 0 }}
                    className="relative w-full max-w-6xl p-8 bg-zinc-900/50 border border-zinc-700/50 rounded-2xl shadow-2xl backdrop-blur-md overflow-hidden"
                >
                    {/* Header */}
                    <div className="flex justify-between items-center mb-8">
                        <div>
                            <h1 className="text-3xl font-thin tracking-widest text-white uppercase font-mono">
                                Executive_View <span className="text-rose-500">///</span>
                            </h1>
                            <p className="text-zinc-500 text-sm mt-1">Founder Clearance Level: ALPHA</p>
                        </div>
                        <button
                            onClick={onClose}
                            className="px-4 py-2 rounded-full border border-zinc-700 text-zinc-400 hover:text-white hover:border-white transition-all text-xs uppercase tracking-wider"
                        >
                            Close Secure Channel
                        </button>
                    </div>

                    {/* Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">

                        {/* Metric 1: Founder Carry */}
                        <motion.div
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: 0.1 }}
                            className="p-6 rounded-xl bg-zinc-800/30 border border-zinc-700/50 hover:border-rose-500/50 transition-colors group"
                        >
                            <h3 className="text-zinc-500 text-xs font-bold uppercase tracking-widest mb-2">Total Carry</h3>
                            <div className="flex items-baseline gap-2">
                                <span className="text-4xl font-light text-white font-mono">
                                    {loading ? "..." : stats?.total_carry_usd.toFixed(2)}
                                </span>
                                <span className="text-rose-500 text-sm">USD</span>
                            </div>
                            <div className="mt-4 h-1 w-full bg-zinc-800 rounded-full overflow-hidden">
                                <motion.div
                                    initial={{ width: 0 }}
                                    animate={{ width: "100%" }}
                                    className="h-full bg-rose-500/80"
                                />
                            </div>
                            <p className="mt-2 text-[10px] text-zinc-500 group-hover:text-rose-400 transition-colors">
                                Fees + Settlements
                            </p>
                        </motion.div>

                        {/* Metric 2: Workforce Liquidity */}
                        <motion.div
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: 0.2 }}
                            className="p-6 rounded-xl bg-zinc-800/30 border border-zinc-700/50 hover:border-indigo-500/50 transition-colors group"
                        >
                            <h3 className="text-zinc-500 text-xs font-bold uppercase tracking-widest mb-2">Voucher Liability</h3>
                            <div className="flex items-baseline gap-2">
                                <span className="text-4xl font-light text-white font-mono">
                                    {loading ? "..." : stats?.active_vouchers_usd.toFixed(2)}
                                </span>
                                <span className="text-indigo-500 text-sm">USD</span>
                            </div>
                            <div className="mt-4 h-1 w-full bg-zinc-800 rounded-full overflow-hidden">
                                <motion.div
                                    initial={{ width: 0 }}
                                    animate={{ width: "60%" }}
                                    className="h-full bg-indigo-500/80"
                                />
                            </div>
                            <p className="mt-2 text-[10px] text-zinc-500 group-hover:text-indigo-400 transition-colors">
                                Workforce Active Exposure
                            </p>
                        </motion.div>

                        {/* Metric 3: Insurance Depth */}
                        <motion.div
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: 0.3 }}
                            className="p-6 rounded-xl bg-zinc-800/30 border border-zinc-700/50 hover:border-emerald-500/50 transition-colors group"
                        >
                            <h3 className="text-zinc-500 text-xs font-bold uppercase tracking-widest mb-2">Sovereign Anchor</h3>
                            <div className="flex items-baseline gap-2">
                                <span className="text-4xl font-light text-white font-mono">
                                    {loading ? "..." : stats?.vault_balance_eth.toFixed(4)}
                                </span>
                                <span className="text-emerald-500 text-sm">ETH</span>
                            </div>
                            <div className="mt-4 h-1 w-full bg-zinc-800 rounded-full overflow-hidden">
                                <motion.div
                                    initial={{ width: 0 }}
                                    animate={{ width: "85%" }}
                                    className="h-full bg-emerald-500/80"
                                />
                            </div>
                            <p className="mt-2 text-[10px] text-zinc-500 group-hover:text-emerald-400 transition-colors">
                                Emerald Vault Solvency
                            </p>
                        </motion.div>

                        {/* Metric 4: Neural Evolution [NEW] */}
                        <motion.div
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: 0.4 }}
                            className="p-6 rounded-xl bg-zinc-800/30 border border-zinc-700/50 hover:border-blue-500/50 transition-colors group shadow-[0_0_20px_rgba(59,130,246,0.1)]"
                        >
                            <h3 className="text-zinc-500 text-xs font-bold uppercase tracking-widest mb-2">Neurons Active</h3>
                            <div className="flex items-baseline gap-2">
                                <span className="text-4xl font-light text-white font-mono">
                                    {loading ? "..." : stats?.neurons_active}
                                </span>
                                <span className="text-blue-500 text-sm">IQ</span>
                            </div>
                            <div className="mt-4 h-1 w-full bg-zinc-800 rounded-full overflow-hidden">
                                <motion.div
                                    initial={{ width: 0 }}
                                    animate={{ width: "100%" }}
                                    transition={{ duration: 2, ease: "easeOut" }}
                                    className="h-full bg-blue-500/80 shadow-[0_0_10px_rgba(59,130,246,0.5)]"
                                />
                            </div>
                            <p className="mt-2 text-[10px] text-zinc-500 group-hover:text-blue-400 transition-colors">
                                Real-time Neural Bridge Evolution
                            </p>
                        </motion.div>

                        {/* Metric 5: Scout Efficiency Rate [NEW] */}
                        <motion.div
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: 0.5 }}
                            className="p-6 rounded-xl bg-zinc-800/30 border border-zinc-700/50 hover:border-amber-500/50 transition-colors group shadow-[0_0_20px_rgba(245,158,11,0.1)]"
                        >
                            <h3 className="text-zinc-500 text-xs font-bold uppercase tracking-widest mb-2">Efficiency Rate</h3>
                            <div className="flex items-baseline gap-2">
                                <span className="text-4xl font-light text-white font-mono">
                                    {loading ? "..." : (stats?.efficiency_rate || 0).toFixed(2)}
                                </span>
                                <span className="text-amber-500 text-sm">%</span>
                            </div>
                            <div className="mt-4 h-1 w-full bg-zinc-800 rounded-full overflow-hidden relative">
                                <motion.div
                                    initial={{ width: 0 }}
                                    animate={{ width: `${Math.min((stats?.efficiency_rate || 0), 100)}%` }}
                                    transition={{ duration: 1.5, ease: "easeOut" }}
                                    className="h-full bg-amber-500/80 shadow-[0_0_10px_rgba(245,158,11,0.5)]"
                                />
                            </div>
                            <p className="mt-2 text-[10px] text-zinc-500 group-hover:text-amber-400 transition-colors">
                                Scout Leads / Total Seen
                            </p>
                        </motion.div>

                        {/* Metric 6: Staged Signatures [NEW] */}
                        <motion.div
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: 0.6 }}
                            className="p-6 rounded-xl bg-zinc-800/30 border border-zinc-700/50 hover:border-violet-500/50 transition-colors group shadow-[0_0_20px_rgba(139,92,246,0.1)]"
                        >
                            <h3 className="text-zinc-500 text-xs font-bold uppercase tracking-widest mb-2">Staged Signatures</h3>
                            <div className="flex items-baseline gap-2">
                                <span className="text-4xl font-light text-white font-mono">
                                    {loading ? "..." : (stats?.staged_signatures || 0)}
                                </span>
                                <span className="text-violet-500 text-sm">HEX</span>
                            </div>
                            <div className="mt-4 h-1 w-full bg-zinc-800 rounded-full overflow-hidden relative">
                                <motion.div
                                    initial={{ width: 0 }}
                                    animate={{ width: stats?.staged_signatures ? "100%" : "0%" }}
                                    transition={{ duration: 1.5, ease: "easeOut" }}
                                    className="h-full bg-violet-500/80 shadow-[0_0_10px_rgba(139,92,246,0.5)]"
                                />
                            </div>
                            <p className="mt-2 text-[10px] text-zinc-500 group-hover:text-violet-400 transition-colors">
                                Intelligence Bridge Staging Area
                            </p>
                        </motion.div>
                    </div>

                    {/* Footer / Status */}
                    <div className="mt-8 pt-6 border-t border-zinc-800 flex justify-between items-center">
                        <div className="flex gap-4">
                            <div className="flex items-center gap-2">
                                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                                <span className="text-xs text-zinc-400 uppercase">Settlement Engine: ONLINE</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse delay-75"></div>
                                <span className="text-xs text-zinc-400 uppercase">Revenue Bot: ACTIVE</span>
                            </div>
                        </div>
                        <div className="text-right">
                            <p className="text-[10px] text-zinc-600 font-mono">SYSTEM_ID: VERA_CORE_V1.2</p>
                        </div>
                    </div>

                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
};

export default Executive;
