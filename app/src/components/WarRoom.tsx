import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface Bounty {
    scout_alias: string;
    target: string;
    score: number;
    payout_eth: number;
    timestamp: number | string;
    initial_detected_at?: number | string;
    type: string;
    liquidity?: number;
    heuristic?: string;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const formatTs = (ts: number | string | undefined | null): string => {
    const opts: Intl.DateTimeFormatOptions = { hour: '2-digit', minute: '2-digit' };
    if (ts === undefined || ts === null) return new Date().toLocaleTimeString([], opts);
    if (typeof ts === 'string') {
        const d = new Date(ts);
        return isNaN(d.getTime()) ? new Date().toLocaleTimeString([], opts) : d.toLocaleTimeString([], opts);
    }
    if (ts === 0 || isNaN(ts)) return new Date().toLocaleTimeString([], opts);
    return new Date(ts * 1000).toLocaleTimeString([], opts);
};

// ── Badges ────────────────────────────────────────────────────────────────────

const ThreatDNABadge = ({ type, heuristic }: { type: string; heuristic?: string }) => {
    const label = heuristic || type;
    const isTriage = type === 'TRIAGE_ALERT';
    return (
        <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold tracking-widest uppercase border ${isTriage
            ? 'bg-amber-950/60 text-amber-400 border-amber-700/50'
            : 'bg-rose-950/60 text-rose-400 border-rose-700/50'}`}>
            {isTriage ? '⚠' : '☠'} {label.slice(0, 16)}
        </span>
    );
};

const RiskBadge = ({ score }: { score: number }) => {
    const colour = score >= 80 ? 'text-red-400 border-red-700/50 bg-red-950/40'
        : score >= 60 ? 'text-orange-400 border-orange-700/50 bg-orange-950/40'
            : score >= 40 ? 'text-yellow-400 border-yellow-700/50 bg-yellow-950/40'
                : 'text-green-400 border-green-700/50 bg-green-950/40';
    return (
        <span className={`px-1 py-0.5 rounded border text-[9px] font-mono font-bold shrink-0 ${colour}`}>
            {score}
        </span>
    );
};

// ── Deep Scan Panel ───────────────────────────────────────────────────────────

const DeepScanView = ({ bounty, onClose }: { bounty: Bounty; onClose: () => void }) => (
    <motion.div
        key="deep-scan"
        initial={{ opacity: 0, x: 24 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: 24 }}
        className="flex-1 min-h-0 bg-zinc-950 border border-zinc-800 rounded-xl p-4 overflow-y-auto flex flex-col gap-3"
    >
        <div className="flex items-start justify-between gap-2">
            <div>
                <p className="text-[9px] text-zinc-500 uppercase tracking-widest mb-1">Deep Scan // Target Profile</p>
                <p className="text-xs font-mono text-white break-all">{bounty.target}</p>
            </div>
            <button onClick={onClose} className="text-[10px] text-zinc-500 hover:text-white border border-zinc-700 px-2 py-1 rounded font-mono shrink-0">[ESC]</button>
        </div>

        <div className="p-2.5 border border-zinc-800 rounded-lg flex flex-col gap-1.5">
            <p className="text-[9px] text-zinc-500 uppercase tracking-widest">Threat DNA</p>
            <div className="flex items-center gap-2 flex-wrap">
                <ThreatDNABadge type={bounty.type} heuristic={bounty.heuristic} />
                <RiskBadge score={bounty.score} />
            </div>
        </div>

        <div className="grid grid-cols-2 gap-2">
            <div className="p-2.5 border border-zinc-800 rounded-lg">
                <p className="text-[9px] text-zinc-500 uppercase tracking-widest mb-1">Potential Loot</p>
                <p className="text-base font-bold font-mono text-emerald-400">
                    {bounty.liquidity != null ? `$${bounty.liquidity.toLocaleString()}` : `+${(bounty.payout_eth ?? 0).toFixed(4)} ETH`}
                </p>
            </div>
            <div className="p-2.5 border border-zinc-800 rounded-lg">
                <p className="text-[9px] text-zinc-500 uppercase tracking-widest mb-1">Scout</p>
                <p className="text-xs font-mono text-indigo-400">@{bounty.scout_alias}</p>
            </div>
        </div>

        <div className="p-2.5 border border-zinc-800 rounded-lg">
            <p className="text-[9px] text-zinc-500 uppercase tracking-widest mb-1.5">Timeline</p>
            <div className="flex flex-col gap-0.5 text-[10px] font-mono">
                <div className="flex justify-between"><span className="text-zinc-500">First detected</span><span className="text-zinc-300">{formatTs(bounty.initial_detected_at ?? bounty.timestamp)}</span></div>
                <div className="flex justify-between"><span className="text-zinc-500">Last seen</span><span className="text-zinc-300">{formatTs(bounty.timestamp)}</span></div>
            </div>
        </div>

        <div className="p-2.5 border border-zinc-800 rounded-lg">
            <p className="text-[9px] text-zinc-500 uppercase tracking-widest mb-1.5">Risk Score</p>
            <div className="flex items-center gap-2">
                <div className="flex-1 bg-zinc-800 rounded-full h-1.5 overflow-hidden">
                    <div className={`h-full rounded-full ${bounty.score >= 80 ? 'bg-red-500' : bounty.score >= 60 ? 'bg-orange-500' : 'bg-yellow-500'}`}
                        style={{ width: `${bounty.score}%` }} />
                </div>
                <span className="text-xs font-mono font-bold text-white">{bounty.score}</span>
            </div>
        </div>
    </motion.div>
);

// ── Compact Strip ────────────────────────────────────────────────────────────

const BountyStrip = ({ b, onClick, active }: { b: Bounty; onClick: () => void; active: boolean }) => (
    <button
        onClick={onClick}
        className={`w-full text-left px-3 py-2 border-b transition-colors flex items-center gap-2 min-w-0
            ${active ? 'bg-rose-950/20 border-rose-800/40' : 'border-zinc-800/50 hover:bg-zinc-800/30'}`}
    >
        {/* Risk dot */}
        <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${b.score >= 80 ? 'bg-red-500' : b.score >= 60 ? 'bg-orange-500' : b.score >= 40 ? 'bg-yellow-500' : 'bg-green-500'}`} />
        {/* Main info */}
        <div className="flex-1 min-w-0 flex flex-col gap-0.5">
            <div className="flex items-center justify-between gap-1">
                <span className="text-[9px] font-mono text-zinc-400 truncate">
                    {b.target.startsWith('0x') ? `${b.target.slice(0, 6)}…${b.target.slice(-4)}` : b.target}
                </span>
                <span className="text-[9px] font-mono text-emerald-400 shrink-0">
                    {b.liquidity != null ? `$${(b.liquidity / 1000).toFixed(0)}K` : `+${(b.payout_eth ?? 0).toFixed(2)}E`}
                </span>
            </div>
            <div className="flex items-center justify-between gap-1">
                <ThreatDNABadge type={b.type} heuristic={b.heuristic} />
                <span className="text-[8px] font-mono text-zinc-600 shrink-0">{formatTs(b.timestamp)}</span>
            </div>
        </div>
    </button>
);

// ── Main WarRoom Component ────────────────────────────────────────────────────

interface WarRoomProps {
    compact?: boolean; // compact=true → slim sidebar strips only, no deep scan expansion
}

const WarRoom: React.FC<WarRoomProps> = ({ compact = false }) => {
    const [bounties, setBounties] = useState<Bounty[]>([]);
    const [selected, setSelected] = useState<Bounty | null>(null);

    useEffect(() => {
        const fetchBounties = () => {
            fetch('http://localhost:8000/api/bounty_feed')
                .then(r => r.json())
                .then(d => { if (Array.isArray(d)) setBounties(d); })
                .catch(e => console.error('Bounty Feed Error:', e));
        };
        fetchBounties();
        const iv = setInterval(fetchBounties, 15000);
        return () => clearInterval(iv);
    }, []);

    if (bounties.length === 0) return null;

    // ── Compact / sidebar mode ────────────────────────────────────────────────
    if (compact) {
        return (
            <div className="flex flex-col flex-1 min-h-0">
                {/* Sidebar header */}
                <div className="flex items-center gap-2 px-3 py-2 border-b border-zinc-800/60 shrink-0">
                    <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse shrink-0" />
                    <span className="text-[9px] font-bold text-rose-300 tracking-widest uppercase">War Room</span>
                    <span className="ml-auto text-[8px] text-zinc-500">{bounties.length}</span>
                </div>
                {/* Scrollable strips */}
                <div className="flex-1 overflow-y-auto">
                    {bounties.map((b, i) => (
                        <motion.div key={i} initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.03 }}>
                            <BountyStrip
                                b={b}
                                active={selected?.target === b.target && selected?.timestamp === b.timestamp}
                                onClick={() => setSelected(prev =>
                                    prev?.target === b.target && prev?.timestamp === b.timestamp ? null : b
                                )}
                            />
                        </motion.div>
                    ))}
                </div>
                {/* Inline quick-view for compact mode */}
                <AnimatePresence mode="wait">
                    {selected && (
                        <motion.div
                            key="compact-scan"
                            initial={{ opacity: 0, y: 12 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: 12 }}
                            className="border-t border-zinc-800/60 p-3 bg-zinc-950 shrink-0 flex flex-col gap-2 max-h-64 overflow-y-auto"
                        >
                            <div className="flex items-center justify-between">
                                <p className="text-[9px] text-zinc-400 uppercase tracking-widest">Quick Scan</p>
                                <button onClick={() => setSelected(null)} className="text-[9px] text-zinc-500 hover:text-white">[x]</button>
                            </div>
                            <p className="text-[10px] font-mono text-white break-all">{selected.target}</p>
                            <div className="flex items-center gap-2 flex-wrap">
                                <ThreatDNABadge type={selected.type} heuristic={selected.heuristic} />
                                <RiskBadge score={selected.score} />
                            </div>
                            <p className="text-xs font-mono text-emerald-400 font-bold">
                                {selected.liquidity != null ? `$${selected.liquidity.toLocaleString()}` : `+${(selected.payout_eth ?? 0).toFixed(4)} ETH`}
                            </p>
                            <div className="flex justify-between text-[9px] font-mono text-zinc-500">
                                <span>Scout: @{selected.scout_alias}</span>
                                <span>{formatTs(selected.timestamp)}</span>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        );
    }

    // ── Full / standalone mode ─ sidebar + deep scan ───────────────────────────
    return (
        <div className="w-full px-4 py-6">
            <div className="flex items-center gap-3 mb-4">
                <div className="w-2 h-2 rounded-full bg-rose-500 animate-pulse shadow-[0_0_8px_rgba(244,63,94,0.8)]" />
                <span className="text-xs font-bold text-rose-100 tracking-widest uppercase font-mono">War Room // Active Bounties</span>
                <span className="ml-auto text-[10px] text-zinc-500 font-mono">{bounties.length} targets</span>
            </div>

            <div className="flex gap-3 min-h-[400px]">
                {/* Sidebar */}
                <div className="w-[300px] shrink-0 flex flex-col overflow-y-auto max-h-[600px]">
                    {bounties.map((b, i) => {
                        const isActive = selected?.target === b.target && selected?.timestamp === b.timestamp;
                        return (
                            <motion.div key={i} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.04 }}>
                                <BountyStrip b={b} active={isActive} onClick={() => setSelected(isActive ? null : b)} />
                            </motion.div>
                        );
                    })}
                </div>

                {/* Deep Scan center */}
                <AnimatePresence mode="wait">
                    {selected ? (
                        <DeepScanView key={selected.target + selected.timestamp} bounty={selected} onClose={() => setSelected(null)} />
                    ) : (
                        <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                            className="flex-1 flex flex-col items-center justify-center gap-3 border border-dashed border-zinc-800 rounded-xl text-zinc-600">
                            <div className="w-8 h-8 rounded-full border border-zinc-700 flex items-center justify-center text-lg">⚔</div>
                            <p className="text-xs font-mono">Select a target to Deep Scan</p>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
};

export default WarRoom;
