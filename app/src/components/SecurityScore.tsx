import React from 'react';

interface SecurityScoreProps {
    score: number;
    warnings: string[];
}

const SecurityScore: React.FC<SecurityScoreProps> = ({ score, warnings }) => {
    // Color Logic
    const getColor = (s: number) => {
        if (s >= 80) return 'text-emerald-500 border-emerald-500 shadow-emerald-200';
        if (s >= 50) return 'text-amber-500 border-amber-500 shadow-amber-200';
        return 'text-red-500 border-red-500 shadow-red-200';
    };

    const getRingColor = (s: number) => {
        if (s >= 80) return 'bg-emerald-500';
        if (s >= 50) return 'bg-amber-500';
        return 'bg-red-500';
    }

    const colorClass = getColor(score);
    const ringColorClass = getRingColor(score);

    return (
        <div className="flex flex-col items-center justify-center p-8 space-y-8 bg-slate-50 min-h-screen">

            {/* Score Visualization */}
            <div className="relative flex items-center justify-center w-64 h-64">
                {/* Breathing Pulse Ring */}
                <div className={`absolute w-full h-full rounded-full opacity-20 animate-ping ${ringColorClass}`}></div>
                <div className={`absolute w-56 h-56 rounded-full opacity-40 animate-pulse ${ringColorClass}`}></div>

                {/* Central Score Circle */}
                <div className={`relative flex items-center justify-center w-48 h-48 bg-white rounded-full border-8 shadow-xl ${colorClass}`}>
                    <div className="text-center">
                        <span className="block text-6xl font-bold">{score}</span>
                        <span className="text-sm font-medium text-slate-400 uppercase tracking-widest">Vera Score</span>
                    </div>
                </div>
            </div>

            {/* Evidence List */}
            <div className="w-full max-w-2xl space-y-4">
                <h3 className="text-xl font-semibold text-slate-800 text-center mb-6">Security Evidence</h3>

                {warnings.length === 0 ? (
                    <div className="p-4 bg-emerald-50 border border-emerald-100 rounded-lg flex items-center text-emerald-700">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span>No threats detected. Contract appears safe.</span>
                    </div>
                ) : (
                    warnings.map((warning, index) => (
                        <div key={index} className="group relative p-4 bg-white border border-slate-200 rounded-lg shadow-sm hover:shadow-md transition-shadow flex items-start justify-between">
                            <div className="flex items-start">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-red-500 mr-3 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                </svg>
                                <div>
                                    <span className="text-slate-700 font-medium">{warning}</span>
                                </div>
                            </div>

                            {/* Info Icon & Tooltip */}
                            <div className="relative">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-slate-400 hover:text-slate-600 cursor-help" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>

                                {/* Tooltip (Simulated logic for now, real implementation would map warning keys to descriptions) */}
                                <div className="absolute right-0 bottom-full mb-2 w-64 p-2 bg-slate-800 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                                    Risk Explanation: Potential exploit detected in contract logic.
                                    {warning.includes("Ghost Mint") && " Checks for pricing logic allowing zero-cost minting."}
                                    {warning.includes("UUPS") && " Proxy detected without upgrade function (Bricking Risk)."}
                                    {warning.includes("Fee") && " Logic detected that may drain native tokens."}
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default SecurityScore;
