import React, { useEffect, useState } from 'react';

interface Bounty {
    scout_alias: string;
    target: string;
    score: number;
    payout_eth: number;
    timestamp: number;
    type: string;
}

const WarRoom: React.FC = () => {
    const [bounties, setBounties] = useState<Bounty[]>([]);

    useEffect(() => {
        const fetchBounties = () => {
            fetch('http://localhost:8000/api/bounty_feed')
                .then(res => res.json())
                .then(data => {
                    if (Array.isArray(data)) setBounties(data);
                })
                .catch(err => console.error("Bounty Feed Error:", err));
        };

        fetchBounties();
        const interval = setInterval(fetchBounties, 5000); // Poll every 5s (Simulate WebSocket)

        return () => clearInterval(interval);
    }, []);

    if (bounties.length === 0) return null;

    return (
        <div className="bg-black/80 border-b border-slate-800 backdrop-blur-md h-10 md:h-12 flex items-center overflow-hidden relative z-30 shadow-sm w-full max-w-[100vw]">
            {/* Label */}
            <div className="absolute left-0 bg-rose-900/90 px-3 md:px-4 h-full flex items-center gap-2 z-20 border-r border-rose-700/50 shadow-lg shadow-black/50">
                <div className="w-1.5 h-1.5 md:w-2 md:h-2 rounded-full bg-rose-500 animate-pulse shadow-[0_0_8px_rgba(244,63,94,0.8)]"></div>
                <span className="text-[10px] md:text-xs font-bold text-rose-100 tracking-widest whitespace-nowrap">
                    WAR ROOM
                </span>
            </div>

            {/* Ticker Content */}
            <div className="animate-marquee flex gap-8 md:gap-16 whitespace-nowrap pl-28 md:pl-44 items-center w-full">
                {bounties.map((b, i) => (
                    <div key={i} className="flex items-center gap-2 text-[10px] md:text-xs font-mono">
                        <span className="text-slate-500 hidden sm:inline">[{new Date(b.timestamp * 1000).toLocaleTimeString()}]</span>
                        <span className="text-rose-400 font-bold">BUST CONFIRMED</span>
                        <span className="text-slate-600">::</span>
                        <span className="text-white max-w-[100px] sm:max-w-none truncate">{b.target}</span>
                        <span className="text-slate-600">::</span>
                        <span className="text-indigo-400">@{b.scout_alias}</span>
                        <span className="bg-emerald-900/50 text-emerald-400 px-1.5 py-0.5 rounded border border-emerald-700/50 text-[9px] md:text-[10px] font-bold">
                            +{b.payout_eth.toFixed(3)} ETH
                        </span>
                    </div>
                ))}
            </div>

            {/* Gradient Fade */}
            <div className="absolute right-0 h-full w-12 md:w-24 bg-gradient-to-l from-black to-transparent z-20 pointer-events-none"></div>
        </div>
    );
};

export default WarRoom;
