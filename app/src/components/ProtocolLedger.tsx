import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

interface ProtocolLedgerProps {
    onClose: () => void;
    highlightHash?: string;
    amount?: number; // [NEW] Dynamic Amount
    source?: 'voucher' | 'purchase' | string; // [NEW] Source Awareness
    isPending?: boolean; // [NEW] Sheriff Pulse
    bountyClaimed?: boolean; // [NEW] Scout Glow
}

const ProtocolLedger: React.FC<ProtocolLedgerProps> = ({ onClose, highlightHash, amount = 3.00, source = 'purchase', isPending = false, bountyClaimed = false }) => {
    const [particles, setParticles] = useState<any[]>([]);

    const isVoucher = source === 'voucher';

    // Calculate Split
    const vault = amount * 0.60;
    const yield_ = amount * 0.25;
    const warchest = amount * 0.15;

    // ETH Value Approximation
    const ethValue = amount * 0.0016;

    useEffect(() => {
        const interval = setInterval(() => {
            const id = Math.random();
            const destination = Math.random();
            let target = '';
            let color = '';

            // 60/25/15 Split logic
            if (destination < 0.60) {
                target = 'vault'; // Or Founder if Voucher
                color = isVoucher ? 'bg-indigo-500' : 'bg-emerald-500';
            } else if (destination < 0.85) {
                target = 'yield';
                color = 'bg-amber-500';
            } else {
                target = 'warchest';
                color = 'bg-indigo-500';
                // Wait, if Voucher, 60% is Indigo. War Chest is also Indigo? 
                // Let's keep War Chest Indigo for consistency with "Blue Team"? 
                // Or maybe make War Chest Purple/Violet if Voucher uses Indigo?
                // Standard Logic: War Chest = Indigo.
                // Voucher Logic: Founder = Indigo?
                // Let's use Violet for Voucher-Base? Or just reuse Indigo.
            }

            setParticles(prev => [...prev.slice(-30), { id, target, color }]);
        }, 200);

        return () => clearInterval(interval);
    }, [isVoucher]);

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/95 backdrop-blur-xl p-4 animate-fade-in font-sans">
            <div className="w-full max-w-4xl h-[90vh] bg-slate-900/50 rounded-3xl border border-slate-800 relative overflow-hidden flex flex-col shadow-2xl">

                {/* Header: User Transaction & Source */}
                <div className="p-6 border-b border-slate-800 bg-slate-900/80 backdrop-blur z-20 flex justify-between items-start">
                    <div>
                        <div className="text-[10px] uppercase font-bold text-slate-500 tracking-widest mb-1">Incoming Transaction Source</div>
                        <div className="flex items-center gap-3">
                            {isVoucher ? (
                                <span className="px-2 py-1 bg-indigo-500/20 text-indigo-400 text-xs font-bold rounded border border-indigo-500/50">VERA-PASS VOUCHER</span>
                            ) : (
                                <span className="px-2 py-1 bg-emerald-500/20 text-emerald-400 text-xs font-bold rounded border border-emerald-500/50">ETH PURCHASE</span>
                            )}
                            <span className="text-slate-600">→</span>
                            <div className="font-mono text-xl text-white flex items-center gap-2">
                                <span className={isVoucher ? "text-indigo-400" : "text-emerald-400"}>{amount.toFixed(2)} CRD</span>
                            </div>
                        </div>
                    </div>
                    <button onClick={onClose} className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold rounded-lg border border-slate-700 transition-colors">
                        CLOSE LEDGER
                    </button>
                </div>

                {/* Vertical Distribution Flow */}
                <div className="flex-1 relative overflow-hidden flex flex-col items-center justify-center py-10">

                    {/* Emitter Point */}
                    <div className={`absolute top-0 w-1 h-10 bg-gradient-to-b ${isVoucher ? 'from-indigo-500' : 'from-emerald-500'} to-transparent`}></div>

                    {/* Flow Lines Background */}
                    <svg className="absolute inset-0 w-full h-full opacity-10 pointer-events-none">
                        <path d="M50% 0 L 50% 20% L 20% 50%" fill="none" stroke={isVoucher ? '#6366F1' : '#10B981'} strokeWidth="2" />
                        <path d="M50% 0 L 50% 20% L 80% 50%" fill="none" stroke="#F59E0B" strokeWidth="2" />
                        <path d="M50% 0 L 50% 20% L 50% 60%" fill="none" stroke="#6366F1" strokeWidth="2" />
                    </svg>

                    {/* Particles Layer */}
                    <div className="absolute inset-0 pointer-events-none">
                        {particles.map(p => (
                            <motion.div
                                key={p.id}
                                className={`absolute w-2 h-2 rounded-full ${p.color} shadow-lg shadow-${p.color}/50`}
                                initial={{ top: '5%', left: '50%', opacity: 1 }}
                                animate={{
                                    top: p.target === 'warchest' ? '70%' : '50%',
                                    left: p.target === 'vault' ? '20%' : p.target === 'yield' ? '80%' : '50%',
                                    opacity: 0
                                }}
                                transition={{ duration: 2.5, ease: "easeInOut" }}
                            />
                        ))}
                    </div>

                    {/* Cards Container */}
                    <div className="w-full grid grid-cols-3 gap-6 px-12 relative z-10 mt-10">
                        {/* 1. Security Vault OR Infrastructure Support */}
                        <div className={`bg-slate-800/80 border ${isVoucher ? 'border-indigo-500/20' : 'border-emerald-500/20'} rounded-2xl p-6 relative overflow-hidden group`}>
                            <div className={`absolute inset-0 ${isVoucher ? 'bg-indigo-500/5 group-hover:bg-indigo-500/10' : 'bg-emerald-500/5 group-hover:bg-emerald-500/10'} transition-colors`}></div>
                            <div className="text-4xl mb-4">{isVoucher ? '🏗️' : '🏦'}</div>
                            <div className="text-3xl font-bold text-white mb-1">60%</div>
                            <div className={`text-xs font-bold ${isVoucher ? 'text-indigo-400' : 'text-emerald-400'} uppercase tracking-wider mb-2`}>
                                {isVoucher ? 'Infrastructure Support' : 'Security Vault'}
                            </div>
                            <p className="text-[10px] text-slate-400 leading-relaxed">
                                {isVoucher
                                    ? "Allocated to Founder/Maintenance (Reserve) to support Ghost Agent & AI Nodes."
                                    : "Permanent insurance backing for protocol solvency. Funds are legally locked and auditable."
                                }
                            </p>
                        </div>

                        {/* 2. Scout War Chest */}
                        <div className={`bg-slate-800/80 border border-indigo-500/20 rounded-2xl p-6 relative overflow-hidden group mt-12 ${bountyClaimed ? 'shadow-lg shadow-indigo-500/50 ring-1 ring-indigo-400' : ''}`}>
                            <div className="absolute inset-0 bg-indigo-500/5 group-hover:bg-indigo-500/10 transition-colors"></div>
                            <div className="text-4xl mb-4">🤠</div>
                            <div className="text-3xl font-bold text-white mb-1">15%</div>
                            <div className="text-xs font-bold text-indigo-400 uppercase tracking-wider mb-2">Scout War Chest</div>
                            <p className="text-[10px] text-slate-400 leading-relaxed">
                                Funds the <strong className="text-indigo-300">Sheriff's Frontier</strong> prize pool. Bounties for top verifiers who find exploits.
                            </p>
                        </div>

                        {/* 3. Sheriff Yield */}
                        <div className={`bg-slate-800/80 border border-amber-500/20 rounded-2xl p-6 relative overflow-hidden group ${isPending ? 'shadow-lg shadow-amber-500/50 animate-pulse' : ''}`}>
                            <div className="absolute inset-0 bg-amber-500/5 group-hover:bg-amber-500/10 transition-colors"></div>
                            <div className="text-4xl mb-4">⭐</div>
                            <div className="text-3xl font-bold text-white mb-1">25%</div>
                            <div className="text-xs font-bold text-amber-400 uppercase tracking-wider mb-2">Sheriff Yield</div>
                            <p className="text-[10px] text-slate-400 leading-relaxed">
                                Immediate redistribution to active node operators and premium subscribers.
                            </p>
                        </div>
                    </div>

                </div>

                {/* Footer: Specific Breakdown */}
                <div className="bg-slate-900 border-t border-slate-800 p-6">
                    <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4">Specific Contribution Record</div>
                    <div className="grid grid-cols-4 gap-4 text-xs font-mono border border-slate-700/50 rounded-lg p-4 bg-black/20">
                        <div className="text-slate-400">ALLOCATION</div>
                        <div className="text-right text-slate-400">PERCENT</div>
                        <div className="text-right text-slate-400">CREDITS</div>
                        <div className="text-right text-slate-400">ETH VALUE</div>

                        <div className={`${isVoucher ? 'text-indigo-400' : 'text-emerald-400'} font-bold`}>
                            {isVoucher ? 'Infrastructure' : 'Protocol Vault'}
                        </div>
                        <div className="text-right text-white">60%</div>
                        <div className="text-right text-white">{vault.toFixed(2)} CRD</div>
                        <div className={`text-right ${isVoucher ? 'text-indigo-400' : 'text-emerald-400'}`}>{(ethValue * 0.60).toFixed(5)} ETH</div>

                        <div className="text-amber-400 font-bold">Sheriff Yield</div>
                        <div className="text-right text-white">25%</div>
                        <div className="text-right text-white">{yield_.toFixed(2)} CRD</div>
                        <div className="text-right text-amber-400">{(ethValue * 0.25).toFixed(5)} ETH</div>

                        <div className="text-indigo-400 font-bold">War Chest</div>
                        <div className="text-right text-white">15%</div>
                        <div className="text-right text-white">{warchest.toFixed(2)} CRD</div>
                        <div className="text-right text-indigo-400">{(ethValue * 0.15).toFixed(5)} ETH</div>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default ProtocolLedger;
