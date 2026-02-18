
import { useEffect, useState } from 'react';

interface LeaderboardEntry {
    user_id: string;
    sheriff_score: number;
    first_finds: number;
    referrals: number;
}

const Leaderboard = () => {
    const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch('http://localhost:8000/api/leaderboard')
            .then(res => res.json())
            .then(data => {
                setEntries(data);
                setLoading(false);
            })
            .catch(err => {
                console.error("Failed to fetch Leaderboard", err);
                setLoading(false);
            });
    }, []);

    const getMedal = (rank: number) => {
        switch (rank) {
            case 0: return "🥇";
            case 1: return "🥈";
            case 2: return "🥉";
            default: return `#${rank + 1}`;
        }
    };

    if (loading) return <div className="p-8 text-center animate-pulse text-xs font-mono tracking-widest uppercase">Syncing Deputy Rankings...</div>;

    return (
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
            <div className="p-6 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50">
                <h2 className="text-xl font-bold flex items-center gap-2 text-slate-700 dark:text-slate-200">
                    <span>🏆</span> Deputy Leaderboard
                </h2>
                <p className="text-xs text-slate-500 mt-1">
                    Ranked by <b>Sheriff Score</b>: (Referrals × 10) + (First Finds × 50)
                </p>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                    <thead className="bg-slate-100 dark:bg-slate-900/50 text-slate-500 uppercase text-[10px] font-bold tracking-wider">
                        <tr>
                            <th className="p-4 w-16 text-center">Rank</th>
                            <th className="p-4">Deputy ID</th>
                            <th className="p-4 text-center">First Finds 🤠</th>
                            <th className="p-4 text-center">Referrals 🔗</th>
                            <th className="p-4 text-right">Sheriff Score ⭐</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                        {entries.map((entry, idx) => (
                            <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors">
                                <td className="p-4 text-center font-bold text-lg">
                                    {getMedal(idx)}
                                </td>
                                <td className="p-4 font-mono font-medium text-slate-700 dark:text-slate-300 flex items-center gap-2">
                                    {entry.is_member && <span title="Vera-Pass Member (1.5x Multiplier)" className="cursor-help text-base">👑</span>}
                                    {entry.user_id}
                                    {idx === 0 && <span className="ml-2 text-[10px] bg-yellow-100 text-yellow-800 px-1 rounded border border-yellow-200">SHERIFF</span>}
                                </td>
                                <td className="p-4 text-center font-mono text-amber-600 dark:text-amber-500 font-bold">
                                    {entry.first_finds}
                                </td>
                                <td className="p-4 text-center text-slate-500 font-mono">
                                    {entry.referrals}
                                </td>
                                <td className="p-4 text-right font-black text-emerald-600 dark:text-emerald-400 font-mono text-lg">
                                    {entry.sheriff_score}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>

                {entries.length === 0 && (
                    <div className="p-8 text-center text-slate-400 text-sm font-mono opacity-75">
                        No deputies ranked yet. Start hunting to claim the badge!
                    </div>
                )}
            </div>
            <div className="p-4 bg-slate-50 dark:bg-slate-800/80 border-t border-slate-200 dark:border-slate-700 text-center">
                <p className="text-[10px] font-bold text-amber-600 dark:text-amber-500 uppercase tracking-widest animate-pulse">
                    Monthly Prize: Top 3 Sheriffs share the Yield Chest! 💰
                </p>
            </div>
        </div>
    );
};

export default Leaderboard;
