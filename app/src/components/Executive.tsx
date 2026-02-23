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

interface BrainStatus {
    status: string;
    brain_mode?: string;
    source_count?: number;
    staged_signatures?: number;
    scout_budget?: number;
    scout_spend?: number;
    vault_solvency?: string;
}

interface ExecutiveProps {
    isOpen: boolean;
    onClose: () => void;
    userId: string;
}

// ── Organ Card ────────────────────────────────────────────────────────────────
const OrganCard = ({ label, value, unit, bar, barColour, sub, glow }: {
    label: string; value: string | number; unit?: string;
    bar?: number; barColour: string; sub?: string; glow?: string;
}) => (
    <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className={`p-5 rounded-xl bg-zinc-800/30 border border-zinc-700/40 hover:border-zinc-600/60 transition-colors group flex flex-col gap-2 ${glow ?? ''}`}
    >
        <h3 className="text-zinc-500 text-[10px] font-bold uppercase tracking-widest">{label}</h3>
        <div className="flex items-baseline gap-1.5">
            <span className="text-3xl font-light text-white font-mono">{value}</span>
            {unit && <span className={`text-sm ${barColour}`}>{unit}</span>}
        </div>
        {bar !== undefined && (
            <div className="h-0.5 w-full bg-zinc-800 rounded-full overflow-hidden">
                <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.min(bar, 100)}%` }}
                    transition={{ duration: 1.2, ease: 'easeOut' }}
                    className={`h-full rounded-full ${barColour.replace('text-', 'bg-')}/80`}
                />
            </div>
        )}
        {sub && <p className="text-[10px] text-zinc-600 group-hover:text-zinc-400 transition-colors">{sub}</p>}
    </motion.div>
);

// ── Brain Organ ───────────────────────────────────────────────────────────────
const BrainOrgan = ({ brain }: { brain: BrainStatus | null }) => {
    const grounded = brain?.brain_mode === 'GROUNDED';
    const src = brain?.source_count ?? 0;
    const staged = brain?.staged_signatures ?? 0;
    const label = grounded ? (src > 0 ? `GROUNDED` : 'GROUNDED') : (brain ? 'LOCAL' : '…');
    const colour = grounded ? 'text-cyan-400' : 'text-yellow-400';
    const borderColour = grounded ? 'border-cyan-500/30 hover:border-cyan-400/50' : 'border-yellow-500/20 hover:border-yellow-400/40';
    const glowClass = grounded ? 'shadow-[0_0_20px_rgba(6,182,212,0.08)]' : '';

    return (
        <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.35 }}
            className={`p-5 rounded-xl bg-zinc-800/30 border ${borderColour} transition-colors group flex flex-col gap-2 ${glowClass}`}
        >
            <h3 className="text-zinc-500 text-[10px] font-bold uppercase tracking-widest">Brain</h3>
            <div className="flex items-baseline gap-2">
                <span className={`text-3xl font-light font-mono ${colour}`}>{label}</span>
                {grounded && src > 0 && (
                    <span className="text-xs text-cyan-600 font-mono">{src} src</span>
                )}
            </div>
            {grounded && (
                <div className="h-0.5 w-full bg-zinc-800 rounded-full overflow-hidden">
                    <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: '100%' }}
                        transition={{ duration: 1.5 }}
                        className="h-full rounded-full bg-cyan-500/70 shadow-[0_0_6px_rgba(6,182,212,0.4)]"
                    />
                </div>
            )}
            <p className="text-[10px] text-zinc-600 group-hover:text-zinc-400 transition-colors">
                {grounded
                    ? `Cloud intelligence active · ${staged} sig staged`
                    : 'Set NOTEBOOK_ID to enable cloud grounding'}
            </p>
        </motion.div>
    );
};

// ── Main Component ────────────────────────────────────────────────────────────
const Executive: React.FC<ExecutiveProps> = ({ isOpen, onClose, userId }) => {
    const [stats, setStats] = useState<ExecutiveStats | null>(null);
    const [brain, setBrain] = useState<BrainStatus | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!isOpen) return;
        setLoading(true);

        // Fetch executive revenue stats
        fetch(`http://localhost:8000/api/executive?user_id=${userId}`)
            .then(r => r.json())
            .then(d => { setStats(d); setLoading(false); })
            .catch(() => setLoading(false));

        // Fetch brain status for GROUNDED indicator
        const initData =
            (window as any).Telegram?.WebApp?.initData ||
            "auth_date=1771409053&query_id=AAG_DEV&user=%7B%22id%22%3A7695994098%2C%22first_name%22%3A%22Admin%22%2C%22username%22%3A%22admin%22%2C%22last_name%22%3A%22Test%22%2C%22language_code%22%3A%22en%22%2C%22allows_write_to_pm%22%3Atrue%7D&hash=f17a0ea19a0f07e0ab4bd7ae41a2f627be61e4e159eee4dd6a431e855f273d57";
        fetch('http://localhost:8000/api/brain/status', { headers: { 'X-Telegram-Init-Data': initData } })
            .then(r => r.ok ? r.json() : null)
            .then(d => { if (d) setBrain(d); })
            .catch(() => { /* silent */ });
    }, [isOpen, userId]);

    if (!isOpen) return null;

    const L = (n: number | undefined, decimals = 2) => loading ? '…' : (n ?? 0).toFixed(decimals);

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-50 flex items-center justify-center bg-black/92 backdrop-blur-xl overflow-y-auto py-8 px-4"
            >
                <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-[0.06] pointer-events-none" />

                <motion.div
                    initial={{ scale: 0.94, y: 24 }}
                    animate={{ scale: 1, y: 0 }}
                    className="relative w-full max-w-5xl bg-zinc-900/60 border border-zinc-700/50 rounded-2xl shadow-2xl backdrop-blur-md overflow-hidden"
                >
                    {/* Header */}
                    <div className="flex justify-between items-center px-8 py-6 border-b border-zinc-800/60">
                        <div>
                            <h1 className="text-2xl font-thin tracking-widest text-white uppercase font-mono">
                                Executive_View <span className="text-rose-500">///</span>
                            </h1>
                            <p className="text-zinc-500 text-xs mt-0.5">Founder Clearance Level: ALPHA</p>
                        </div>
                        <button
                            onClick={onClose}
                            className="px-4 py-1.5 rounded-full border border-zinc-700 text-zinc-400 hover:text-white hover:border-white transition-all text-xs uppercase tracking-wider"
                        >
                            Close
                        </button>
                    </div>

                    <div className="p-8 flex flex-col gap-8">

                        {/* ── Neural Organ Map (centerpiece) ──────────────── */}
                        <section>
                            <p className="text-[9px] uppercase text-zinc-600 tracking-widest mb-4">▸ Neural Organ Map</p>
                            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
                                <OrganCard label="Neurons Active" value={loading ? '…' : (stats?.neurons_active ?? 0)} unit="IQ"
                                    bar={100} barColour="text-blue-500"
                                    sub="Real-time neural evolution" glow="shadow-[0_0_20px_rgba(59,130,246,0.07)]" />
                                <OrganCard label="Scout Budget" value={L(brain?.scout_budget)} unit="USD"
                                    bar={brain ? ((brain.scout_spend ?? 0) / Math.max(brain.scout_budget ?? 1, 1)) * 100 : 0}
                                    barColour="text-green-500" sub={`Spent: $${L(brain?.scout_spend)}`} />
                                <BrainOrgan brain={brain} />
                                <OrganCard label="Sovereign Anchor" value={L(stats?.vault_balance_eth, 4)} unit="ETH"
                                    bar={85} barColour="text-emerald-500" sub="Emerald Vault solvency" />
                                <OrganCard label="Staged Signatures" value={loading ? '…' : (stats?.staged_signatures ?? 0)} unit="HEX"
                                    bar={stats?.staged_signatures ? 100 : 0} barColour="text-violet-500"
                                    sub="Intelligence staging area" glow="shadow-[0_0_20px_rgba(139,92,246,0.07)]" />
                            </div>
                        </section>

                        {/* ── Revenue Metrics ──────────────────────────────── */}
                        <section>
                            <p className="text-[9px] uppercase text-zinc-600 tracking-widest mb-4">▸ Revenue & Liability</p>
                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                                <OrganCard label="Total Carry" value={L(stats?.total_carry_usd)} unit="USD"
                                    bar={100} barColour="text-rose-500" sub="Fees + Settlements" />
                                <OrganCard label="Voucher Liability" value={L(stats?.active_vouchers_usd)} unit="USD"
                                    bar={60} barColour="text-indigo-500" sub="Active workforce exposure" />
                                <OrganCard label="Efficiency Rate" value={L(stats?.efficiency_rate)} unit="%"
                                    bar={stats?.efficiency_rate ?? 0} barColour="text-amber-500"
                                    sub="Scout leads / total seen" glow="shadow-[0_0_20px_rgba(245,158,11,0.07)]" />
                            </div>
                        </section>
                    </div>

                    {/* Footer */}
                    <div className="px-8 py-4 border-t border-zinc-800/60 flex items-center justify-between">
                        <div className="flex gap-4">
                            <div className="flex items-center gap-2">
                                <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                                <span className="text-[10px] text-zinc-500 uppercase">Settlement Engine: ONLINE</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse delay-75" />
                                <span className="text-[10px] text-zinc-500 uppercase">Revenue Bot: ACTIVE</span>
                            </div>
                        </div>
                        <span className="text-[9px] text-zinc-700 font-mono">VERA_CORE_V1.2</span>
                    </div>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
};

export default Executive;
