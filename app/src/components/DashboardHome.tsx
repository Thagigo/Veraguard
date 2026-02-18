import { useState, useEffect, useCallback } from 'react'
import AuditStory from './AuditStory'
import ProtocolDashboard from './ProtocolDashboard'
import AuditReport from './AuditReport'
import SheriffsFrontier from './SheriffsFrontier';
import LandingPage from './LandingPage';
import PreFlightPreview from './PreFlightPreview'; // [NEW]
import DistributionReceipt from './DistributionReceipt'; // [NEW]
import WebApp from '@twa-dev/sdk'
import '../App.css'
import { useNavigate } from 'react-router-dom';

// --- Telegram WebApp Types ---
declare global {
    interface Window {
        Telegram?: {
            WebApp?: {
                initData: string;
                initDataUnsafe: any;
                ready: () => void;
                expand: () => void;
                MainButton: {
                    text: string;
                    color: string;
                    textColor: string;
                    isVisible: boolean;
                    show: () => void;
                    hide: () => void;
                    onClick: (callback: () => void) => void;
                    offClick: (callback: () => void) => void;
                    showProgress: (leaveActive: boolean) => void;
                    hideProgress: () => void;
                };
                HapticFeedback: {
                    impactOccurred: (style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft') => void;
                    notificationOccurred: (type: 'error' | 'success' | 'warning') => void;
                    selectionChanged: () => void;
                };
                openLink: (url: string) => void;
            }
        }
    }
}

interface FeeQuote {
    amount: number;
    expiry: number;
    signature: string;
    subscription_amount?: number;
    eth_price_usd?: number;
}

interface DashboardHomeProps {
    userId: string;
    onLogout: () => void;
}

export default function DashboardHome({ userId, onLogout }: DashboardHomeProps) {
    const navigate = useNavigate();

    // State
    const [address, setAddress] = useState('')
    const [analyzing, setAnalyzing] = useState(false)
    const [score, setScore] = useState<number | null>(null)
    const [warnings, setWarnings] = useState<string[]>([])
    const [error, setError] = useState<string | null>(null)

    // User/Credit/Fee State
    const [credits, setCredits] = useState<number>(0)
    const [paying, setPaying] = useState(false)

    // Custom Purchase State
    const [purchaseAmount, setPurchaseAmount] = useState<number>(1)

    // Fee Quote State
    const [feeQuote, setFeeQuote] = useState<FeeQuote | null>(null)
    const [quoteTimeLeft, setQuoteTimeLeft] = useState<number>(0);

    // [FIX] Persist Wallet Connection
    const [walletAddress, setWalletAddress] = useState<string | null>(() => {
        return localStorage.getItem('veraguard_wallet');
    })

    // Deep Dive State
    const [showDeepDiveModal, setShowDeepDiveModal] = useState(false)
    const [pendingDeepDiveAddress, setPendingDeepDiveAddress] = useState<string | null>(null)

    // Audit State
    const [milestones, setMilestones] = useState<any[]>([]);
    const [riskSummary, setRiskSummary] = useState<string | undefined>(undefined);
    const [vitals, setVitals] = useState<any | undefined>(undefined);

    // Membership & Referral State
    const [isMember, setIsMember] = useState(false);
    const [myRefCode, setMyRefCode] = useState<string | null>(null);
    const [referralStats, setReferralStats] = useState({ uses: 0, earned: 0 });
    const [inputRefCode, setInputRefCode] = useState("");

    // God Mode / Dashboard State
    const [showDashboard, setShowDashboard] = useState(false)
    const [logoClicks, setLogoClicks] = useState(0)

    // Live Link & Transparency State
    const [referralBanner, setRefBanner] = useState<string | null>(null);
    const [showFrontier, setShowFrontier] = useState(false);

    const [isLiveView, setIsLiveView] = useState(false);

    // [NEW] Purchase Flow States
    const [showPreFlight, setShowPreFlight] = useState(false);
    const [pendingPurchase, setPendingPurchase] = useState<{ amount: number; isSubscription: boolean } | null>(null);
    const [showReceipt, setShowReceipt] = useState(false);
    const [paymentSuccessAmount, setPaymentSuccessAmount] = useState(0);

    const [paymentSuccessCost, setPaymentSuccessCost] = useState(0);

    // [NEW] High-Noon Leads Ticker
    const [leads, setLeads] = useState<any[]>([]);
    useEffect(() => {
        if (!userId) return;
        fetch(`http://localhost:8000/api/leads?user_id=${userId}`)
            .then(res => res.json())
            .then(data => {
                if (data.leads) setLeads(data.leads);
            })
            .catch(console.error);
    }, [userId]);

    // Initialize Telegram & Fee (User ID handled by parent)
    useEffect(() => {
        fetchCredits(userId);
        fetchFee();
        fetchReferralData(userId);

        // Quote Timer
        const timer = setInterval(() => {
            setQuoteTimeLeft(prev => prev > 0 ? prev - 1 : 0);
        }, 1000);

        // Check for Live Link (Permalink)
        const params = new URLSearchParams(window.location.search);
        const reportId = params.get('report_id');
        const refCode = params.get('ref');

        if (reportId) {
            fetchLiveReport(reportId, refCode);
            if (refCode) setInputRefCode(refCode);
        }

        return () => clearInterval(timer);

    }, [userId])

    // Fetch Live Report
    const fetchLiveReport = async (reportId: string, refCode: string | null) => {
        setAnalyzing(true);
        try {
            let url = `http://localhost:8000/api/audit/live/${reportId}`;
            if (refCode) url += `?ref=${refCode}`;

            const res = await fetch(url);
            if (!res.ok) throw new Error("Report not found or expired.");

            const data = await res.json();
            if (data.report) {
                const r = data.report;
                setScore(r.vera_score);
                setWarnings(r.warnings || []);
                setRiskSummary(r.risk_summary);
                setMilestones(r.milestones || []);
                setVitals(r.vitals);
                setIsLiveView(true);
            }
            if (data.referral_msg) {
                setRefBanner(data.referral_msg);
            }

        } catch (e) {
            setError("Failed to load live report.");
            console.error(e);
        } finally {
            setAnalyzing(false);
        }
    }

    // Refresh Quote when expired
    useEffect(() => {
        if (quoteTimeLeft === 0 && feeQuote) {
            fetchFee();
        }
    }, [quoteTimeLeft, feeQuote]);

    const fetchCredits = async (uid: string) => {
        try {
            const res = await fetch(`http://localhost:8000/api/credits/${uid}`)
            if (res.ok) {
                const data = await res.json()
                setCredits(data.credits)
                setIsMember(data.is_member || false)
            }
        } catch (e) {
            console.error("Failed to fetch credits", e)
        }
    }

    const fetchReferralData = async (uid: string) => {
        try {
            const res = await fetch(`http://localhost:8000/api/referral/${uid}`);
            if (res.ok) {
                const data = await res.json();
                setMyRefCode(data.code);
                setReferralStats({ uses: data.uses, earned: data.earned });
            }
        } catch (e) { console.error(e); }
    }

    const generateReferralCode = async () => {
        try {
            const res = await fetch(`http://localhost:8000/api/referral/create`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId, tx_hash: "ref_gen", credits: 0 })
            });
            const data = await res.json();
            if (data.code) setMyRefCode(data.code);
        } catch (e) { console.error(e); }
    }

    const fetchFee = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/fee')
            if (res.ok) {
                const data = await res.json()
                if (data.quote) {
                    setFeeQuote(data.quote);
                    const now = Math.floor(Date.now() / 1000);
                    const timeLeft = data.quote.expiry - now;
                    setQuoteTimeLeft(timeLeft > 0 ? timeLeft : 0);
                }
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
                localStorage.setItem('veraguard_wallet', accounts[0]); // [FIX] Persist
                WebApp.HapticFeedback.notificationOccurred('success');
            } catch (error) {
                console.error(error);
                WebApp.HapticFeedback.notificationOccurred('error');
            }
        } else {
            const mockAddress = "0x71C7656EC7ab88b098defB751B7401B5f6d8976F";
            setWalletAddress(mockAddress);
            localStorage.setItem('veraguard_wallet', mockAddress); // [FIX] Persist
            WebApp.HapticFeedback.notificationOccurred('success');
        }
    }

    // initiatePayment triggers PreFlight
    const initiatePayment = (amount: number, isSubscription: boolean = false) => {
        if (!feeQuote) {
            WebApp.HapticFeedback.notificationOccurred('error');
            // Try fetching again
            fetchFee();
            setError("Connection to Treasury offline. Retrying quote...");
            return;
        }
        setPendingPurchase({ amount, isSubscription });
        setShowPreFlight(true);
    };

    const executePayment = useCallback(async () => {
        if (!pendingPurchase) return;
        const { amount, isSubscription } = pendingPurchase;

        setShowPreFlight(false);
        WebApp.MainButton.showProgress(false);
        setPaying(true);
        setError(null);
        try {
            const mockTxHash = walletAddress ? "0xreal_" + Math.random().toString(36).substr(2, 9) : "0xvalid_" + Math.random().toString(36).substr(2, 9)

            const response = await fetch('http://localhost:8000/api/pay', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    tx_hash: mockTxHash,
                    user_id: userId,
                    credits: isSubscription ? 0 : amount,
                    is_subscription: isSubscription,
                    referral_code: inputRefCode || null
                }),
            })

            if (!response.ok) throw new Error('Payment verification failed')

            const data = await response.json()
            setCredits(data.credits)
            setIsMember(data.is_member)

            const cost = isSubscription ? (feeQuote?.subscription_amount || 0.05) : (amount * (feeQuote?.amount || 0.001));
            // setLastPaymentAmount(cost); // Unused

            // Show Receipt
            setPaymentSuccessAmount(isSubscription ? 50 : amount);
            setPaymentSuccessCost(cost);
            setShowReceipt(true);

            WebApp.HapticFeedback.notificationOccurred('success');

        } catch (err: any) {
            setError(err.message || "Payment Failed")
            WebApp.HapticFeedback.notificationOccurred('error');
        } finally {
            setPaying(false);
            WebApp.MainButton.hideProgress();
            setPendingPurchase(null);
        }
    }, [userId, walletAddress, feeQuote, inputRefCode, pendingPurchase]);

    const handleAudit = useCallback(async (e?: React.FormEvent, confirmDeepDive: boolean = false, bypassDeepDive: boolean = false) => {
        if (e) e.preventDefault();
        if (!address && !confirmDeepDive && !bypassDeepDive) return;

        const targetAddress = (confirmDeepDive || bypassDeepDive) && pendingDeepDiveAddress ? pendingDeepDiveAddress : address;

        WebApp.MainButton.showProgress(false);
        WebApp.MainButton.showProgress(true);

        setAnalyzing(true);
        setError(null);
        setScore(null);
        setWarnings([]);
        setMilestones([]);
        setRiskSummary(undefined);
        setVitals(undefined);
        setShowDeepDiveModal(false);

        try {
            const response = await fetch('http://localhost:8000/api/audit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    address: pendingDeepDiveAddress || address,
                    user_id: userId,
                    confirm_deep_dive: confirmDeepDive,
                    bypass_deep_dive: false
                })
            })

            if (response.status === 402) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Insufficient credits.");
            }

            if (response.status === 503) {
                throw new Error("Security Vault Insolvent. Audit halted for safety.")
            }

            const data = await response.json()

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
                setMilestones(data.milestones || [])
                setRiskSummary(data.risk_summary)
                setVitals(data.vitals)

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
    }, [address, userId, pendingDeepDiveAddress, showDeepDiveModal]);


    // Sync MainButton State and Predictive CTA
    useEffect(() => {
        const mainButton = WebApp.MainButton;

        if (credits < 1) {
            // PREDICTIVE CTA: If insufficient credits, Button = Get Access
            // If purchase pending confirmation (PreFlight), hide MainButton or change text?
            // PreFlight is a modal, so MainButton might be distracting. Let's hide it if PreFlight is open.

            if (showPreFlight) {
                mainButton.hide();
                return;
            }

            if (feeQuote && purchaseAmount > 0) {
                const totalEth = (feeQuote.amount * purchaseAmount).toFixed(4);
                mainButton.setText(`GET ACCESS (${totalEth} ETH)`); // Predictive CTA
                mainButton.show();

                mainButton.offClick(handleAudit);
                // On Click -> Initiate Payment (PreFlight)
                const onPayClick = () => initiatePayment(purchaseAmount);
                mainButton.onClick(onPayClick);

                return () => { mainButton.offClick(onPayClick); };
            } else {
                mainButton.hide();
            }
        } else if (address) {
            mainButton.setText(analyzing ? "SCANNING..." : "AUDIT CONTRACT");
            mainButton.show();
            mainButton.onClick(handleAudit);
            return () => { mainButton.offClick(handleAudit); };
        } else {
            mainButton.hide();
        }
    }, [credits, address, handleAudit, executePayment, feeQuote, purchaseAmount, showPreFlight, analyzing]);

    const handleLogoClick = () => {
        const newCount = logoClicks + 1;
        setLogoClicks(newCount);
        if (newCount === 3) {
            setShowDashboard(true);
            setLogoClicks(0);
            WebApp.HapticFeedback.notificationOccurred('success');
        }
    };

    return (
        <div className="min-h-screen font-sans bg-transparent text-white">
            {/* PreFlight Modal */}
            {showPreFlight && pendingPurchase && feeQuote && (
                <PreFlightPreview
                    amount={pendingPurchase.isSubscription ? 50 : pendingPurchase.amount}
                    costEth={pendingPurchase.isSubscription ? (feeQuote.subscription_amount || 0.05) : (pendingPurchase.amount * feeQuote.amount)}
                    onConfirm={executePayment}
                    onCancel={() => setShowPreFlight(false)}
                />
            )}

            {/* Distribution Receipt */}
            {showReceipt && (
                <DistributionReceipt
                    amount={paymentSuccessAmount}
                    ethCost={paymentSuccessCost}
                    onComplete={() => setShowReceipt(false)}
                />
            )}

            {showDashboard && <ProtocolDashboard onClose={() => setShowDashboard(false)} userId={userId} />}

            {/* Ticker Bar */}
            <div className="bg-black/40 border-b border-slate-800 backdrop-blur-md h-10 flex items-center overflow-hidden relative">
                <div className="absolute left-0 bg-emerald-500/20 px-3 h-full flex items-center text-xs font-bold text-emerald-400 z-10">
                    PRIORITY LEADS
                </div>
                <div className="animate-marquee flex gap-10 whitespace-nowrap pl-32 text-xs font-mono">
                    {leads.map((lead, i) => (
                        <div key={i} className={`flex items-center gap-2 ${lead.status !== 'VISIBLE' ? 'filter blur-sm opacity-50 select-none' : 'text-emerald-200'}`}>
                            <span className="text-slate-500">[{lead.timestamp}]</span>
                            <span>{lead.address}</span>
                            <span className={`px-1 rounded ${lead.risk === 'High' ? 'bg-red-500/20 text-red-500' : 'bg-amber-500/20 text-amber-500'}`}>
                                {lead.risk}
                            </span>
                            {lead.status !== 'VISIBLE' && <span className="text-[10px] text-slate-600">LOCKED</span>}
                        </div>
                    ))}
                    {leads.length === 0 && <span className="text-slate-600">Scanning Mempool... No Active Leads.</span>}
                </div>
            </div>

            {referralBanner && (
                <div className="bg-indigo-600 text-white px-4 py-2 text-xs font-bold flex justify-between items-center animate-slide-down shadow-md relative z-50">
                    <div className="flex items-center gap-2">
                        <span className="bg-white/20 p-1 rounded-full">🤝</span>
                        <span>{referralBanner}</span>
                    </div>
                    <button
                        onClick={() => { setRefBanner(null); setInputRefCode(""); window.history.replaceState({}, '', window.location.pathname); }}
                        className="text-white/70 hover:text-white underline"
                    >
                        Clear Referral
                    </button>
                </div>
            )}

            {!walletAddress ? (
                <LandingPage onConnect={connectWallet} />
            ) : (
                <>
                    <header className="sticky top-0 z-40 transition-all duration-300 backdrop-blur-xl bg-slate-900/90 border-b border-white/5 shadow-2xl">
                        <div className="max-w-[1400px] mx-auto flex justify-between items-center px-10 py-5">
                            <h1
                                onClick={handleLogoClick}
                                className="text-2xl font-bold tracking-tight flex items-center gap-2 cursor-pointer select-none text-white hover:opacity-80 transition-opacity"
                            >
                                Vera<span className="text-emerald-400 drop-shadow-[0_0_15px_rgba(52,211,153,0.6)]">Guard</span>
                            </h1>

                            <div className="flex gap-10 items-center">
                                {isLiveView && (
                                    <div className="bg-red-500/90 text-white text-[10px] font-bold px-2 py-1 rounded-full animate-pulse border border-red-400/50">
                                        LIVE VIEW
                                    </div>
                                )}

                                {/* Vault Icon / Logout */}
                                <button
                                    onClick={() => navigate('/vault')}
                                    className="p-2 hover:bg-slate-800 rounded-lg transition-colors group relative"
                                    title="View Vault"
                                >
                                    <span className="text-xl group-hover:scale-110 block transition-transform">🏛️</span>
                                </button>

                                <button
                                    onClick={onLogout}
                                    className="p-2 hover:bg-slate-800 rounded-lg transition-colors group relative"
                                    title="Logout (Sovereign Reset)"
                                >
                                    <span className="text-xl group-hover:scale-110 block transition-transform">🛑</span>
                                </button>

                                <div className="text-sm font-bold px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 shadow-inner min-w-[80px] text-center">
                                    <span className={credits > 0 ? "text-emerald-400" : "text-slate-400"}>{credits}</span> <span className="text-[10px] uppercase text-slate-500">CRD</span>
                                </div>
                            </div>
                        </div>
                    </header>

                    <main className="container mx-auto px-4 py-8 pb-32">
                        {score === null && (
                            <div className="max-w-xl mx-auto mb-12">
                                {credits < 1 ? (
                                    <div className="text-center p-6 rounded-2xl shadow-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
                                        {/* Top Up UI */}
                                        <div className="mb-6">
                                            <div className="inline-block p-3 rounded-full bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 mb-2">
                                                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                                            </div>
                                            <h2 className="text-xl font-bold">Top Up Credits</h2>
                                            <p className="text-sm text-slate-500 dark:text-slate-400">Secure audits require verified tokens.</p>
                                        </div>

                                        {/* Cost Display */}
                                        <div className="p-4 rounded-xl mb-6 bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
                                            <div className="flex justify-between items-end mb-4">
                                                <div>
                                                    <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider mb-1">TOTAL COST</div>
                                                    <div className="text-3xl font-mono text-slate-800 dark:text-slate-100 flex items-baseline gap-2">
                                                        {feeQuote ? (
                                                            <>
                                                                <span>{(purchaseAmount * feeQuote.amount).toFixed(6)} ETH</span>
                                                                <span className="text-sm text-slate-400 font-sans">
                                                                    (${(purchaseAmount * 3.00).toFixed(2)})
                                                                </span>
                                                            </>
                                                        ) : "..."}
                                                    </div>
                                                </div>
                                                <div className="flex flex-col items-end gap-1">
                                                    <div className="flex items-center gap-1.5">
                                                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-600 font-bold border border-emerald-500/20">LIVE QUOTE</span>
                                                        <span className="text-xs font-mono">{quoteTimeLeft}s</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Memberships / Plans */}
                                        <div className="grid grid-cols-2 gap-4 mt-6">
                                            <div className={`border border-slate-200 dark:border-slate-700 rounded-xl p-4 cursor-pointer transition-all ${purchaseAmount === 7 ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20' : 'hover:border-emerald-500'}`}
                                                onClick={() => setPurchaseAmount(7)}>
                                                <div className="text-xs text-slate-400 uppercase font-bold">Standard</div>
                                                <div className="text-2xl font-bold my-1">7 Credits</div>
                                                <div className="text-xs text-emerald-500">
                                                    ${(7 * 3.00).toFixed(2)} USD
                                                </div>
                                            </div>

                                            <div className={`border-2 rounded-xl p-4 cursor-pointer transition-all relative overflow-hidden group ${isMember ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20' : 'border-amber-400/80 hover:border-amber-500 hover:bg-amber-50 dark:hover:bg-amber-900/10'}`}
                                                onClick={() => !isMember && initiatePayment(0, true)}>
                                                {isMember && <div className="absolute top-0 right-0 bg-emerald-500 text-white text-[10px] px-2 py-0.5 font-bold">ACTIVE</div>}
                                                <div className="text-xs text-amber-600 dark:text-amber-500 uppercase font-bold mb-1">Vera-Pass 👑</div>
                                                <div className="text-xl font-bold mb-2">50 Credits</div>
                                                <div className="text-[10px] text-slate-500 dark:text-slate-400 leading-tight space-y-1 mb-2">
                                                    <li className="flex items-center gap-1"><span className="text-emerald-500">✓</span> Unlimited Triage</li>
                                                    <li className="flex items-center gap-1"><span className="text-emerald-500">✓</span> -33% Audits</li>
                                                    <li className="flex items-center gap-1"><span className="text-emerald-500">✓</span> Priority Scouting</li>
                                                </div>
                                                <div className="text-[10px] pt-2 border-t border-slate-200 dark:border-slate-700/50">
                                                    <div className="flex justify-between items-center text-slate-400">
                                                        <span>Active Until: {isMember ? 'Feb 20, 2026' : 'N/A'}</span>
                                                        <span className="font-mono opacity-75">{feeQuote?.subscription_amount?.toFixed(6)} ETH</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="mb-4 text-left mt-6">
                                            <label className="block text-xs font-bold text-slate-500 mb-1 ml-1">AMOUNT TO BUY</label>
                                            <div className="flex gap-2">
                                                <input
                                                    type="number"
                                                    min="1"
                                                    value={purchaseAmount}
                                                    onChange={(e) => setPurchaseAmount(Math.max(1, parseInt(e.target.value) || 0))}
                                                    className="flex-1 p-3 text-lg font-bold text-center rounded-xl bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white border-2 border-transparent focus:border-emerald-500 focus:bg-white dark:focus:bg-slate-900 outline-none transition-all"
                                                />
                                            </div>
                                        </div>

                                        <div className="flex gap-2 justify-center mb-6">
                                            {[1, 5, 10, 50].map(amt => (
                                                <button
                                                    key={amt}
                                                    onClick={() => setPurchaseAmount(amt)}
                                                    className={`px-3 py-1 text-xs font-bold rounded-full border transition-all ${purchaseAmount === amt ? 'bg-emerald-500 text-white border-emerald-500' : 'text-slate-500 border-slate-200 dark:border-slate-700 hover:border-emerald-400'}`}
                                                >
                                                    {amt}
                                                </button>
                                            ))}
                                        </div>

                                        <button
                                            onClick={() => initiatePayment(purchaseAmount)}
                                            className="w-full py-4 bg-emerald-500 text-white font-bold rounded-xl shadow-lg shadow-emerald-500/20 active:scale-95 transition-transform hover:bg-emerald-600 uppercase tracking-widest"
                                        >
                                            {paying ? "PROCESSING..." : "GET ACCESS"}
                                        </button>

                                        {/* Membership & Referral Card */}
                                        {userId && (
                                            <div className="mt-8 pt-6 border-t border-slate-200 dark:border-slate-800 text-left">
                                                <h3 className="text-sm font-bold text-slate-400 uppercase mb-4">Partner Program</h3>
                                                {myRefCode ? (
                                                    <div className="bg-slate-50 dark:bg-slate-800 p-4 rounded-xl flex justify-between items-center border border-slate-200 dark:border-slate-700">
                                                        <div>
                                                            <div className="text-xs text-slate-500">Your Code</div>
                                                            <div className="font-mono font-bold text-lg tracking-wider text-purple-500">{myRefCode}</div>
                                                        </div>
                                                        <div className="text-right">
                                                            <div className="text-xs text-slate-500">Earned</div>
                                                            <div className="font-bold text-emerald-500">+{referralStats.earned} Credits</div>
                                                            <div className="text-[10px] text-slate-400">{referralStats.uses} Uses</div>
                                                        </div>
                                                    </div>
                                                ) : (
                                                    <button
                                                        onClick={generateReferralCode}
                                                        className="w-full py-3 border border-dashed border-slate-300 dark:border-slate-700 rounded-xl text-slate-500 text-xs hover:bg-slate-50 dark:hover:bg-slate-800 transition-all font-mono"
                                                    >
                                                        [GENERATE REFERRAL LINK] <br />
                                                        (Requires Lifetime Spend {'>'} 0.01 ETH)
                                                    </button>
                                                )}
                                            </div>
                                        )}

                                    </div>
                                ) : (
                                    <>
                                        <div className="flex gap-4">
                                            <input
                                                type="text"
                                                value={address}
                                                onChange={(e) => setAddress(e.target.value)}
                                                placeholder="Enter Contract Address (e.g., 0x...)"
                                                className="flex-1 p-4 border rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono text-sm shadow-sm transition-shadow bg-slate-800 text-white border-slate-700 placeholder-slate-500"
                                            />
                                        </div>

                                        <button
                                            onClick={() => handleAudit()}
                                            disabled={analyzing || !address}
                                            className="w-full mt-4 py-4 bg-slate-900 dark:bg-emerald-600 text-white font-bold rounded-xl active:scale-95 transition-all disabled:opacity-50 hover:bg-slate-800 dark:hover:bg-emerald-700 shadow-lg"
                                        >
                                            {analyzing ? 'Scanning...' : 'Start Audit'}
                                        </button>
                                    </>
                                )}
                            </div>
                        )}

                        {!analyzing && (
                            <div className="max-w-xl mx-auto mt-8 border-t border-slate-200 dark:border-slate-800 pt-8">
                                <button
                                    onClick={() => setShowFrontier(!showFrontier)}
                                    className="w-full flex items-center justify-between p-4 bg-amber-50 dark:bg-amber-900/20 rounded-xl border border-amber-200 dark:border-amber-800/50 hover:bg-amber-100 dark:hover:bg-amber-900/40 transition-all group"
                                >
                                    <div className="flex items-center gap-3">
                                        <span className="text-2xl">🤠</span>
                                        <div className="text-left">
                                            <h3 className="font-bold text-amber-900 dark:text-amber-500 uppercase tracking-wider text-sm">The Sheriff's Frontier</h3>
                                            <p className="text-[10px] text-amber-800/60 dark:text-amber-400/60">Wanted Posters & Deputy Leaderboard</p>
                                        </div>
                                    </div>
                                    <span className={`transform transition-transform duration-300 ${showFrontier ? 'rotate-180' : ''}`}>▼</span>
                                </button>

                                {showFrontier && (
                                    <SheriffsFrontier />
                                )}
                            </div>
                        )}

                        {error && <p className="mt-4 text-red-500 text-center font-bold text-sm bg-red-50 dark:bg-red-900/20 p-3 rounded-lg border border-red-100 dark:border-red-900/50">{error}</p>}

                        {analyzing && (
                            <div className="max-w-xl mx-auto mb-12 animate-fade-in">
                                <AuditStory />
                            </div>
                        )
                        }

                        {score !== null && !analyzing && (
                            <div className="animate-fade-in-up">
                                <AuditReport
                                    score={score}
                                    warnings={warnings}
                                    riskSummary={riskSummary}
                                    milestones={milestones}
                                    vitals={vitals}
                                />

                                <div className="flex justify-center mt-8 mb-12">
                                    <button
                                        onClick={() => { setScore(null); setWarnings([]); setAddress(''); setRiskSummary(undefined); setMilestones([]); setVitals(undefined); }}
                                        className="px-8 py-3 bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold rounded-full shadow-sm hover:bg-emerald-500 hover:text-white transition-all flex items-center gap-2"
                                    >
                                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
                                        Scan Another Contract
                                    </button>
                                </div>
                            </div>
                        )
                        }

                        {score === null && !analyzing && !error && credits > 0 && (
                            <div className="text-center opacity-40 mt-20">
                                <div className="text-4xl mb-4 grayscale">🛡️</div>
                                <p className="text-base font-medium">Ready to secure the chain.</p>
                            </div>
                        )
                        }

                        {showDeepDiveModal && (
                            <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/60 backdrop-blur-sm sm:p-4">
                                <div className="bg-white dark:bg-slate-900 w-full sm:max-w-md rounded-t-2xl sm:rounded-2xl p-6 shadow-2xl border-t sm:border border-slate-200 dark:border-slate-700 animate-slide-up">
                                    <div className="flex items-center gap-3 mb-4 text-amber-500">
                                        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                                        <h3 className="text-xl font-bold text-slate-900 dark:text-white">Universal Ledger Alert</h3>
                                    </div>

                                    <p className="text-slate-600 dark:text-slate-300 mb-6 font-medium leading-relaxed">
                                        This contract exceeds <strong>24KB</strong> in bytecode size. Standard heuristics will likely miss hidden deeper logic vectors.
                                    </p>

                                    <div className="space-y-3">
                                        <button
                                            onClick={() => handleAudit(undefined, true)}
                                            className="w-full py-4 bg-emerald-600 text-white font-bold rounded-xl shadow-lg shadow-emerald-500/20 flex justify-between px-6 hover:bg-emerald-700 transition-colors mb-3"
                                        >
                                            <span>Recommended: Deep Dive</span>
                                            <span className="bg-white/20 px-2 py-0.5 rounded text-sm">
                                                {isMember ? <><span className="line-through opacity-70 mr-1">3</span>2 Credits</> : "3 Credits"}
                                            </span>
                                        </button>

                                        <button
                                            onClick={() => handleAudit(undefined, false, true)}
                                            className="w-full py-3 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 font-bold rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors mb-3 text-sm"
                                        >
                                            Standard Scan (1 Credit) - Risk of False Negatives
                                        </button>
                                    </div>
                                </div>
                            </div>
                        )}
                    </main>
                </>
            )}
        </div>
    );
}
