import { useState, useEffect } from 'react';

interface LandingPageProps {
    onConnect: () => void;
}

const LandingPage = ({ onConnect }: LandingPageProps) => {
    const [stats, setStats] = useState({
        busts: 0,
        deputies: 0,
        vault: "128.5 ETH" // Mocked/Preserved
    });

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const [wallRes, leaderRes] = await Promise.all([
                    fetch('http://localhost:8000/api/shame-wall'),
                    fetch('http://localhost:8000/api/leaderboard')
                ]);

                const wallData = await wallRes.json();
                const leaderData = await leaderRes.json();

                setStats(prev => ({
                    ...prev,
                    busts: wallData.length || 42,
                    deputies: leaderData.length || 12
                }));
            } catch (e) {
                console.error("Stats fetch failed", e);
            }
        };

        fetchStats();
    }, []);

    return (
        // 1. Dark Radial Gradient Background
        <div className="min-h-screen bg-[radial-gradient(circle_at_center,_#050505_0%,_#000000_100%)] text-white flex flex-col items-center justify-center relative overflow-hidden">

            {/* Background Grid & Noise */}
            <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-10 pointer-events-none"></div>
            <div className="absolute inset-0 bg-grid-slate-800/[0.05] bg-[length:60px_60px] pointer-events-none"></div>

            <div className="z-10 text-center max-w-5xl px-6 flex flex-col items-center">

                {/* 2. 3D Pulsing Shield (Custom SVG) */}
                <div className="mb-10 relative group">
                    <div className="absolute inset-0 bg-emerald-500/20 blur-[50px] rounded-full animate-pulse-slow group-hover:bg-emerald-500/30 transition-all duration-1000"></div>
                    <svg width="120" height="120" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="relative z-10 drop-shadow-[0_0_15px_rgba(16,185,129,0.5)]">
                        <path d="M12 2L3 7V12C3 17.52 7.02 22.46 12 23.59C16.98 22.46 21 17.52 21 12V7L12 2Z" fill="url(#shieldGradient)" stroke="#10B981" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                        <path d="M12 6L12 18" stroke="#064E3B" strokeWidth="1.5" strokeLinecap="round" />
                        <path d="M6 12L18 12" stroke="#064E3B" strokeWidth="1.5" strokeLinecap="round" />
                        <circle cx="12" cy="12" r="3" fill="#10B981" className="animate-ping" style={{ animationDuration: '3s' }} />
                        <defs>
                            <linearGradient id="shieldGradient" x1="12" y1="2" x2="12" y2="23.59" gradientUnits="userSpaceOnUse">
                                <stop stopColor="#065f46" stopOpacity="0.4" />
                                <stop offset="1" stopColor="#022c22" stopOpacity="0.9" />
                            </linearGradient>
                        </defs>
                    </svg>
                </div>

                {/* 3. High-Contrast Headline */}
                {/* 3. Fluid Keyframe Headline */}
                <h1 className="font-black tracking-tight mb-8 text-white drop-shadow-2xl leading-tight" style={{ fontSize: 'clamp(2rem, 5vw, 4.5rem)' }}>
                    MEDICALLY ACCURATE<br />
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-emerald-600">SECURITY FOR THE CHAIN</span>
                </h1>

                <p className="text-sm md:text-xl text-slate-500 mb-12 font-medium tracking-widest uppercase max-w-2xl mx-auto px-4">
                    Autonomous detection. Red-team simulations. Community-driven justice.
                </p>

                {/* 4. Secure My Wallet Button */}
                {/* 4. Semantic CTA */}
                <div className="flex flex-col items-center gap-4">
                    <button
                        onClick={onConnect}
                        className="group relative inline-flex items-center justify-center px-8 py-4 md:px-12 md:py-6 text-lg md:text-xl font-bold text-white transition-all duration-300 bg-emerald-600 font-mono rounded-xl hover:bg-emerald-500 hover:scale-105 hover:shadow-[0_0_30px_rgba(16,185,129,0.4)] active:scale-95 w-full md:w-auto"
                    >
                        <span className="absolute inset-0 border border-white/20 rounded-xl group-hover:border-white/40 transition-colors pointer-events-none"></span>
                        <span className="relative z-10 flex items-center gap-3">
                            INITIALIZE SECURITY
                            <svg className="w-6 h-6 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                            </svg>
                        </span>
                    </button>
                    <span className="text-xs text-slate-600 font-mono tracking-wider uppercase flex items-center gap-2 opacity-70">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500/50"></span>
                        Sign-in with Ethereum
                    </span>
                </div>

            </div>

            {/* 5. Live Stat Cards */}
            <div className="absolute bottom-12 w-full">
                <div className="max-w-6xl mx-auto px-6 grid grid-cols-1 md:grid-cols-3 gap-6">

                    {/* Card 1: Scams Neutralized */}
                    <div className="bg-slate-900/50 backdrop-blur-md border border-slate-800 rounded-xl p-6 flex flex-col items-center group hover:border-emerald-500/30 transition-colors">
                        <span className="text-slate-500 text-[10px] uppercase font-bold tracking-widest mb-2">Scams Neutralized</span>
                        <span className="text-3xl font-mono text-white font-bold group-hover:text-emerald-400 transition-colors">
                            {stats.busts > 0 ? stats.busts : "..."}
                        </span>
                    </div>

                    {/* Card 2: System Heartbeat */}
                    <div className="bg-slate-900/50 backdrop-blur-md border border-slate-800 rounded-xl p-6 flex flex-col items-center group hover:border-emerald-500/30 transition-colors">
                        <span className="text-slate-500 text-[10px] uppercase font-bold tracking-widest mb-2">System Heartbeat</span>
                        <div className="flex items-center gap-3">
                            <span className="relative flex h-3 w-3">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                            </span>
                            <span className="text-xl font-mono text-emerald-400 font-bold tracking-wider">ACTIVE</span>
                        </div>
                    </div>

                    {/* Card 3: Vault Value */}
                    <div className="bg-slate-900/50 backdrop-blur-md border border-slate-800 rounded-xl p-6 flex flex-col items-center group hover:border-emerald-500/30 transition-colors">
                        <span className="text-slate-500 text-[10px] uppercase font-bold tracking-widest mb-2">Vault Security</span>
                        <span className="text-3xl font-mono text-white font-bold group-hover:text-amber-400 transition-colors">
                            {stats.vault}
                        </span>
                    </div>

                </div>
            </div>

        </div>
    );
};

export default LandingPage;
