import { useState, useEffect } from 'react'

const storySteps = [
    "Step 1: Flash Triage (Universal Ledger Check)...",
    "Step 2: Decompiling Bytecode & Opcode Analysis...",
    "Step 3: Historical Pattern Matching (Reentrancy/Overflow)...",
    "Step 4: Proactive Hunter Simulation (Gemini 3 Pro)...",
    "Step 5: Verifying Vault Solvency & Liquidity...",
    "Step 6: Generating Medical-Grade Report..."
]

export default function AuditStory() {
    const [currentStep, setCurrentStep] = useState(0)

    useEffect(() => {
        const interval = setInterval(() => {
            setCurrentStep((prev) => (prev + 1) % storySteps.length)
        }, 800) // Slower, more deliberate pace for "Story"

        return () => clearInterval(interval)
    }, [])

    return (
        <div className="font-mono text-xs sm:text-sm text-emerald-400 bg-slate-900 p-6 rounded-lg border border-emerald-900/50 shadow-inner min-h-[160px] flex flex-col justify-center items-center text-center">
            <div className="mb-4">
                <span className="inline-block w-2 h-2 bg-emerald-500 rounded-full animate-ping mr-2"></span>
                <span className="uppercase tracking-widest text-xs font-bold text-emerald-600">Veraguard Core Active</span>
            </div>
            <div className="transition-all duration-300 transform">
                <p className="text-lg text-emerald-100 font-bold mb-2">
                    {storySteps[currentStep]}
                </p>
                <p className="text-emerald-500/50 text-xs">
                    {currentStep + 1} / {storySteps.length}
                </p>
            </div>
        </div>
    )
}
