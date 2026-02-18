import { useState, useEffect, useRef } from 'react';

interface ScoutLog {
    timestamp: string;
    message: string;
    type: 'info' | 'success' | 'warning' | 'error' | 'alert' | 'skip' | 'system';
}

const ScoutMonitor = () => {
    const [logs, setLogs] = useState<ScoutLog[]>([]);
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const fetchLogs = async () => {
            try {
                const res = await fetch('http://localhost:8000/api/scout/logs');
                if (res.ok) {
                    const data = await res.json();
                    setLogs(data); // Backend returns deque as list, already sorted recent first? 
                    // Python deque appendleft means index 0 is newest. 
                    // responsive terminal usually puts newest at bottom. 
                    // Let's reverse purely for display if we want waterfall.
                }
            } catch (e) {
                // silent fail
            }
        };

        fetchLogs();
        const interval = setInterval(fetchLogs, 1000); // 1s polling for "Live" feel
        return () => clearInterval(interval);
    }, []);

    // Auto-scroll to bottom if strictly following terminal rules, 
    // but since we are polling a buffer that might replace history, 
    // let's just display the buffer as is.

    const getColor = (type: string) => {
        switch (type) {
            case 'alert': return 'text-red-500 animate-pulse font-bold';
            case 'success': return 'text-emerald-400';
            case 'warning': return 'text-yellow-400';
            case 'error': return 'text-red-600 bg-red-900/20';
            case 'skip': return 'text-slate-500';
            case 'system': return 'text-blue-400';
            default: return 'text-emerald-500/80';
        }
    };

    return (
        <div className="flex flex-col h-64 border border-green-500/20 rounded bg-black/50 overflow-hidden font-mono text-xs p-2">
            <div className="uppercase opacity-50 mb-2 border-b border-green-500/20 pb-1 flex justify-between">
                <span>Scout_Live_Feed.exe</span>
                <span className="animate-pulse">● REC</span>
            </div>
            <div className="flex-1 overflow-y-auto space-y-1 scrollbar-hide">
                {logs.map((log, i) => (
                    <div key={i} className="flex gap-2">
                        <span className="opacity-30">[{log.timestamp}]</span>
                        <span className={getColor(log.type)}>{log.message}</span>
                    </div>
                ))}
                {logs.length === 0 && <span className="opacity-30">Waiting for Scout data...</span>}
                <div ref={bottomRef} />
            </div>
        </div>
    );
};

export default ScoutMonitor;
