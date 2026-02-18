import { useState, useEffect } from 'react'

export default function TreasuryFlow() {
    const [animate, setAnimate] = useState(false);

    useEffect(() => {
        const interval = setInterval(() => {
            setAnimate(true);
            setTimeout(() => setAnimate(false), 2000); // Reset animation
        }, 5000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="mt-12 pt-8 border-t border-slate-200 dark:border-slate-800">
            <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-6">Medical-Grade Treasury Flow</h3>

            <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm relative overflow-hidden">

                {/* Flow Container */}
                <div className="flex flex-col md:flex-row items-center justify-between gap-8 relative z-10">

                    {/* Source: User/Splitter */}
                    <div className="text-center">
                        <div className="w-16 h-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center border-2 border-slate-300 mx-auto mb-2">
                            <span className="text-2xl">👤</span>
                        </div>
                        <p className="text-xs font-bold text-slate-600 dark:text-slate-400">User Fee</p>
                    </div>

                    {/* The Splitter Contract */}
                    <div className="flex-1 w-full relative h-1 md:h-px bg-slate-200 dark:bg-slate-700 my-4 md:my-0">
                        <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-white dark:bg-slate-900 px-2">
                            <div className="w-8 h-8 bg-emerald-100 dark:bg-emerald-900/30 rounded flex items-center justify-center border border-emerald-500/30">
                                <span className="text-xs font-mono font-bold text-emerald-600">⚡</span>
                            </div>
                        </div>
                        {/* Animation Dots */}
                        <div className={`absolute top-0 left-0 h-full bg-emerald-500 transition-all duration-1000 ${animate ? 'w-1/2 opacity-100' : 'w-0 opacity-0'}`}></div>
                        <div className={`absolute top-0 right-0 h-full bg-emerald-500 transition-all duration-1000 delay-1000 ${animate ? 'w-1/2 opacity-100' : 'w-0 opacity-0'}`}></div>
                    </div>

                    {/* Destinations */}
                    <div className="flex gap-4 md:gap-8">
                        {/* Vault */}
                        <div className="text-center group">
                            <div className="w-12 h-12 bg-emerald-50 dark:bg-emerald-900/10 rounded-full flex items-center justify-center border-2 border-emerald-500 mx-auto mb-2 transition-transform group-hover:scale-110">
                                <span className="text-sm font-bold text-emerald-600">60%</span>
                            </div>
                            <p className="text-[10px] font-bold uppercase tracking-wider text-emerald-600">Vault</p>
                        </div>
                        {/* Founder */}
                        <div className="text-center group">
                            <div className="w-12 h-12 bg-blue-50 dark:bg-blue-900/10 rounded-full flex items-center justify-center border-2 border-blue-400 mx-auto mb-2 transition-transform group-hover:scale-110">
                                <span className="text-sm font-bold text-blue-600">25%</span>
                            </div>
                            <p className="text-[10px] font-bold uppercase tracking-wider text-blue-600">Yield</p>
                        </div>
                        {/* War Chest */}
                        <div className="text-center group">
                            <div className="w-12 h-12 bg-amber-50 dark:bg-amber-900/10 rounded-full flex items-center justify-center border-2 border-amber-400 mx-auto mb-2 transition-transform group-hover:scale-110">
                                <span className="text-sm font-bold text-amber-600">15%</span>
                            </div>
                            <p className="text-[10px] font-bold uppercase tracking-wider text-amber-600">Chest</p>
                        </div>
                    </div>
                </div>

                <div className="mt-6 text-center">
                    <p className="text-xs text-slate-400">
                        Verifiable on-chain via <a href="#" className="underline decoration-dotted hover:text-emerald-500">VeraSplitter.sol</a>
                    </p>
                </div>

            </div>
        </div>
    )
}
