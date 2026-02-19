import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

import WantedPoster from './WantedPoster';
import ProtocolLedger from './ProtocolLedger'; // [NEW]

interface HistoryItem {
    id: string;
    type: 'purchase' | 'audit' | 'reward';
    amount_eth?: number;
    amount_usd?: number;
    score?: number;
    address?: string;
    timestamp: number;
    description: string;
    referee?: string;
    red_team_log?: any[]; // [NEW] Premium Check
    report_hash?: string; // [NEW] Ledger Link
}

export default function Vault({ userId }: { userId: string }) {
    const navigate = useNavigate();
    const [history, setHistory] = useState<HistoryItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<'ALL' | 'AUDIT' | 'PURCHASE'>('ALL');

    // [NEW] Ledger Modal State
    const [showLedger, setShowLedger] = useState(false);
    const [selectedLedgerHash, setSelectedLedgerHash] = useState<string | undefined>(undefined);

    useEffect(() => {
        fetchHistory();
    }, [userId]);

    const fetchHistory = async () => {
        try {
            const res = await fetch(`http://localhost:8000/api/user/history/${userId}`);
            if (res.ok) {
                const data = await res.json();
                if (Array.isArray(data)) {
                    setHistory(data);
                } else {
                    console.error("Invalid history format:", data);
                    setHistory([]);
                }
            }
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const handleViewLedger = (hash: string) => {
        setSelectedLedgerHash(hash);
        setShowLedger(true);
    }

    if (loading) return <div className="p-10 text-center text-slate-500 animate-pulse">Decrypting Vault Archives...</div>;

    return (
        <div className="min-h-screen bg-slate-900 text-slate-200 p-4 pb-20 relative">
            {/* [NEW] Protocol Ledger Modal */}
            <AnimatePresence>
                {showLedger && (
                    <ProtocolLedger
                        onClose={() => setShowLedger(false)}
                        highlightHash={selectedLedgerHash}
                    />
                )}
            </AnimatePresence>

            <div className="max-w-4xl mx-auto">
                <header className="mb-10 pt-10 border-b border-slate-800 pb-6 flex justify-between items-end">
                    <div>
                        <button
                            onClick={() => navigate('/')}
                            className="flex items-center gap-2 text-slate-400 hover:text-white mb-4 transition-colors group"
                        >
                            <span className="group-hover:-translate-x-1 transition-transform">←</span> Return to Dashboard
                        </button>
                        <h1 className="text-4xl font-bold text-white tracking-tight mb-2">The Vault</h1>
                        <p className="text-slate-400 font-mono text-sm">SECURE ARCHIVE OF ON-CHAIN ACTIVITY</p>
                    </div>
                    <div className="text-right">
                        <div className="text-xs text-slate-500 uppercase">Total Records</div>
                        <div className="text-2xl font-mono text-emerald-400">{history.length}</div>
                    </div>
                </header>

                {/* Filter Tabs */}
                <div className="flex gap-4 mb-8 border-b border-slate-800 pb-1">
                    {['ALL', 'AUDIT', 'PURCHASE'].map((f) => (
                        <button
                            key={f}
                            onClick={() => setFilter(f as any)}
                            className={`px-4 py-2 text-sm font-bold border-b-2 transition-colors ${filter === f ? 'border-emerald-500 text-white' : 'border-transparent text-slate-500 hover:text-slate-300'}`}
                        >
                            {f === 'AUDIT' ? 'AUDITS' : f === 'PURCHASE' ? 'PURCHASES' : f}
                        </button>
                    ))}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {history
                        .filter(item => filter === 'ALL' ? true : filter === 'AUDIT' ? item.type === 'audit' : item.type === 'purchase' || item.type === 'reward')
                        .length === 0 ? (
                        <div className="col-span-full text-center py-20 opacity-50">
                            <span className="text-6xl block mb-4">🕸️</span>
                            <p>The Archives are empty, Sheriff.</p>
                        </div>
                    ) : (
                        history
                            .filter(item => filter === 'ALL' ? true : filter === 'AUDIT' ? item.type === 'audit' : item.type === 'purchase' || item.type === 'reward')
                            .map((item, index) => (
                                <motion.div
                                    key={item.id}
                                    initial={{ opacity: 0, scale: 0.95 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    transition={{ delay: index * 0.1 }}
                                    className="group relative bg-[#0a0a0a] border border-slate-800 rounded-xl overflow-hidden hover:border-emerald-500/50 transition-all shadow-xl"
                                >
                                    {/* Museum Glass Reflection */}
                                    <div className="absolute inset-0 bg-gradient-to-tr from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-20" />

                                    <div className="flex h-full">
                                        {/* Left: Visual Evidence */}
                                        <div className="w-1/3 bg-black/50 border-r border-slate-800 p-4 flex items-center justify-center relative">
                                            {item.type === 'audit' && item.address ? (
                                                <WantedPoster address={item.address} risk={(item.score || 100) < 50 ? 'High' : 'Low'} className="w-full h-auto shadow-none border-none" />
                                            ) : (
                                                <div className="text-4xl">
                                                    {item.type === 'purchase' ? '💳' : '🎁'}
                                                </div>
                                            )}
                                            {item.type === 'audit' && (item.score || 0) < 50 && (
                                                <div className="absolute top-2 right-2 bg-red-600 text-white text-[10px] font-bold px-2 py-0.5 transform rotate-12 shadow-lg">
                                                    BUSTED
                                                </div>
                                            )}
                                        </div>

                                        {/* Right: The Record */}
                                        <div className="w-2/3 p-5 flex flex-col justify-between">
                                            <div>
                                                <div className="flex justify-between items-start mb-2">
                                                    <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest">{item.type} RECORD</span>
                                                    <span className="text-[10px] font-mono text-slate-600">
                                                        {new Date(item.timestamp * 1000).toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })} | {new Date(item.timestamp * 1000).toLocaleTimeString('en-US', { hour12: false })}
                                                    </span>
                                                </div>
                                                <h3 className="text-lg font-bold text-slate-200 leading-tight mb-1">{item.description}</h3>
                                                <div className="text-xs font-mono text-emerald-500/80 truncate">
                                                    {item.address || item.id}
                                                </div>
                                            </div>

                                            <div className="mt-4 pt-4 border-t border-dashed border-slate-800 flex justify-between items-end">
                                                <div>
                                                    <div className="text-[10px] text-slate-600 uppercase">Value/Score</div>
                                                    <div className="text-xl font-mono text-white">
                                                        {item.amount_eth ? `${item.amount_eth.toFixed(4)} ETH` : item.score ? `Score: ${item.score}` : '+Credits'}
                                                    </div>
                                                </div>
                                                {item.type === 'audit' && (
                                                    <div className="opacity-0 group-hover:opacity-100 transition-opacity flex flex-col gap-2 items-end">
                                                        <button
                                                            onClick={() => navigate(`/?report_id=${item.id}&ref=${userId}`)}
                                                            className="text-[10px] bg-slate-800 hover:bg-slate-700 text-white px-3 py-1 rounded border border-slate-700 hover:border-slate-500 transition-colors"
                                                        >
                                                            VIEW FULL REPORT
                                                        </button>
                                                        {item.red_team_log && item.red_team_log.length > 0 && (
                                                            <button
                                                                onClick={(e) => { e.stopPropagation(); handleViewLedger(item.report_hash || "0x_legacy_audit"); }}
                                                                className="text-[10px] bg-emerald-900/30 hover:bg-emerald-900/50 text-emerald-400 px-3 py-1 rounded border border-emerald-500/30 hover:border-emerald-500"
                                                            >
                                                                VIEW LEDGER
                                                            </button>
                                                        )}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </motion.div>
                            ))
                    )}
                </div>

            </div>
        </div >
    );
}
