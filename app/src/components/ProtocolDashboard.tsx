import { useState, useEffect } from 'react';
import ScoutMonitor from './ScoutMonitor';

// ── Types ─────────────────────────────────────────────────────────────────────
interface BrainStatus {
    scout_budget: number;
    scout_spend: number;
    staged_signatures: number;
    vault_solvency: string;
    status: string;
    brain_mode?: string;
    source_count?: number;
}

interface LastDiscovery {
    text: string;
    timestamp: number | string;
}

const API_BASE = "http://localhost:8000";

// ── Helpers ───────────────────────────────────────────────────────────────────
const HBDot = ({ active }: { active?: boolean }) => (
    <span className={`w-1.5 h-1.5 rounded-full shrink-0 inline-block ${active ? 'bg-emerald-400 animate-pulse' : 'bg-zinc-700'}`} />
);

const OrganCard = ({ label, value, sub, active, colour }: {
    label: string; value: string | number; sub?: string; active?: boolean; colour: string;
}) => (
    <div className={`p-4 border ${colour} rounded-xl bg-black/30 flex flex-col gap-1`}>
        <div className="flex items-center gap-1.5">
            <HBDot active={active} />
            <span className="text-[9px] opacity-40 uppercase tracking-widest">{label}</span>
        </div>
        <span className="text-xl font-bold font-mono">{value}</span>
        {sub && <span className="text-[9px] opacity-30">{sub}</span>}
    </div>
);

