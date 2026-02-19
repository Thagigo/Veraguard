import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface CrystallizationLoaderProps {
    tier?: 'triage' | 'deep';
}

const CrystallizationLoader: React.FC<CrystallizationLoaderProps> = ({ tier = 'deep' }) => {
    const [phase, setPhase] = useState(0);
    const [hexStream, setHexStream] = useState<string[]>([]);

    useEffect(() => {
        // Phase Sequencing
        if (tier === 'deep') {
            const t1 = setTimeout(() => setPhase(1), 2500); // 0->1: Decoding -> Mapping
            const t2 = setTimeout(() => setPhase(2), 5500); // 1->2: Mapping -> Simulating
            return () => {
                clearTimeout(t1);
                clearTimeout(t2);
            };
        }
        // Triage Mode: Stays in Phase 0 (Extraction) indefinitely (until parent unmounts)
    }, [tier]);

    useEffect(() => {
        // Hex Stream Generation (Faster for Triage)
        const speed = tier === 'triage' ? 50 : 100;
        const interval = setInterval(() => {
            setHexStream(prev => [
                ...prev.slice(-15),
                "0x" + Math.random().toString(16).substr(2, 8)
            ]);
        }, speed);

        return () => clearInterval(interval);
    }, [tier]);

    const theme = {
        triage: {
            glow: 'bg-emerald-500/5',
            border: 'border-emerald-500/30',
            text: 'text-emerald-500/80',
            title: 'text-emerald-400'
        },
        deep: {
            glow: 'bg-amber-500/5',
            border: 'border-amber-500/30',
            text: 'text-amber-500/80',
            title: 'text-amber-400'
        }
    }[tier];

    return (
        <div className="flex flex-col items-center justify-center p-8 bg-slate-900/50 rounded-2xl border border-slate-700/50 backdrop-blur-md w-full max-w-md mx-auto aspect-square relative overflow-hidden group">

            {/* Ambient Background Glow */}
            <div className={`absolute inset-0 transition-opacity duration-1000 pointer-events-none
                ${phase === 0 ? theme.glow : phase === 1 ? 'bg-indigo-500/5' : 'bg-red-500/10'}`}
            />

            <AnimatePresence mode="wait">
                {phase === 0 && (
                    <motion.div
                        key="phase1"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0, filter: "blur(10px)" }}
                        className={`flex flex-col items-center font-mono text-xs gap-1 ${theme.text}`}
                    >
                        <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
                            className={`w-12 h-12 border-2 border-dashed rounded-full mb-4 ${theme.border}`}
                        />
                        <div className={`uppercase tracking-widest font-bold mb-2 ${theme.title}`}>Phase I: Extraction</div>
                        {hexStream.map((hex, i) => (
                            <motion.div key={i} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1 - (i / 20), x: 0 }} className="text-[10px]">
                                {hex}
                            </motion.div>
                        ))}
                    </motion.div>
                )}

                {phase === 1 && (
                    <motion.div
                        key="phase2"
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 1.5 }}
                        className="flex flex-col items-center"
                    >
                        <div className="relative w-24 h-24 mb-6">
                            <motion.div
                                className="absolute inset-0 border border-indigo-500/50"
                                animate={{ rotate: [0, 90, 180, 270, 360], borderRadius: ["0%", "50%", "0%", "50%", "0%"] }}
                                transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                            />
                            <motion.div
                                className="absolute inset-4 border border-purple-500/50"
                                animate={{ rotate: [360, 270, 180, 90, 0], borderRadius: ["50%", "0%", "50%", "0%", "50%"] }}
                                transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                            />
                        </div>
                        <div className="uppercase tracking-widest font-bold text-indigo-400">Phase II: Mapping DNA</div>
                        <p className="text-slate-500 text-xs mt-2">Constructing Logic Graph...</p>
                    </motion.div>
                )}

                {phase === 2 && (
                    <motion.div
                        key="phase3"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="flex flex-col items-center w-full"
                    >
                        <div className="relative w-full h-16 mb-4 flex gap-1 items-center justify-center">
                            {[...Array(5)].map((_, i) => (
                                <motion.div
                                    key={i}
                                    className="w-2 bg-red-500/50 rounded-full"
                                    animate={{ height: ["10%", "80%", "30%"] }}
                                    transition={{ duration: 0.6, repeat: Infinity, repeatDelay: i * 0.1, ease: "easeInOut" }}
                                />
                            ))}
                        </div>
                        <div className="uppercase tracking-widest font-bold text-red-500 animate-pulse">Phase III: Red-Team Sim</div>
                        <p className="text-red-400/60 text-xs mt-2 text-center">Injecting exploited payloads (Virtual VM)...</p>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default CrystallizationLoader;
