import { useState, useEffect } from 'react'

const steps = [
    "Initializing Secure Environment...",
    "Fetching Bytecode from Base...",
    "Decompiling EVM Opcodes...",
    "Scanning for 'Ghost Mint' Signatures...",
    "Checking 'Liquidity Unlock' Patterns...",
    "Verifying Math Safety (Solidity <0.8.0)...",
    "Simulating Transaction via Foundry...",
    "Querying Veraguard Intelligence Ledger...",
    "Finalizing Risk Score..."
]

export default function AuditFeed() {
    const [currentStep, setCurrentStep] = useState(0)

    useEffect(() => {
        const interval = setInterval(() => {
            setCurrentStep((prev) => (prev + 1) % steps.length)
        }, 400) // Fast updates for "Matrix" feel

        return () => clearInterval(interval)
    }, [])

    return (
        <div className="font-mono text-xs sm:text-sm text-emerald-400 bg-slate-900 p-4 rounded-lg border border-emerald-900/50 shadow-inner h-32 overflow-hidden flex flex-col justify-end">
            {steps.slice(Math.max(0, currentStep - 3), currentStep + 1).map((step, i) => (
                <div key={i} className={`mb-1 ${i === 3 ? "text-emerald-200 font-bold animate-pulse" : "opacity-50"}`}>
                    {">"} {step}
                </div>
            ))}
        </div>
    )
}