const fmtTs = (ts: number | string | null | undefined): string => {
    if (!ts) return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    if (typeof ts === 'string') {
        const d = new Date(ts);
        return isNaN(d.getTime()) ? '—' : d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    return new Date(ts * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

// ── GodMode Admin Overlay ─────────────────────────────────────────────────────
// This is NOT the end-user dashboard. It is the admin/operator diagnostic panel.
// The end-user audit input lives in DashboardHome.tsx.

const ProtocolDashboard = ({ onClose, userId }: { onClose: () => void; userId: string }) => {
    const [status, setStatus] = useState<BrainStatus | null>(null);
    const [lastDiscovery, setLastDiscovery] = useState<LastDiscovery | null>(null);

    useEffect(() => {
        const initData =
            (window as any).Telegram?.WebApp?.initData ||
            "auth_date=1771409053&query_id=AAG_DEV&user=%7B%22id%22%3A7695994098%2C%22first_name%22%3A%22Admin%22%2C%22username%22%3A%22admin%22%2C%22last_name%22%3A%22Test%22%2C%22language_code%22%3A%22en%22%2C%22allows_write_to_pm%22%3Atrue%7D&hash=f17a0ea19a0f07e0ab4bd7ae41a2f627be61e4e159eee4dd6a431e855f273d57";

        const poll = async () => {
            try {
                const res = await fetch(`${API_BASE}/api/brain/status`, { headers: { 'X-Telegram-Init-Data': initData } });
                if (res.ok) setStatus(await res.json());
                else setStatus(s => s ?? { status: res.status === 403 ? 'ACCESS DENIED' : 'OFFLINE', scout_budget: 0, scout_spend: 0, staged_signatures: 0, vault_solvency: 'LOCKED' });
            } catch {
                setStatus(s => s ?? { status: 'OFFLINE', scout_budget: 0, scout_spend: 0, staged_signatures: 0, vault_solvency: 'UNKNOWN' });
            }
            try {
                const r = await fetch(`${API_BASE}/api/brain/last_discovery`);
                if (r.ok) { const d = await r.json(); if (d?.text) setLastDiscovery(d); }
            } catch { /* silent */ }
        };

        poll();
        const iv = setInterval(poll, 15000);
        return () => clearInterval(iv);
    }, []);

    const ok = status?.status === 'OPERATIONAL';
    const grounded = status?.brain_mode === 'GROUNDED';
    const src = status?.source_count ?? 0;

    return (
        <div className="fixed inset-0 z-[100] bg-black/98 text-green-400 font-mono flex flex-col overflow-hidden">

            {/* ── Title bar ─────────────────────────────────────────────── */}
            <div className={`flex items-center gap-3 px-5 py-2 border-b text-[10px] shrink-0
                ${ok ? 'border-green-500/20' : 'border-red-500/20'}`}>
                <HBDot active={ok} />
                <span className="font-bold tracking-widest text-green-200">PROTOCOL // GOD MODE</span>
                <span className="text-zinc-600 ml-1">
                    VAULT:<strong className={ok ? ' text-emerald-400' : ' text-red-400'}> {ok ? 'UNLOCKED' : (status?.vault_solvency ?? '…')}</strong>
                </span>
                <span className="text-zinc-600">
                    BRAIN:<strong className={grounded ? ' text-cyan-400' : ' text-yellow-400'}>
                        {grounded ? ` GROUNDED${src > 0 ? ` (${src})` : ''}` : (status ? ' LOCAL' : ' …')}
                    </strong>
                </span>
                <span className="text-zinc-600">
                    SYS:<strong className={ok ? ' text-emerald-400' : ' text-red-400'}> {status?.status ?? 'CONNECTING…'}</strong>
                </span>
                <div className="ml-auto flex items-center gap-2">
                    <button onClick={onClose}
                        className="text-[10px] border border-zinc-700/50 px-2 py-0.5 rounded text-zinc-500 hover:text-white hover:border-white transition-colors">
                        [ESC]
                    </button>
                </div>
            </div>

            {/* ── Body ────────────────────────────────────────────────────── */}
            <div className="flex flex-1 min-h-0 overflow-hidden">

                {/* Main diagnostics column */}
                <div className="flex-1 min-w-0 overflow-y-auto flex flex-col gap-0">

                    {/* Sovereign Surgeon Map */}
                    <section className="p-5 border-b border-zinc-800/40">
                        <p className="text-[9px] uppercase opacity-30 tracking-widest mb-3">▸ Sovereign Surgeon Map</p>
                        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                            <OrganCard
                                label="Scout Budget" active={ok}
                                value={`$${status?.scout_budget?.toFixed?.(2) ?? '...'}`}
                                sub={`Spent: $${status?.scout_spend?.toFixed?.(2) ?? '0.00'}`}
                                colour="border-green-500/20 text-green-400"
                            />
                            <OrganCard
                                label="Vault" active={ok}
                                value={ok ? 'UNLOCKED' : (status?.vault_solvency ?? 'UNKNOWN')}
                                sub={status?.vault_solvency ?? '—'}
                                colour={ok ? "border-emerald-500/20 text-emerald-400" : "border-red-500/20 text-red-400"}
                            />
                            <OrganCard
                                label="Brain" active={grounded}
                                value={grounded ? 'GROUNDED' : 'LOCAL'}
                                sub={grounded ? `${src > 0 ? `${src} sources · ` : ''}${status?.staged_signatures ?? 0} staged` : 'No cloud connection'}
                                colour={grounded ? "border-cyan-500/20 text-cyan-400" : "border-yellow-500/20 text-yellow-400"}
                            />
                            <OrganCard
                                label="Chain Listener" active
                                value="ACTIVE"
                                sub="eth_subscribe / live"
                                colour="border-indigo-500/20 text-indigo-400"
                            />
                        </div>
                    </section>

                    {/* Reasoning Trace */}
                    <section className="p-5 border-b border-zinc-800/40">
                        <p className="text-[9px] uppercase opacity-30 tracking-widest mb-3">▸ Reasoning Trace // Last Discovery</p>
                        {lastDiscovery ? (
                            <div className="p-4 border border-cyan-500/15 rounded-xl bg-cyan-950/10">
                                <pre className="text-[10px] text-cyan-300 whitespace-pre-wrap leading-relaxed max-h-44 overflow-y-auto opacity-80">
                                    {lastDiscovery.text}
                                </pre>
                                <p className="text-[9px] opacity-25 mt-2">
                                    Staged: {fmtTs(lastDiscovery.timestamp)}
                                </p>
                            </div>
                        ) : (
                            <p className="text-xs opacity-25 italic">No staged candidates. Run brain_monitor to populate.</p>
                        )}
                    </section>

                    {/* Debug — admin only */}
                    <section className="p-5 border-b border-zinc-800/40">
                        <p className="text-[9px] uppercase opacity-30 tracking-widest mb-3">▸ Admin Controls</p>
                        <div className="flex gap-2">
                            <button onClick={() => {
                                if (!userId) return;
                                fetch(`${API_BASE}/api/debug/reset`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ user_id: userId }) })
                                    .then(() => { alert('Credits reset'); window.location.reload(); });
                            }} className="px-3 py-1.5 text-[10px] font-bold bg-red-500/10 text-red-400 border border-red-500/20 rounded hover:bg-red-500/20 transition-colors">
                                Reset Credits
                            </button>
                            <button onClick={() => {
                                if (confirm('DANGER: Delete ALL data?')) {
                                    fetch(`${API_BASE}/api/debug/wipeout`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ user_id: userId }) })
                                        .then(() => { alert('WIPEOUT COMPLETE'); window.location.reload(); });
                                }
                            }} className="px-3 py-1.5 text-[10px] font-bold bg-red-700/60 text-white border border-red-700/40 rounded hover:bg-red-700 transition-colors">
                                WIPEOUT
                            </button>
                        </div>
                    </section>

                    {/* Live Scout Terminal */}
                    <section className="p-5 flex-1">
                        <p className="text-[9px] uppercase opacity-30 tracking-widest mb-3">▸ Live Scout Terminal</p>
                        <div className="border border-green-500/15 rounded-xl p-3">
                            <ScoutMonitor />
                        </div>
                    </section>

                    <p className="text-[8px] opacity-10 text-center pb-3 font-mono">
                        BRAIN EVOLUTION LOOP · {Math.random().toString(36).substr(2, 9).toUpperCase()}
                    </p>
                </div>
            </div>
        </div>
    );
};

export default ProtocolDashboard;
