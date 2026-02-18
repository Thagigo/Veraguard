import { useState, useEffect } from 'react';
import ScoutMonitor from './ScoutMonitor';

interface BrainStatus {
    scout_budget: number;
    scout_spend: number;
    staged_signatures: number;
    vault_solvency: string;
    status: string;
}

const ProtocolDashboard = ({ onClose, userId }: { onClose: () => void, userId: string }) => {
    const [status, setStatus] = useState<BrainStatus | null>(null);

    useEffect(() => {
        const fetchBrainStatus = async () => {
            try {
                // [HARDENING] Send Telegram InitData for Auth
                // In Prod: window.Telegram.WebApp.initData
                // In Dev: Use pre-signed token matching .env secrets (Generated for ID: 123456789)
                const initData = (window as any).Telegram?.WebApp?.initData || "auth_date=1771409053&query_id=AAG_DEV&user=%7B%22id%22%3A+123456789%2C+%22first_name%22%3A+%22Admin%22%2C+%22username%22%3A+%22admin%22%2C+%22last_name%22%3A+%22Test%22%2C+%22language_code%22%3A+%22en%22%2C+%22allows_write_to_pm%22%3A+true%7D&hash=95f52384f51459165582dd59d7bb9e32b5cf449cb1a08a3ab3350fb618d01f2b";

                const res = await fetch('http://localhost:8000/api/brain/status', {
                    headers: {
                        'X-Telegram-Init-Data': initData
                    }
                });

                if (res.status === 403 || res.status === 401) {
                    setStatus({
                        status: "ACCESS DENIED",
                        scout_budget: 0,
                        scout_spend: 0,
                        staged_signatures: 0,
                        vault_solvency: "LOCKED"
                    });
                    return;
                }

                const data = await res.json();
                setStatus(data);
            } catch (e) {
                setStatus({
                    status: "OFFLINE",
                    scout_budget: 0,
                    scout_spend: 0,
                    staged_signatures: 0,
                    vault_solvency: "UNKNOWN"
                });
            }
        };

        fetchBrainStatus();
        const interval = setInterval(fetchBrainStatus, 5000); // Poll status
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="fixed inset-0 z-[100] bg-black/95 text-green-500 font-mono p-4 overflow-hidden flex flex-col items-center justify-center animate-fade-in">
            <div className="max-w-2xl w-full border border-green-500/30 rounded-lg p-6 bg-black shadow-[0_0_50px_rgba(0,255,0,0.1)] relative">

                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 text-green-500 hover:text-white"
                >
                    [X] CLOSE
                </button>

                <h1 className="text-2xl font-bold mb-6 tracking-widest border-b border-green-500/30 pb-4">
                    PROTOCOL_COMMAND_INTERFACE // v2.0
                </h1>

                <div className="bg-slate-50 dark:bg-slate-800 p-4 rounded-xl border border-slate-200 dark:border-slate-700 mb-6">
                    <h3 className="text-sm font-bold text-slate-500 mb-2">Debug Tools</h3>
                    <div className="flex gap-2">
                        <button
                            onClick={() => {
                                if (!userId) {
                                    alert("User ID not available for debug action.");
                                    return;
                                }
                                fetch('http://localhost:8000/api/debug/reset', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ user_id: userId })
                                }).then(() => {
                                    alert("Credits Reset to 0");
                                    window.location.reload();
                                });
                            }}
                            className="px-3 py-2 bg-red-500/10 text-red-500 text-xs font-bold rounded hover:bg-red-500/20 transition-all border border-red-500/20"
                        >
                            ⚠️ Reset My Credits
                        </button>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">

                    <div className="p-4 border border-green-500/20 rounded">
                        <h3 className="text-xs uppercase opacity-50 mb-2">Autonomous Scout Budget</h3>
                        <div className="text-3xl font-bold flex items-baseline gap-2">
                            ${status?.scout_budget.toFixed(2) || "..."}
                            <span className="text-sm opacity-50">USD</span>
                        </div>
                        <div className="text-xs mt-2 opacity-70">
                            SPENT: -${status?.scout_spend.toFixed(2) || "0.00"}
                        </div>
                    </div>

                    <div className="p-4 border border-green-500/20 rounded">
                        <h3 className="text-xs uppercase opacity-50 mb-2">Live Signatures Staged</h3>
                        <div className="text-3xl font-bold animate-pulse">
                            {status?.staged_signatures || 0}
                        </div>
                        <div className="text-xs mt-2 opacity-70">
                            PENDING SYNC
                        </div>
                    </div>

                    <div className="p-4 border border-green-500/20 rounded md:col-span-2">
                        <h3 className="text-xs uppercase opacity-50 mb-2">Live Scout Terminal</h3>
                        <ScoutMonitor />
                    </div>

                    <div className="p-4 border border-green-500/20 rounded md:col-span-2">
                        <h3 className="text-xs uppercase opacity-50 mb-2">System Diagnostic</h3>
                        <div className="flex gap-4">
                            <div>
                                STATUS: <span className="text-white font-bold">{status?.status || "CONNECTING..."}</span>
                            </div>
                            <div>
                                VAULT: <span className="text-white font-bold">{status?.vault_solvency || "UNKNOWN"}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="text-xs opacity-40 text-center">
                    VERAGUARD AUTONOMOUS BRAIN EVOLUTION LOOP ACTIVE
                    <br />
                    ID: {Math.random().toString(36).substr(2, 9).toUpperCase()}
                </div>

            </div>
        </div>
    );
};

export default ProtocolDashboard;
