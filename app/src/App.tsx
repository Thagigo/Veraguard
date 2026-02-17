import { useState } from 'react'
import SecurityScore from './components/SecurityScore'
import './App.css'

function App() {
  // State
  const [address, setAddress] = useState('')
  const [analyzing, setAnalyzing] = useState(false)
  const [score, setScore] = useState<number | null>(null)
  const [warnings, setWarnings] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)

  const handleAudit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!address) return

    setAnalyzing(true)
    setError(null)
    setScore(null)
    setWarnings([])

    try {
      // Call the local FastAPI backend
      const response = await fetch('http://localhost:8000/api/audit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address }),
      })

      if (!response.ok) {
        throw new Error('Audit request failed')
      }

      const data = await response.json()

      if (data.error) {
        setError(data.error)
      } else {
        setScore(data.vera_score)
        setWarnings(data.warnings || [])
      }

    } catch (err: any) {
      setError(err.message || "Something went wrong. Is the backend running?")
    } finally {
      setAnalyzing(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      <header className="p-6 bg-white shadow-sm border-b border-slate-200">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">VeraGuard <span className="text-emerald-500">Dashboard</span></h1>
      </header>

      <main className="container mx-auto px-4 py-8">

        {/* Input Section */}
        <div className="max-w-xl mx-auto mb-12">
          <form onSubmit={handleAudit} className="flex gap-4">
            <input
              type="text"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="Enter Contract Address (e.g., 0x...)"
              className="flex-1 p-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono text-sm shadow-sm"
            />
            <button
              type="submit"
              disabled={analyzing}
              className="px-6 py-3 bg-slate-900 text-white font-semibold rounded-lg hover:bg-slate-800 disabled:opacity-50 transition-colors shadow-sm"
            >
              {analyzing ? 'Scanning...' : 'Audit'}
            </button>
          </form>
          {error && <p className="mt-4 text-red-500 text-center font-medium bg-red-50 p-2 rounded border border-red-100">{error}</p>}
        </div>

        {/* Results Section */}
        {score !== null && (
          <div className="animate-fade-in-up">
            <SecurityScore score={score} warnings={warnings} />
          </div>
        )}

        {/* Initial Empty State */}
        {score === null && !analyzing && !error && (
          <div className="text-center text-slate-400 mt-20">
            <p className="text-lg mb-6">Ready to verify. Enter a contract address above.</p>
            <div className="inline-block p-6 bg-white rounded-xl border border-slate-200 shadow-sm text-left">
              <p className="font-bold text-slate-700 mb-3 border-b border-slate-100 pb-2">Try these simulations:</p>
              <ul className="space-y-2 font-mono text-sm text-slate-600">
                <li className="flex justify-between gap-8"><span>Ghost Mint:</span> <span className="text-slate-400">0x...ghost</span></li>
                <li className="flex justify-between gap-8"><span>Bricking Risk:</span> <span className="text-slate-400">0x...brick</span></li>
                <li className="flex justify-between gap-8"><span>Fee Abuse:</span> <span className="text-slate-400">0x...fee</span></li>
                <li className="flex justify-between gap-8"><span>Clean Contract:</span> <span className="text-slate-400">0x...safe</span></li>
              </ul>
            </div>
          </div>
        )}

      </main>
    </div>
  )
}

export default App
