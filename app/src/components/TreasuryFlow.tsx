import { useState, useEffect } from 'react'

interface TreasuryFlowProps {
    trigger: boolean;
    amount: number; // The amount of ETH (or credits) being split
}

export default function TreasuryFlow({ trigger, amount }: TreasuryFlowProps) {
    const [animate, setAnimate] = useState(false);

    useEffect(() => {
        if (trigger) {
            setAnimate(true);
            const timer = setTimeout(() => setAnimate(false), 3000); // 3s animation
            return () => clearTimeout(timer);
        }
    }, [trigger]);

    // Split Logic (60 / 25 / 15)
    // If amount is 0 (initial state), we can show percentages or 0
    const vaultAmount = amount * 0.60;
    const yieldAmount = amount * 0.25;
    const chestAmount = amount * 0.15;

    const formatAmt = (val: number) => val > 0 ? `${val.toFixed(6)}` : '';

    return (
        <div className="mt-12 pt-8 border-t border-slate-200 dark:border-slate-800">
            <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-6">Medical-Grade Treasury Flow</h3>

            <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm relative overflow-hidden">

                {/* Flow Container */}
                <div className="flex flex-col md:flex-row items-center justify-between gap-8 relative z-10">

                    {/* Source: User/Splitter */}
                    <div className="text-center min-w-[80px]">
                        <div className={`w-16 h-16 rounded-full flex items-center justify-center border-2 mx-auto mb-2 transition-all duration-500 ${animate ? 'bg-emerald-100 border-emerald-500 shadow-[0_0_15px_rgba(16,185,129,0.5)] scale-110' : 'bg-slate-100 dark:bg-slate-800 border-slate-300'}`}>
                            <span className="text-2xl">👤</span>
                        </div>
                        <p className="text-xs font-bold text-slate-600 dark:text-slate-400">
                            {amount > 0 ? `${amount.toFixed(6)} ETH` : 'User Fee'}
                        </p>
                    </div>

                    {/* The Splitter Contract */}
                    <div className="flex-1 w-full relative h-1 md:h-px bg-slate-200 dark:bg-slate-700 my-4 md:my-0">
                        <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-white dark:bg-slate-900 px-2 z-20">
                            <div className={`w-8 h-8 rounded flex items-center justify-center border transition-all duration-300 ${animate ? 'bg-emerald-500 border-emerald-600 scale-125 shadow-lg' : 'bg-emerald-100 dark:bg-emerald-900/30 border-emerald-500/30'}`}>
                                <span className={`text-xs font-mono font-bold ${animate ? 'text-white' : 'text-emerald-600'}`}>⚡</span>
                            </div>
                        </div>
                        {/* Animation Dots - Split Logic */}
                        <div className={`absolute top-0 left-1/2 h-full bg-emerald-500 transition-all duration-1000 ease-out origin-left ${animate ? 'w-1/2 opacity-100' : 'w-0 opacity-0'}`} style={{ transform: 'translateX(-100%) scaleX(-1)' }}></div>
                        <div className={`absolute top-0 left-1/2 h-full bg-emerald-500 transition-all duration-1000 ease-out ${animate ? 'w-1/2 opacity-100' : 'w-0 opacity-0'}`}></div>
                    </div>

                    {/* Destinations */}
                    <div className="flex gap-4 md:gap-8">
                        {/* Vault */}
                        <div className="text-center group min-w-[60px]">
                            <div className={`w-12 h-12 rounded-full flex items-center justify-center border-2 mx-auto mb-2 transition-all duration-1000 delay-700 ${animate ? 'bg-emerald-100 border-emerald-600 scale-110 shadow-md' : 'bg-emerald-50 dark:bg-emerald-900/10 border-emerald-500'}`}>
                                <span className="text-[10px] font-bold text-emerald-600">{formatAmt(vaultAmount) || '60%'}</span>
                            </div>
                            <p className="text-[10px] font-bold uppercase tracking-wider text-emerald-600">Vault</p>
                        </div>
                        {/* Founder */}
                        <div className="text-center group min-w-[60px]">
                            <div className={`w-12 h-12 rounded-full flex items-center justify-center border-2 mx-auto mb-2 transition-all duration-1000 delay-800 ${animate ? 'bg-blue-100 border-blue-600 scale-110 shadow-md' : 'bg-blue-50 dark:bg-blue-900/10 border-blue-400'}`}>
                                <span className="text-[10px] font-bold text-blue-600">{formatAmt(yieldAmount) || '25%'}</span>
                            </div>
                            <p className="text-[10px] font-bold uppercase tracking-wider text-blue-600">Yield</p>
                        </div>
                        {/* War Chest */}
                        <div className="text-center group min-w-[60px]">
                            <div className={`w-12 h-12 rounded-full flex items-center justify-center border-2 mx-auto mb-2 transition-all duration-1000 delay-900 ${animate ? 'bg-amber-100 border-amber-600 scale-110 shadow-md' : 'bg-amber-50 dark:bg-amber-900/10 border-amber-400'}`}>
                                <span className="text-[10px] font-bold text-amber-600">{formatAmt(chestAmount) || '15%'}</span>
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
