import { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface SecurityVerificationProps {
    onComplete: () => void;
}

export default function SecurityVerification({ onComplete }: SecurityVerificationProps) {
    useEffect(() => {
        const timer = setTimeout(() => {
            onComplete();
        }, 1500);
        return () => clearTimeout(timer);
    }, [onComplete]);

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0, scale: 1.1, filter: "blur(20px)" }}
                transition={{ duration: 0.5 }}
                className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/80 backdrop-blur-xl"
            >
                <div className="text-center space-y-6">
                    <div className="relative w-24 h-24 mx-auto">
                        <div className="absolute inset-0 border-4 border-emerald-500/30 rounded-full animate-ping"></div>
                        <div className="absolute inset-0 border-4 border-t-emerald-500 border-r-transparent border-b-emerald-500/50 border-l-transparent rounded-full animate-spin"></div>
                        <div className="absolute inset-4 bg-emerald-500/20 rounded-full backdrop-blur-sm flex items-center justify-center">
                            <svg className="w-8 h-8 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </div>
                    </div>

                    <div>
                        <h2 className="text-2xl font-bold text-white tracking-widest uppercase">Verifying Identity</h2>
                        <p className="text-emerald-400 font-mono text-sm mt-2 animate-pulse">ESTABLISHING SECURE PERIMETER...</p>
                    </div>

                    <div className="w-64 h-1 bg-slate-800 rounded-full mx-auto overflow-hidden">
                        <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: "100%" }}
                            transition={{ duration: 1.5, ease: "easeInOut" }}
                            className="h-full bg-emerald-500 shadow-[0_0_10px_#10b981]"
                        />
                    </div>
                </div>
            </motion.div>
        </AnimatePresence>
    );
}
