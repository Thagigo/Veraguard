
import { useState } from 'react';
import WallOfShame from './WallOfShame';
import Leaderboard from './Leaderboard';

const SheriffsFrontier = () => {
    const [activeTab, setActiveTab] = useState<'bounty' | 'leaderboard'>('bounty');

    return (
        <div className="mt-8 pt-8 border-t border-slate-200 dark:border-slate-800 animate-slide-down">
            {/* Header & Tabs */}
            <div className="flex flex-col items-center mb-6">
                <div className="flex items-center gap-2 mb-4">
                    <span className="text-3xl">🤠</span>
                    <h3 className="font-bold text-amber-900 dark:text-amber-500 uppercase tracking-wider text-lg">The Sheriff's Frontier</h3>
                </div>

                <div className="flex p-1 bg-slate-100 dark:bg-slate-800 rounded-lg overflow-x-auto max-w-full no-scrollbar">
                    <button
                        onClick={() => setActiveTab('bounty')}
                        className={`px-4 py-2 text-xs font-bold uppercase tracking-wider rounded-md transition-all whitespace-nowrap ${activeTab === 'bounty'
                            ? 'bg-amber-500 text-white shadow-md'
                            : 'text-slate-500 hover:text-amber-600'
                            }`}
                    >
                        Bounty Board
                    </button>
                    <button
                        onClick={() => setActiveTab('leaderboard')}
                        className={`px-4 py-2 text-xs font-bold uppercase tracking-wider rounded-md transition-all whitespace-nowrap ${activeTab === 'leaderboard'
                            ? 'bg-emerald-600 text-white shadow-md'
                            : 'text-slate-500 hover:text-emerald-600'
                            }`}
                    >
                        Leaderboard
                    </button>
                </div>
            </div>

            {/* Content Area */}
            <div className="min-h-[400px]">
                {activeTab === 'bounty' ? (
                    <WallOfShame mode="carousel" />
                ) : (
                    <Leaderboard />
                )}
            </div>
        </div>
    );
};

export default SheriffsFrontier;
