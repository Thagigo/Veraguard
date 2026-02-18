import { useState, useEffect, useCallback } from 'react'
import SecurityScore from './components/SecurityScore'
import WebApp from '@twa-dev/sdk'
import './App.css'

function App() {
  // State
  const [address, setAddress] = useState('')
  const [analyzing, setAnalyzing] = useState(false)
  const [score, setScore] = useState<number | null>(null)
  const [warnings, setWarnings] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)

  // User/Credit State
  const [userId, setUserId] = useState<string>('')
  const [credits, setCredits] = useState<number>(0)
  const [paying, setPaying] = useState(false)

  // Initialize Telegram & User
  useEffect(() => {
    // expansive mode
    WebApp.expand();

    // Theme Sync
    document.documentElement.style.setProperty('--tg-theme-bg-color', WebApp.backgroundColor || '#ffffff');
    document.documentElement.style.setProperty('--tg-theme-text-color', WebApp.themeParams.text_color || '#000000');

    // User ID from Telegram or LocalStorage fallback
    let currentUserId = '';
    if (WebApp.initDataUnsafe.user) {
      currentUserId = String(WebApp.initDataUnsafe.user.id);
    } else {
      const stored = localStorage.getItem('veraguard_user_id');
      currentUserId = stored || 'user_' + Math.random().toString(36).substr(2, 9);
      if (!stored) localStorage.setItem('veraguard_user_id', currentUserId);
    }

    setUserId(currentUserId);
    fetchCredits(currentUserId);

  }, [])

  const fetchCredits = async (uid: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/credits/${uid}`)
      if (res.ok) {
        const data = await res.json()
        setCredits(data.credits)
      }
    } catch (e) {
      console.error("Failed to fetch credits", e)
    }
  }

  const handlePayment = useCallback(async () => {
    WebApp.MainButton.showProgress(false);
    setPaying(true);
    setError(null);
    try {
      // simulating a Wallet Tx Hash
      const mockTxHash = "0xvalid_" + Math.random().toString(36).substr(2, 9)

      const response = await fetch('http://localhost:8000/api/pay', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tx_hash: mockTxHash, user_id: userId }),
      })

      if (!response.ok) throw new Error('Payment verification failed')

      const data = await response.json()
      setCredits(data.credits)
      WebApp.HapticFeedback.notificationOccurred('success');

    } catch (err: any) {
      setError(err.message || "Payment Failed")
      WebApp.HapticFeedback.notificationOccurred('error');
    } finally {
      setPaying(false);
      WebApp.MainButton.hideProgress();
    }
  }, [userId]);

  const handleAudit = useCallback(async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!address) return;
    WebApp.MainButton.showProgress(false);
    WebApp.MainButton.showProgress(true);

    setAnalyzing(true);
    setError(null);
    setScore(null);
    setWarnings([]);

    try {
      // Call the local FastAPI backend with user_id
      const response = await fetch('http://localhost:8000/api/audit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address, user_id: userId }),
      })

      if (response.status === 402) {
        throw new Error("Insufficient credits. Payment required.")
      }

      const data = await response.json()

      if (data.error) {
        setError(data.error)
        WebApp.HapticFeedback.notificationOccurred('error');
      } else {
        setScore(data.vera_score)
        setWarnings(data.warnings || [])
        // Refresh credits after spend
        fetchCredits(userId)
        WebApp.HapticFeedback.notificationOccurred('success');
      }

    } catch (err: any) {
      setError(err.message || "Something went wrong. Is the backend running?")
      WebApp.HapticFeedback.notificationOccurred('error');
    } finally {
      setAnalyzing(false);
      WebApp.MainButton.hideProgress();
    }
  }, [address, userId]);

  // Sync MainButton State
  useEffect(() => {
    const mainButton = WebApp.MainButton;

    if (credits < 1) {
      mainButton.setText(`PAY 0.001 ETH TO AUDIT`);
      mainButton.show();
      mainButton.onClick(handlePayment);
    } else if (address) {
      mainButton.setText("AUDIT CONTRACT");
      mainButton.show();
      mainButton.onClick(handleAudit);
    } else {
      mainButton.hide();
    }

    return () => {
      mainButton.offClick(handlePayment);
      mainButton.offClick(handleAudit);
    };
  }, [credits, address, handleAudit, handlePayment]);


  return (
    <div className="min-h-screen font-sans" style={{ backgroundColor: 'var(--tg-theme-bg-color)', color: 'var(--tg-theme-text-color)' }}>
      <header className="p-6 shadow-sm border-b border-slate-200 flex justify-between items-center" style={{ borderColor: 'var(--tg-theme-hint-color)' }}>
        <h1 className="text-2xl font-bold tracking-tight">VeraGuard <span className="text-emerald-500">App</span></h1>
        <div className="text-sm font-medium px-3 py-1 rounded-full" style={{ backgroundColor: 'var(--tg-theme-secondary-bg-color)' }}>
          Credits: <span className={credits > 0 ? "text-emerald-600 font-bold" : "text-red-500 font-bold"}>{credits}</span>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">

        {/* Input Section */}
        <div className="max-w-xl mx-auto mb-12">

          {credits < 1 ? (
            <div className="text-center p-8 rounded-xl shadow-sm border" style={{ backgroundColor: 'var(--tg-theme-secondary-bg-color)', borderColor: 'var(--tg-theme-hint-color)' }}>
              <h2 className="text-xl font-bold mb-2">Audit Credits Required</h2>
              <p className="mb-6 opacity-70">1 Credit = 1 Medical-Grade Audit</p>
              <div className="p-4 rounded-lg mb-6 border opacity-80" style={{ borderColor: 'var(--tg-theme-hint-color)' }}>
                <p className="text-xs uppercase tracking-wider font-semibold mb-1">Cost</p>
                <p className="text-2xl font-mono font-bold">0.001 ETH</p>
              </div>
              {/* Fallback button if MainButton fails or for desktop testing */}
              <button
                onClick={handlePayment}
                disabled={paying}
                className="w-full py-4 bg-emerald-500 text-white font-bold rounded-lg hover:bg-emerald-600 transition-all disabled:opacity-70"
              >
                {paying ? 'Processing...' : 'Pay & Add Credit'}
              </button>
            </div>
          ) : (
            <div className="flex gap-4">
              <input
                type="text"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder="Enter Contract Address (e.g., 0x...)"
                className="flex-1 p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono text-sm shadow-sm"
                style={{ backgroundColor: 'var(--tg-theme-bg-color)', color: 'var(--tg-theme-text-color)', borderColor: 'var(--tg-theme-hint-color)' }}
              />
              {/* Hide Audit button on mobile if using MainButton, but keep for hybrid/desktop */}
              <button
                onClick={() => handleAudit({ preventDefault: () => { } } as React.FormEvent)}
                disabled={analyzing || !address}
                className="px-6 py-3 bg-slate-900 text-white font-semibold rounded-lg disabled:opacity-50 hidden sm:block"
              >
                {analyzing ? 'Scanning...' : 'Audit'}
              </button>
            </div>
          )}

          {error && <p className="mt-4 text-red-500 text-center font-medium p-2 rounded border border-red-100">{error}</p>}
        </div>

        {/* Results Section */}
        {score !== null && (
          <div className="animate-fade-in-up">
            <SecurityScore score={score} warnings={warnings} />
          </div>
        )}

        {/* Initial Empty State */}
        {score === null && !analyzing && !error && credits > 0 && (
          <div className="text-center opacity-50 mt-20">
            <p className="text-lg mb-6">Enter a contract address to verify.</p>
          </div>
        )}

      </main>
    </div>
  )
}

export default App
