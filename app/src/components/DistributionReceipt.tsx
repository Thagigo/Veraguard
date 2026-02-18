import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useState } from 'react';
import TreasuryFlow from './TreasuryFlow';

interface DistributionReceiptProps {
    amount: number;
    ethCost?: number;
    onComplete: () => void;
}

export default function DistributionReceipt({ amount, ethCost, onComplete }: DistributionReceiptProps) {
    const [showFlow, setShowFlow] = useState(false);

    useEffect(() => {
        // Reveal flow after entry animation
        setTimeout(() => setShowFlow(true), 500);

        const timer = setTimeout(() => {
            onComplete();
        }, 6000); // Extended time to see the flow
        return () => clearTimeout(timer);
    }, [onComplete]);

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.5, y: -200, x: 200 }}
                transition={{ duration: 0.5, exit: { duration: 0.8, ease: "easeIn" } }}
                className="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-md"
                onClick={onComplete} // Close on backdrop click
            >
                <div
                    className="bg-slate-900/95 border border-emerald-500/50 p-6 rounded-3xl shadow-[0_0_50px_rgba(16,185,129,0.3)] text-center max-w-2xl w-full mx-4 relative overflow-hidden pointer-events-auto"
                    onClick={(e) => e.stopPropagation()} // Prevent close on content click
                >

                    <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-transparent pointer-events-none"></div>

                    <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1, rotate: [0, 10, -10, 0] }}
                        transition={{ type: "spring", delay: 0.2 }}
                        className="w-16 h-16 bg-emerald-500 rounded-full mx-auto mb-4 flex items-center justify-center shadow-lg shadow-emerald-500/40 relative z-10"
                    >
                        <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                        </svg>
                    </motion.div>

                    <h3 className="text-xl font-bold text-white mb-2 relative z-10">Protocol Funded</h3>

                    {/* Treasury Flow Integration */}
                    {showFlow && <div className="relative z-10"><TreasuryFlow trigger={true} amount={ethCost || amount * 0.001} /></div>}

                    <div className="mt-6 flex justify-between items-center bg-slate-800/50 p-3 rounded-lg border border-slate-700/50 relative z-10">
                        <span className="text-xs text-slate-500 uppercase font-bold">Credits Added</span>
                        <span className="text-xl font-mono font-bold text-emerald-400">+{amount}</span>
                    </div>

                    <button
                        onClick={onComplete}
                        className="mt-6 w-full py-3 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white font-bold rounded-xl transition-colors border border-slate-700 relative z-50 cursor-pointer shadow-lg hover:shadow-emerald-500/10"
                    >
                        Close Receipt
                    </button>

                </div>
            </motion.div>
        </AnimatePresence>
    );
}
