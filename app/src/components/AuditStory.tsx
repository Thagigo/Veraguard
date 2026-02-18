import { useState, useEffect } from 'react'

const storySteps = [
    "Initializing Semantic Biopsy...",
    "Scanning Vital Signs (Liquidity & Auth)...",
    "Mapping Control Flow (AST Tomography)...",
    "Checking for Malignant Signatures...",
    "Running Deep Hunter Simulation (Prognosis)...",
    "Generating Medical Audit Report..."
]

export default function AuditStory() {
    const [currentStep, setCurrentStep] = useState(0)
    const [isMonitoring, setIsMonitoring] = useState(false)

    useEffect(() => {
        const interval = setInterval(() => {
            setCurrentStep((prev) => {
                const next = prev + 1;
                if (next >= storySteps.length) {
                    setIsMonitoring(true);
                    return prev; // Stay on last step or loop? User complaint said "loop loops".
                    // Let's loop but indicating it's deep analysis or start over?
                    // "Runs in loops and wont stop" -> The analysis might be hanging.
                    // If backend is hung, frontend just shows this.
                    // Let's slow it down and loop, but "Monitoring" state is better.
                    return 0;
                }
                return next;
            })
        }, 1500) // Slower, more deliberate pace

        return () => clearInterval(interval)
    }, [])

    return (
        <div className="font-mono text-xs sm:text-sm text-emerald-400 bg-slate-900 p-6 rounded-lg border border-emerald-900/50 shadow-inner min-h-[160px] flex flex-col justify-center items-center text-center">
            <div className="mb-4">
                <span className="inline-block w-2 h-2 bg-emerald-500 rounded-full animate-ping mr-2"></span>
                <span className="uppercase tracking-widest text-xs font-bold text-emerald-600">Veraguard Core Active</span>
            </div>
            <div className="transition-all duration-300 transform">
                {isMonitoring && currentStep === 0 ? (
                    <p className="text-xl text-emerald-300 font-bold mb-2 animate-pulse font-mono">
                        ANALYZING PATIENT ZERO...
                    </p>
                ) : (
                    <p className="text-lg text-emerald-100 font-bold mb-2 font-mono">
                        {storySteps[currentStep]}
                    </p>
                )}

                <p className="text-emerald-500/50 text-xs mt-2 uppercase tracking-widest">
                    VeraGuard Diagnostic Engine
                </p>
            </div>
        </div>
    )
}
