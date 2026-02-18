import { useState, useEffect, useCallback } from 'react'
import SecurityScore from './components/SecurityScore'
import TreasuryFlow from './components/TreasuryFlow'
import AuditStory from './components/AuditStory'
import WebApp from '@twa-dev/sdk'
import './App.css'

function App() {
  // State
  const [address, setAddress] = useState('')
  const [analyzing, setAnalyzing] = useState(false)
  const [score, setScore] = useState<number | null>(null)
  const [warnings, setWarnings] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)

  // User/Credit/Fee State
  const [userId, setUserId] = useState<string>('')
  const [credits, setCredits] = useState<number>(0)
  const [paying, setPaying] = useState(false)
  const [dynamicFee, setDynamicFee] = useState<string>('0.001')
  const [walletAddress, setWalletAddress] = useState<string | null>(null)

  // Deep Dive State
  const [showDeepDiveModal, setShowDeepDiveModal] = useState(false)
  const [pendingDeepDiveAddress, setPendingDeepDiveAddress] = useState<string | null>(null)

  // Initialize Telegram & User & Fee
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
    fetchFee();

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

  const fetchFee = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/fee')
      if (res.ok) {
        const data = await res.json()
        setDynamicFee(String(data.fee))
      }
    } catch (e) {
      console.error("Failed to fetch fee", e)
    }
  }

  const connectWallet = async () => {
    if (typeof window.ethereum !== 'undefined') {
      try {
        const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
        setWalletAddress(accounts[0]);
        WebApp.HapticFeedback.notificationOccurred('success');
      } catch (error) {
        console.error(error);
        WebApp.HapticFeedback.notificationOccurred('error');
      }
    } else {
      alert('No crypto wallet found. Please install MetaMask.');
    }
  }

  const handlePayment = useCallback(async (amount: number = 1) => {
    WebApp.MainButton.showProgress(false);
    setPaying(true);
    setError(null);
    try {
      // simulating a Wallet Tx Hash (or use real if wallet connected)
      const mockTxHash = walletAddress ? "0xreal_" + Math.random().toString(36).substr(2, 9) : "0xvalid_" + Math.random().toString(36).substr(2, 9)

      const response = await fetch('http://localhost:8000/api/pay', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tx_hash: mockTxHash, user_id: userId, credits: amount }),
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
  }, [userId, walletAddress]);

  const handleAudit = useCallback(async (e?: React.FormEvent, confirmDeepDive: boolean = false) => {
    if (e) e.preventDefault();
    if (!address && !confirmDeepDive) return;

    const targetAddress = confirmDeepDive && pendingDeepDiveAddress ? pendingDeepDiveAddress : address;

    WebApp.MainButton.showProgress(false);
    WebApp.MainButton.showProgress(true);

    setAnalyzing(true);
    setError(null);
    setScore(null);
    setWarnings([]);
    setShowDeepDiveModal(false);

    try {
      const response = await fetch('http://localhost:8000/api/audit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          address: targetAddress,
          user_id: userId,
          confirm_deep_dive: confirmDeepDive
        }),
      })

      if (response.status === 402) {
        throw new Error("Insufficient credits. Please purchase more.")
      }

      if (response.status === 503) {
        throw new Error("Security Vault Insolvent. Audit halted for safety.")
      }

      const data = await response.json()

      // Handle Tiered Pricing (Universal Ledger Alert)
      if (data.status === "requires_approval") {
        setPendingDeepDiveAddress(targetAddress);
        setShowDeepDiveModal(true);
        setAnalyzing(false);
        WebApp.MainButton.hideProgress();
        WebApp.HapticFeedback.notificationOccurred('warning');
        return;
      }

      if (data.error) {
        setError(data.error)
        WebApp.HapticFeedback.notificationOccurred('error');
      } else {
        setScore(data.vera_score)
        setWarnings(data.warnings || [])
        fetchCredits(userId)
        WebApp.HapticFeedback.notificationOccurred('success');
      }

    } catch (err: any) {
      setError(err.message || "Something went wrong. Is the backend running?")
      WebApp.HapticFeedback.notificationOccurred('error');
    } finally {
      if (!showDeepDiveModal) {
        setAnalyzing(false);
        WebApp.MainButton.hideProgress();
      }
    }
  }, [address, userId, pendingDeepDiveAddress, showDeepDiveModal]);


  // Sync MainButton State
  useEffect(() => {
    const mainButton = WebApp.MainButton;

    if (credits < 1) {
      mainButton.setText(`PAY ${dynamicFee} ETH (1 Credit)`);
      mainButton.show();
      mainButton.onClick(() => handlePayment(1));
    } else if (address) {
      mainButton.setText("AUDIT CONTRACT");
      mainButton.show();
      mainButton.onClick(() => handleAudit());
    } else {
      mainButton.hide();
    }

    return () => {
      mainButton.offClick(handlePayment);
      mainButton.offClick(handleAudit);
    };
  }, [credits, address, handleAudit, handlePayment, dynamicFee]);


  return (
    <div className="min-h-screen font-sans" style={{ backgroundColor: 'var(--tg-theme-bg-color)', color: 'var(--tg-theme-text-color)' }}>
      <header className="p-6 shadow-sm border-b border-slate-200 flex justify-between items-center" style={{ borderColor: 'var(--tg-theme-hint-color)' }}>
        <h1 className="text-2xl font-bold tracking-tight">VeraGuard <span className="text-emerald-500">App</span></h1>

        <div className="flex gap-2">
          {/* Wallet Connect */}
          <button
            onClick={connectWallet}
            className="text-xs px-3 py-1 rounded-full border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
          >
            {walletAddress ?
              <span className="text-emerald-600 font-bold">● {walletAddress.substring(0, 6)}...</span>
              : <span className="text-slate-500">Connect Wallet</span>
            }
          </button>
          <div className="text-sm font-medium px-3 py-1 rounded-full" style={{ backgroundColor: 'var(--tg-theme-secondary-bg-color)' }}>
            Credits: <span className={credits > 0 ? "text-emerald-600 font-bold" : "text-red-500 font-bold"}>{credits}</span>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 pb-32">

        {/* Input / Payment Section */}
        <div className="max-w-xl mx-auto mb-12">

          {credits < 1 ? (
            <div className="text-center p-8 rounded-xl shadow-sm border" style={{ backgroundColor: 'var(--tg-theme-secondary-bg-color)', borderColor: 'var(--tg-theme-hint-color)' }}>
              <h2 className="text-xl font-bold mb-2">Audit Credits Required</h2>
              <div className="p-4 rounded-lg mb-6 border opacity-80" style={{ borderColor: 'var(--tg-theme-hint-color)' }}>
                <p className="text-xs uppercase tracking-wider font-semibold mb-1">Dynamic Cost (1 Credit)</p>
                <p className="text-2xl font-mono font-bold">{dynamicFee} ETH</p>
              </div>

              <div className="grid grid-cols-3 gap-2 mb-4">
                <button onClick={() => handlePayment(1)} disabled={paying} className="py-3 bg-emerald-500 text-white font-bold rounded hover:bg-emerald-600 disabled:opacity-50">
                  1 Credit
                </button>
                <button onClick={() => handlePayment(10)} disabled={paying} className="py-3 bg-emerald-600 text-white font-bold rounded hover:bg-emerald-700 disabled:opacity-50 relative overflow-hidden">
                  <span className="relative z-10">10 Pack</span>
                  <div className="absolute inset-0 bg-white/10 skew-x-12 -ml-4"></div>
                </button>
                <button onClick={() => handlePayment(50)} disabled={paying} className="py-3 bg-slate-800 text-white font-bold rounded hover:bg-slate-900 disabled:opacity-50 border border-emerald-500/50">
                  50 Pack
                </button>
              </div>
              <p className="text-xs opacity-50">{paying ? "Processing Transaction..." : "Select a Bundle"}</p>
            </div>
          ) : (
            <>
              <div className="flex gap-4">
                <input
                  type="text"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  placeholder="Enter Contract Address (e.g., 0x...)"
                  className="flex-1 p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono text-sm shadow-sm"
                  style={{ backgroundColor: 'var(--tg-theme-bg-color)', color: 'var(--tg-theme-text-color)', borderColor: 'var(--tg-theme-hint-color)' }}
                />
                <button
                  onClick={() => handleAudit()}
                  disabled={analyzing || !address}
                  className="px-6 py-3 bg-slate-900 text-white font-semibold rounded-lg disabled:opacity-50 hidden sm:block"
                >
                  {analyzing ? 'Scanning...' : 'Audit'}
                </button>
              </div>
            </>
          )}

          {error && <p className="mt-4 text-red-500 text-center font-medium p-2 rounded border border-red-100">{error}</p>}
        </div>

        {/* Audit Story (Loader) */}
        {analyzing && (
          <div className="max-w-xl mx-auto mb-12 animate-fade-in">
            <AuditStory />
          </div>
        )}

        {/* Results Section */}
        {score !== null && !analyzing && (
          <div className="animate-fade-in-up">
            <SecurityScore score={score} warnings={warnings} />
          </div>
        )}

        {/* Initial State */}
        {score === null && !analyzing && !error && credits > 0 && (
          <div className="text-center opacity-50 mt-20">
            <p className="text-lg mb-6">Enter a contract address to verify.</p>
          </div>
        )}

        {/* Universal Ledger Alert Modal (Deep Dive) */}
        {showDeepDiveModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-white p-6 rounded-xl shadow-2xl max-w-sm w-full border border-slate-200 dark:bg-slate-900 dark:border-slate-700">
              <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-2">⚠️ Universal Ledger Alert</h3>
              <p className="text-slate-600 dark:text-slate-300 mb-6 font-medium">
                Heuristic Analysis detects a massive contract ({'>'}24KB).
                <br /><br />
                <span className="opacity-70 font-normal">Standard auditing cannot guarantee safety for this volume of bytecode logic.</span>
                <br /><br />
                <span className="text-emerald-500 font-bold block mt-2 p-2 bg-emerald-50 dark:bg-emerald-900/20 rounded text-center border border-emerald-100 dark:border-emerald-800">
                  Recommend: Deep Dive (3 Credits)
                </span>
              </p>
              <div className="flex gap-3">
                <button
                  onClick={() => setShowDeepDiveModal(false)}
                  className="flex-1 py-3 bg-slate-200 text-slate-800 font-bold rounded hover:bg-slate-300"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleAudit(undefined, true)}
                  className="flex-1 py-3 bg-emerald-600 text-white font-bold rounded hover:bg-emerald-700 shadow-lg shadow-emerald-500/20"
                >
                  Approve
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Treasury Flow Visuals */}
        <TreasuryFlow />

      </main>
    </div>
  )
}

export default App
