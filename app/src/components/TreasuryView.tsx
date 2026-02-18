

export default function TreasuryView() {
    // Determine color based on solvency (Mocked for now as "Healthy")
    const isSolvent = true;
    const balance = "5.0"; // Mocked matching backend

    return (
        <div className="mt-12 pt-8 border-t border-slate-200">
            <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-4">Security Vault Status</h3>

            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-center gap-6">

                {/* Simple CSS Donut Chart */}
                <div className="relative w-24 h-24 rounded-full bg-emerald-100 flex items-center justify-center">
                    <div className="absolute inset-0 rounded-full border-4 border-emerald-500" style={{ clipPath: 'polygon(0 0, 100% 0, 100% 100%, 0 100%)' }}></div>
                    <div className="bg-white w-16 h-16 rounded-full flex items-center justify-center z-10">
                        <span className="text-xl font-bold text-emerald-600">60%</span>
                    </div>
                </div>

                <div className="flex-1 text-center sm:text-left">
                    <h4 className="text-lg font-bold text-slate-800">Veraguard Treasury</h4>
                    <div className="flex items-center justify-center sm:justify-start gap-2 mt-1">
                        <span className={`inline-block w-2 h-2 rounded-full ${isSolvent ? 'bg-emerald-500' : 'bg-red-500'}`}></span>
                        <span className="text-sm text-slate-600 font-medium">{isSolvent ? 'Solvent & Active' : 'Insolvent'}</span>
                    </div>
                    <p className="text-xs text-slate-400 mt-2 max-w-sm">
                        Each audit contributes 60% to this vault (Current: {balance} ETH), strictly reserved for deep simulations and user protection.
                    </p>
                </div>

                <a
                    href="#"
                    onClick={(e) => e.preventDefault()} // Mock link
                    className="text-xs font-mono text-emerald-600 hover:underline hover:text-emerald-700 bg-emerald-50 px-3 py-2 rounded border border-emerald-100"
                >
                    View Contract ↗
                    <br />
                    <span className="opacity-50">0x1111...1111</span>
                </a>

            </div>
        </div>
    )
}
