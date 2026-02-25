
import { useEffect, useState } from 'react';

interface ShameReport {
    address: string;
    score: number;
    timestamp: number;
    scam_type: string;
    report_id: string;
    finder_display?: string; // [NEW]
}

const WallOfShame = ({ mode = 'grid' }: { mode?: 'grid' | 'carousel' }) => {
    const [reports, setReports] = useState<ShameReport[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch('http://localhost:8000/api/shame-wall')
            .then(res => res.json())
            .then(data => {
                setReports(data);
                setLoading(false);
            })
            .catch(err => {
                console.error("Failed to fetch Shame Wall", err);
                setLoading(false);
            });
    }, []);

    const handleShare = (report: ShameReport) => {
        // [UPDATED] Included Risk Score in text
        const text = `VeraGuard just took down a ${report.scam_type} scam at ${report.address.substring(0, 6)}... Risk Score: ${report.score}. Check the live vitals.`;
        const url = `${window.location.origin}?report_id=${report.report_id}&ref=MY_CODE`;

        if (navigator.share) {
            navigator.share({
                title: 'Wanted: Smart Contract Scam',
                text: text,
                url: url
            });
        } else {
            navigator.clipboard.writeText(`${text} ${url}`);
            alert("Sharable link copied to clipboard!");
        }
    };

    if (loading) return <div className="p-8 text-center animate-pulse text-amber-900">LOADING FRONTIER DATA...</div>;

    // Grid Layout (Legacy / Expanded)
    if (mode === 'grid') {
        return (
            <div className="p-4 bg-amber-50 dark:bg-slate-900/50 min-h-[50vh]">
                <h2 className="text-3xl font-extrabold text-center mb-8 text-amber-900 dark:text-amber-500 uppercase tracking-widest border-b-4 border-double border-amber-900/20 pb-4">
                    🤠 The Wall of Shame
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {reports.map((report, idx) => <WantedPoster key={idx} report={report} onShare={handleShare} />)}
                    {reports.length === 0 && (
                        <div className="col-span-full text-center py-12 opacity-50 font-mono">
                            Available bounties collected. The frontier is quiet... for now.
                        </div>
                    )}
                </div>
            </div>
        );
    }

    // Carousel Layout (New Frontier)
    return (
        <div className="w-full overflow-x-auto snap-x snap-mandatory flex gap-4 pb-8 px-4 custom-scrollbar">
            {reports.map((report, idx) => (
                <div key={idx} className="snap-center shrink-0 w-[80%] md:w-[40%] first:pl-2 last:pr-2">
                    <WantedPoster report={report} onShare={handleShare} />
                </div>
            ))}
            {reports.length === 0 && (
                <div className="w-full text-center py-12 opacity-50 font-mono">
                    The frontier is quiet... for now.
                </div>
            )}
        </div>
    );
};

// Sub-component for clean rendering
const WantedPoster = ({ report, onShare }: { report: ShameReport, onShare: (r: ShameReport) => void }) => (
    <div className="relative bg-[#f4e4bc] text-amber-950 p-6 rounded-sm shadow-[5px_5px_15px_rgba(0,0,0,0.3)] border-2 border-amber-900/30 h-full flex flex-col transition-transform hover:scale-[1.02] duration-300">
        {/* Rusty Nail Effect */}
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 w-4 h-4 rounded-full bg-stone-400 shadow-inner border border-stone-600 z-10"></div>

        {/* [NEW] Founder Badge */}
        {report.finder_display && report.finder_display !== "Unknown" && (
            <div className="absolute top-2 right-2 md:-right-2 rotate-12 bg-yellow-400 text-yellow-900 text-[10px] font-black uppercase px-2 py-1 rounded shadow-md border-2 border-yellow-600 z-20 animate-bounce-slow">
                ARRESTED BY: {report.finder_display}
            </div>
        )}

        <div className="border-4 border-amber-950 p-4 h-full flex flex-col items-center flex-1 relative bg-[url('/paper-texture.png')] bg-blend-multiply">
            <h3 className="text-4xl font-black uppercase mb-2 tracking-tighter drop-shadow-sm">WANTED</h3>
            <div className="text-xs font-bold uppercase tracking-widest mb-4 border-b border-amber-950 w-full text-center pb-1">For Crimes Against Crypto</div>

            <div className="w-full bg-amber-900/5 p-4 mb-4 grayscale flex items-center justify-center flex-1 min-h-[120px] relative">
                {/* Stamp Effect */}
                <div className="text-5xl font-mono font-bold text-center text-red-700/90 rotate-[-12deg] border-4 border-red-700/60 p-2 rounded-lg transform">
                    {report.score} <span className="text-sm block text-red-900 tracking-widest">VERA-SCORE</span>
                </div>
            </div>

            <div className="w-full space-y-2 font-mono text-xs md:text-sm mb-6 bg-white/30 p-2 rounded">
                <div className="flex justify-between border-b border-amber-900/10 pb-1">
                    <span className="font-bold text-amber-900/70">CHARGE:</span>
                    <span className="text-red-900 font-bold truncate max-w-[120px]">{report.scam_type}</span>
                </div>
                <div className="flex justify-between border-b border-amber-900/10 pb-1">
                    <span className="font-bold text-amber-900/70">LOC:</span>
                    <span className="font-mono text-amber-950">{report.address.substring(0, 8)}...</span>
                </div>
                <div className="flex justify-between border-b border-amber-900/10 pb-1">
                    <span className="font-bold text-amber-900/70">DATE:</span>
                    <span className="text-amber-950">
                        {(() => {
                            const ts = report.timestamp;
                            if (!ts) return "Unknown Date";
                            const d = typeof ts === 'string' ? new Date(ts) : new Date(ts * 1000);
                            return isNaN(d.getTime()) ? "Unknown Date" : d.toLocaleDateString();
                        })()}
                    </span>
                </div>
            </div>

            <button
                onClick={() => onShare(report)}
                className="w-full py-3 bg-amber-900 text-amber-50 font-bold uppercase tracking-widest hover:bg-amber-800 transition-all hover:shadow-[0_4px_10px_rgba(120,53,15,0.4)] active:scale-95 flex items-center justify-center gap-2"
            >
                <span>📤 Share Bust</span>
            </button>
        </div>
    </div>
);

export default WallOfShame;
