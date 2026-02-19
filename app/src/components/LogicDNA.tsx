import React from 'react';
import { motion } from 'framer-motion';

interface LogicDNAProps {
    score: number;
    complexity?: string;
    isSafe: boolean;
}

const LogicDNA: React.FC<LogicDNAProps> = ({ score, complexity = "Standard", isSafe }) => {
    // Color Logic based on Score
    const primaryColor = isSafe ? 'text-emerald-500' : score > 50 ? 'text-amber-500' : 'text-red-500';
    const borderColor = isSafe ? 'border-emerald-500' : score > 50 ? 'border-amber-500' : 'border-red-500';
    const glowColor = isSafe ? 'shadow-emerald-500/50' : score > 50 ? 'shadow-amber-500/50' : 'shadow-red-500/50';
    const bgGradient = isSafe ? 'from-emerald-500/20' : score > 50 ? 'from-amber-500/20' : 'from-red-900/40';

    // Unfolding Animation Variants
    const containerVariants = {
        hidden: { scale: 0.5, opacity: 0, rotate: -90 },
        visible: {
            scale: 1,
            opacity: 1,
            rotate: 0,
            transition: { duration: 1.5, ease: "easeInOut" }
        }
    };

    return (
        <div className="relative w-full h-64 flex items-center justify-center overflow-hidden bg-slate-900 rounded-2xl border border-slate-800 mb-8">

            {/* Background Grid */}
            <div className="absolute inset-0 opacity-20"
                style={{ backgroundImage: 'radial-gradient(circle, #334155 1px, transparent 1px)', backgroundSize: '20px 20px' }}>
            </div>

            {/* Central "DNA" Structure */}
            <motion.div
                className="relative z-10 w-48 h-48"
                initial="hidden"
                animate="visible"
                variants={containerVariants}
            >

                {/* Orbital Rings */}
                {[...Array(3)].map((_, i) => (
                    <motion.div
                        key={i}
                        className={`absolute inset-0 rounded-full border ${borderColor} opacity-30`}
                        style={{ borderStyle: i === 1 ? 'dashed' : 'solid' }}
                        animate={{
                            rotate: i % 2 === 0 ? 360 : -360,
                            scale: [1, 1.1, 1],
                        }}
                        transition={{
                            rotate: { duration: 10 + i * 5, repeat: Infinity, ease: "linear" },
                            scale: { duration: 3, repeat: Infinity, ease: "easeInOut", delay: i }
                        }}
                    />
                ))}

                {/* Core Crystal */}
                <div className="absolute inset-12 flex items-center justify-center">
                    <motion.div
                        className={`absolute inset-0 ${borderColor} border-2 backdrop-blur-sm bg-gradient-to-br ${bgGradient} to-transparent shadow-lg ${glowColor}`}
                        initial={{ scale: 0, rotate: 45 }}
                        animate={{ scale: 1, rotate: [45, 225] }}
                        transition={{ duration: 1.5, ease: "easeOut" }}
                    />
                    <div className={`relative z-10 text-4xl font-bold ${primaryColor}`}>{score}</div>
                </div>

                {/* Data Particles */}
                {[...Array(8)].map((_, i) => (
                    <motion.div
                        key={`p-${i}`}
                        className={`absolute w-2 h-2 rounded-full ${isSafe ? 'bg-emerald-400' : 'bg-red-400'}`}
                        initial={{ opacity: 0 }}
                        animate={{
                            opacity: [0, 1, 0],
                            x: Math.cos(i * 45 * (Math.PI / 180)) * 80,
                            y: Math.sin(i * 45 * (Math.PI / 180)) * 80,
                        }}
                        transition={{
                            duration: 2,
                            repeat: Infinity,
                            delay: i * 0.2,
                            ease: "easeOut"
                        }}
                        style={{ top: '50%', left: '50%' }}
                    />
                ))}
            </motion.div>

            <div className="absolute bottom-4 left-4 text-xs font-mono text-slate-500">
                LOGIC_TOPOLOGY: {complexity.toUpperCase()}
            </div>

            <div className="absolute top-4 right-4 text-xs font-mono text-slate-500 border border-slate-700 px-2 py-1 rounded">
                dna_seq_id: {Math.random().toString(36).substr(2, 6).toUpperCase()}
            </div>

        </div>
    );
};

export default LogicDNA;
