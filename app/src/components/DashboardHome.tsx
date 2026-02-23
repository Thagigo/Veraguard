import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';

import ProtocolDashboard from './ProtocolDashboard'
import AuditReport from './AuditReport'
import SheriffsFrontier from './SheriffsFrontier';
import LandingPage from './LandingPage';
import PreFlightPreview from './PreFlightPreview'; // [NEW]
import DistributionReceipt from './DistributionReceipt'; // [NEW]
import CrystallizationLoader from './CrystallizationLoader';
import PreFlightTriage from './PreFlightTriage';
import Executive from './Executive'; // [NEW]
import WarRoom from './WarRoom'; // [NEW]
import WebApp from '@twa-dev/sdk'
import '../App.css'


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

    // Smart Command History & Routing
    const [history, setHistory] = useState<any[]>([]);
    const [showTopUp, setShowTopUp] = useState(false);

    // State
    const [address, setAddress] = useState('')
    const [analyzing, setAnalyzing] = useState(false)
    const [score, setScore] = useState<number | null>(null)
    const [warnings, setWarnings] = useState<string[]>([])
    const [error, setError] = useState<string | null>(null);
    const [lifetimeSpend, setLifetimeSpend] = useState<number>(0);
    const [showPartnerModal, setShowPartnerModal] = useState(false);

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

    // Sidebar State
    const [railOpen, setRailOpen] = useState(false);

    // Audit State
    const [milestones, setMilestones] = useState<any[]>([]);
    const [riskSummary, setRiskSummary] = useState<string | undefined>(undefined);
    const [vitals, setVitals] = useState<any | undefined>(undefined);
    // [NEW] Premium Data
    const [redTeamLog, setRedTeamLog] = useState<any[]>([]);
    const [reportHash, setReportHash] = useState<string | undefined>(undefined);
    const [auditCost, setAuditCost] = useState<number>(3.00); // [NEW] Track Cost for Ledger
    const [creditSource, setCreditSource] = useState<string>('purchase'); // [NEW] Credit Source

    // Membership & Referral State
    const [isMember, setIsMember] = useState(false);
    const [myRefCode, setMyRefCode] = useState<string | null>(null);
    const [referralStats, setReferralStats] = useState({ uses: 0, earned: 0 });
    const [inputRefCode, setInputRefCode] = useState("");

    // God Mode / Dashboard State
    const [showDashboard, setShowDashboard] = useState(false)
    const [showExecutive, setShowExecutive] = useState(false) // [NEW]
    const [logoClicks, setLogoClicks] = useState(0);

    // Smart Audit State
    const [showTriage, setShowTriage] = useState(false);
    const [triageConfig, setTriageConfig] = useState<any>(null);
    const [matchedHistoryItem, setMatchedHistoryItem] = useState<any>(null);

    // Live Link & Transparency State
    const [referralBanner, setRefBanner] = useState<string | null>(null);
    const [showFrontier, setShowFrontier] = useState(false);

    const [isLiveView, setIsLiveView] = useState(false);
    // [NEW] Analysis Tier State
    const [analysisTier, setAnalysisTier] = useState<'triage' | 'deep'>('deep');

    // [NEW] Purchase Flow States
    const [showPreFlight, setShowPreFlight] = useState(false);
    const [pendingPurchase, setPendingPurchase] = useState<{ amount: number; isSubscription: boolean } | null>(null);
    const [showReceipt, setShowReceipt] = useState(false);
    const [paymentSuccessAmount, setPaymentSuccessAmount] = useState(0);

    const [paymentSuccessCost, setPaymentSuccessCost] = useState(0);

    // [NEW] Live Heuristic Heartbeat State
    const [livePing, setLivePing] = useState<string | null>(null);
    const [liveIntelligence, setLiveIntelligence] = useState<string | null>(null);
    // [NEW] Spoof Alert State
    const [spoofAlert, setSpoofAlert] = useState<string | null>(null);
    // [NEW] History of Suspicion
    const [initialDetection, setInitialDetection] = useState<{ score: number; source: string; detected_at: number } | null>(null);



    // Initialize Telegram & Fee (User ID handled by parent)
    // [NEW] Fetch History
    // Initialize Telegram & Fee (User ID handled by parent)
    useEffect(() => {
        // Initialization moved to ensure functions are defined

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

        // Listen for Treasury visualizer event
        const handleOpenDash = () => setShowDashboard(true);
        window.addEventListener('open-protocol-dashboard', handleOpenDash);

        // [NEW] Live Events SSE Connection
        const source = new EventSource('http://localhost:8000/api/live_events');
        source.onmessage = function (event) {
            try {
                const data = JSON.parse(event.data);
                const eventType = data.event;
                const payload = typeof data.data === 'string' ? JSON.parse(data.data) : data.data;

                if (eventType === 'contract_detected') {
                    if (window.Telegram?.WebApp?.HapticFeedback) {
                        window.Telegram.WebApp.HapticFeedback.impactOccurred('light');
                    }
                    setLivePing(payload.address);
                    setTimeout(() => setLivePing(null), 2500);
                } else if (eventType === 'intelligence_update') {
                    if (window.Telegram?.WebApp?.HapticFeedback) {
                        window.Telegram.WebApp.HapticFeedback.notificationOccurred('success');
                    }
                    setLiveIntelligence(payload.heuristic);
                    setTimeout(() => setLiveIntelligence(null), 6000);
                } else if (eventType === 'brain_discovery') {
                    if (window.Telegram?.WebApp?.HapticFeedback) {
                        window.Telegram.WebApp.HapticFeedback.notificationOccurred('success');
                    }
                    setLiveIntelligence("🧠 BRAIN DISCOVERY: New detection rule staged.");
                    setTimeout(() => setLiveIntelligence(null), 8000);
                } else if (eventType === 'spoof_alert') {
                    if (window.Telegram?.WebApp?.HapticFeedback) {
                        window.Telegram.WebApp.HapticFeedback.notificationOccurred('warning');
                    }
                    setSpoofAlert(payload.message);
                    setTimeout(() => setSpoofAlert(null), 6000);
                }
            } catch (e) {
                console.error("SSE parse error", e);
            }
        };

        return () => {
            clearInterval(timer);
            window.removeEventListener('open-protocol-dashboard', handleOpenDash);
            source.close();
        };

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
                setRedTeamLog(r.red_team_log || []);
                setReportHash(r.report_hash);
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
                setLifetimeSpend(data.lifetime_spend_eth || 0)
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

    // Smart Routing Logic

    const showAuditInput = (credits > 0 || isMember) && !showTopUp;

    const handleHistoryClick = (item: any) => {
        if (item.is_proxy) {
            setMatchedHistoryItem(item); // Trigger "Logic Update" warning
            setAddress(item.address);
        } else {
            // Load Full Report State
            setScore(item.score);
            setWarnings(item.warnings || []);
            setMilestones(item.milestones || []);
            setVitals(item.vitals);
            setRiskSummary(item.risk_summary);

            // [Fix] Premium Persistence
            if (item.red_team_log) setRedTeamLog(item.red_team_log);
            if (item.report_hash) setReportHash(item.report_hash);
            if (item.cost) setAuditCost(item.cost); // [NEW] Restore Cost
            // [NEW] Restore Source
            setCreditSource(item.credit_source || 'purchase');

            setAddress(item.address);
        }
    };

    // Smart Re-Scan Protection
    useEffect(() => {
        if (!address) {
            setMatchedHistoryItem(null);
            return;
        }
        const match = history.find(h => h.address.toLowerCase() === address.toLowerCase());
        setMatchedHistoryItem(match || null);
    }, [address, history]);

    const handleViewReport = () => {
        if (!matchedHistoryItem) return;
        setScore(matchedHistoryItem.score);
        setWarnings(matchedHistoryItem.warnings || []);
        setMilestones(matchedHistoryItem.milestones || []);
        setVitals(matchedHistoryItem.vitals);
        setRiskSummary(matchedHistoryItem.risk_summary);
        setRedTeamLog(matchedHistoryItem.red_team_log || []);
        setReportHash(matchedHistoryItem.report_hash);
        if (matchedHistoryItem.cost) setAuditCost(matchedHistoryItem.cost); // [NEW] Restore Cost
        // [NEW] Restore Source
        setCreditSource(matchedHistoryItem.credit_source || 'purchase');

        WebApp.HapticFeedback.notificationOccurred('success');
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
            if (data.lifetime_spend_eth !== undefined) {
                setLifetimeSpend(data.lifetime_spend_eth);
            }
            fetchReferralData(userId); // Refresh in case they just unlocked it

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

    // [NEW] Fetch History (Moved)
    const fetchHistory = useCallback((uid: string) => {
        if (!uid) return;
        fetch(`http://localhost:8000/api/history/${uid}`)
            .then(res => res.json())
            .then(data => setHistory(data))
            .catch(err => console.error("Failed to fetch history:", err));
    }, []);

    // Initialize Data (Moved to respect hoisting)
    useEffect(() => {
        fetchCredits(userId);
        fetchFee();
        fetchReferralData(userId);
        fetchHistory(userId);
    }, [userId]); // Functions omitted from deps to avoid infinite loop (they are not memoized)

    const handleAudit = useCallback(async (e?: React.FormEvent, confirmDeepDive: boolean = false, bypassDeepDive: boolean = false, confirmTriage: boolean = false) => {
        if (e) e.preventDefault();

        // [NEW] Smart Re-Scan Bypass
        if (matchedHistoryItem && !matchedHistoryItem.is_proxy) {
            handleViewReport();
            return;
        }

        if (!address && !confirmDeepDive && !bypassDeepDive) return;

        // [NEW] Pre-Flight Triage Intercept
        if (!confirmDeepDive && !bypassDeepDive && !confirmTriage && !matchedHistoryItem) {
            // Heuristic Complexity Check (Mocked for now, or based on backend "dry run"?)
            // Since we don't have a cheap dry run endpoint yet, we'll use a local heuristic or just always show Triage for new addresses.
            // Let's assume complexity is 'Standard' unless address contains 'huge' (Simulation).
            const isComplex = address.toLowerCase().includes('huge') || address.toLowerCase().includes('deep');

            setTriageConfig({
                address: address,
                complexity: isComplex ? 'High' : 'Standard',
                isProxy: false, // We don't know yet without scan, simulating for Triage
                cost: isComplex ? 3 : 1
            });
            setShowTriage(true);
            return;
        }

        const targetAddress = (confirmDeepDive || bypassDeepDive) && pendingDeepDiveAddress ? pendingDeepDiveAddress : address;

        WebApp.MainButton.showProgress(false);
        WebApp.MainButton.showProgress(true);
        setAnalyzing(true);

        const tier = confirmDeepDive ? 'deep' : 'triage';
        setAnalysisTier(tier); // Update State

        // Enforce Minimum Animation Duration
        const minDuration = tier === 'deep' ? 7000 : 2000;

        setError(null);
        setScore(null);
        setWarnings([]);
        setMilestones([]);
        setRiskSummary(undefined);
        setVitals(undefined);
        setRedTeamLog([]);
        setReportHash(undefined);
        setInitialDetection(null);  // [NEW] Clear history on new scan
        setShowDeepDiveModal(false);

        try {
            const auditPromise = fetch('http://localhost:8000/api/audit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    address: pendingDeepDiveAddress || address,
                    user_id: userId,
                    confirm_deep_dive: confirmDeepDive,
                    bypass_deep_dive: bypassDeepDive
                })
            });

            const delayPromise = new Promise(resolve => setTimeout(resolve, minDuration));

            // Wait for both
            const [response] = await Promise.all([auditPromise, delayPromise]);

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
                setRedTeamLog(data.red_team_log || [])
                setVitals(data.vitals)
                setRedTeamLog(data.red_team_log || [])
                setReportHash(data.report_hash)
                // [NEW] History of Suspicion — set if backend returned initial_detection
                if (data.initial_detection) setInitialDetection(data.initial_detection);
                // [NEW] Set Cost for Ledger (Default to standard/deep pricing if logic missing)
                setAuditCost(data.cost_deducted || (confirmDeepDive ? (isMember ? 2 : 3) : (isMember ? 0 : 1)));

                fetchCredits(userId);
                fetchHistory(userId); // Refresh history immediately
                WebApp.HapticFeedback.notificationOccurred('success');

            }

        } catch (err: any) {
            setError(err.message || "Something went wrong. Is the backend running?")
            WebApp.HapticFeedback.notificationOccurred('error');
        } finally {
            setAnalyzing(false);
            WebApp.MainButton.hideProgress();
        }

    }, [address, userId, pendingDeepDiveAddress, showDeepDiveModal, matchedHistoryItem]);


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
            WebApp.HapticFeedback.notificationOccurred('success');
        } else if (newCount === 5) {
            // [NEW] Trigger Executive Dashboard
            setShowExecutive(true);
            setLogoClicks(0);
            WebApp.HapticFeedback.impactOccurred('heavy');
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
            {showExecutive && <Executive isOpen={showExecutive} onClose={() => setShowExecutive(false)} userId={userId} />}



            {referralBanner && (
                <div className="bg-indigo-600 text-white px-4 py-2 text-xs font-bold flex justify-between items-center animate-slide-down shadow-md relative z-50">
                    <div className="flex items-center gap-2">
                        <span className="bg-slate-800 p-1 rounded-full">🤝</span>
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

            {/* [UPGRADED] Thought Stream Toast — Cognitive Control Plane */}
            {liveIntelligence && (
                <div className="fixed bottom-4 left-4 right-4 md:left-auto md:right-6 md:w-[420px] z-50 animate-slide-up">
                    <div className="bg-slate-900 border border-amber-500/60 rounded-xl shadow-2xl shadow-amber-500/20 overflow-hidden">
                        <div className="h-0.5 bg-amber-400 animate-pulse" />
                        <div className="px-4 py-3 flex items-start gap-3">
                            <span className="text-2xl animate-pulse mt-0.5">🧠</span>
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="text-[10px] font-bold text-amber-400 uppercase tracking-widest">Cognitive Control Plane</span>
                                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping inline-block" />
                                </div>
                                <p className="text-sm text-white font-mono leading-snug break-words">
                                    {liveIntelligence}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* [NEW] Spoof Alert Toast — Blue False-Positive Block */}
            {spoofAlert && (
                <div className="fixed bottom-4 left-4 right-4 md:left-auto md:right-6 md:w-[420px] z-50 animate-slide-up" style={{ bottom: liveIntelligence ? '9rem' : '1rem' }}>
                    <div className="bg-slate-900 border border-blue-500/60 rounded-xl shadow-2xl shadow-blue-500/20 overflow-hidden">
                        <div className="h-0.5 bg-blue-400 animate-pulse" />
                        <div className="px-4 py-3 flex items-start gap-3">
                            <span className="text-2xl mt-0.5">🔵</span>
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="text-[10px] font-bold text-blue-400 uppercase tracking-widest">Spoof Alert</span>
                                    <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-ping inline-block" />
                                </div>
                                <p className="text-sm text-blue-100 font-mono leading-snug break-words">
                                    {spoofAlert}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            )}


            {!walletAddress ? (
                <LandingPage onConnect={connectWallet} />
            ) : (
                <>
                    <header className="sticky top-0 z-40 transition-all duration-300 backdrop-blur-xl bg-slate-900/90 border-b border-white/5 shadow-2xl">
                        <div className="max-w-[1400px] mx-auto flex justify-between items-center px-4 md:px-10 py-3 md:py-5">
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

                                {livePing && (
                                    <div className="bg-blue-500/90 text-white text-[10px] font-bold px-2 py-1 rounded-full animate-pulse border border-blue-400/50" title={livePing}>
                                        ⚡ SCOUT PING
                                    </div>
                                )}

                                {/* Profile Chip / HUD */}
                                <div className="flex items-center gap-3 bg-slate-800/50 rounded-full pr-1 pl-4 py-1 border border-slate-700/50 hover:border-emerald-500/30 transition-colors group">
                                    <div className="flex flex-col text-right">
                                        <div className="text-[10px] uppercase font-bold text-slate-500 flex items-center justify-end gap-1">
                                            <span>Authenticated</span>
                                            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.8)]"></div>
                                        </div>
                                        <div className="text-xs font-mono text-emerald-400 font-bold tracking-wide">
                                            {walletAddress ? `${walletAddress.substring(0, 6)}...${walletAddress.substring(walletAddress.length - 4)}` : 'Connect Wallet'}
                                        </div>
                                    </div>

                                    <div className="h-6 w-px bg-slate-700 mx-1"></div>

                                    <button
                                        onClick={() => navigate('/vault')}
                                        className="p-2 hover:bg-slate-700 rounded-full transition-colors relative"
                                        title="View Vault"
                                    >
                                        <span className="text-lg block hover:scale-110 transition-transform">🏛️</span>
                                    </button>

                                    <button
                                        onClick={onLogout}
                                        className="p-2 hover:bg-red-500/20 rounded-full transition-colors relative group/logout"
                                        title="TERMINATE SECURE SESSION (Sovereign Reset)"
                                    >
                                        <span className="text-lg block group-hover/logout:text-red-400 transition-colors">🛑</span>
                                    </button>
                                </div>

                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={() => setRailOpen(r => !r)}
                                        className={`text-[10px] px-2 py-1.5 rounded-lg border font-mono transition-all flex items-center gap-1.5
                                            ${railOpen ? 'bg-rose-500/10 border-rose-500/50 text-rose-500 shadow-[0_0_15px_rgba(244,63,94,0.1)]' : 'bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-500 hover:text-slate-200'}`}
                                    >
                                        <span className={railOpen ? 'animate-pulse' : ''}>⚔</span> WAR ROOM {railOpen ? '▶' : '◀'}
                                    </button>

                                    <div
                                        onClick={() => setShowTopUp(!showTopUp)}
                                        className="text-sm font-bold px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 shadow-inner min-w-[80px] text-center cursor-pointer hover:bg-slate-700 transition-colors select-none"
                                        title="Toggle Top Up View"
                                    >
                                        <span className={credits > 0 ? "text-emerald-400" : "text-slate-400"}>{credits}</span> <span className="text-[10px] uppercase text-slate-500">CRD</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </header>

                    <div className="flex flex-1 overflow-hidden">
                        <div className="flex-1 overflow-y-auto">
                            <main className="container mx-auto px-4 py-8 pb-32">
                                {score === null && (
                                    <div className="max-w-xl mx-auto mb-12">
                                        <AnimatePresence mode="wait">
                                            {!showAuditInput ? (
                                                <motion.div
                                                    key="top-up"
                                                    initial={{ opacity: 0, y: 20 }}
                                                    animate={{ opacity: 1, y: 0 }}
                                                    exit={{ opacity: 0, y: -20 }}
                                                    transition={{ duration: 0.3 }}
                                                >
                                                    <div className="text-center p-6 rounded-2xl shadow-xl border border-slate-800 bg-slate-900/95">
                                                        {/* Top Up UI */}
                                                        <div className="mb-6">
                                                            <div className="inline-block p-3 rounded-full bg-emerald-900/30 text-emerald-500 mb-2">
                                                                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                                                            </div>
                                                            <h2 className="text-xl font-bold">Top Up Credits</h2>
                                                            <p className="text-sm text-slate-500 dark:text-slate-400">Secure audits require verified tokens.</p>
                                                        </div>

                                                        {/* Cost Display */}
                                                        <div className="p-4 rounded-xl mb-6 bg-slate-800/50 border border-slate-700">
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
                                                            <div className={`border border-slate-700 rounded-xl p-4 cursor-pointer transition-all ${purchaseAmount === 7 ? 'border-emerald-500 bg-emerald-900/20' : 'hover:border-emerald-500'}`}
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
                                                                    <li className="flex items-center gap-1 group/perk cursor-help" title="Free instant X-rays on any contract. No credit cost.">
                                                                        <span className="text-emerald-500">✓</span> Unlimited Triage <span className="text-slate-600 opacity-0 group-hover/perk:opacity-100 transition-opacity">?</span>
                                                                    </li>
                                                                    <li className="flex items-center gap-1 group/perk cursor-help" title="Premium audits for 2 CRD (Save 33% per scan).">
                                                                        <span className="text-emerald-500">✓</span> -33% Audits <span className="text-slate-600 opacity-0 group-hover/perk:opacity-100 transition-opacity">?</span>
                                                                    </li>
                                                                    <li className="flex items-center gap-1 group/perk cursor-help" title="5-minute head-start on new threats. Claim the First-Bust bonus before the public.">
                                                                        <span className="text-emerald-500">✓</span> Priority Scouting <span className="text-slate-600 opacity-0 group-hover/perk:opacity-100 transition-opacity">?</span>
                                                                    </li>
                                                                </div>
                                                                <div className="text-[10px] pt-2 border-t border-slate-800">
                                                                    <div className="flex justify-between items-center text-slate-400">
                                                                        <span>Active Until: {isMember ? new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toLocaleDateString() : 'N/A'}</span>
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
                                                                    className="flex-1 p-3 text-lg font-bold text-center rounded-xl bg-slate-800 text-slate-100 border-2 border-transparent focus:border-emerald-500 focus:bg-slate-900 outline-none transition-all"
                                                                />
                                                            </div>
                                                        </div>

                                                        <div className="flex gap-2 justify-center mb-6">
                                                            {[1, 5, 10, 50].map(amt => (
                                                                <button
                                                                    key={amt}
                                                                    onClick={() => setPurchaseAmount(amt)}
                                                                    className={`px-3 py-1 text-xs font-bold rounded-full border transition-all ${purchaseAmount === amt ? 'bg-emerald-500 text-white border-emerald-500' : 'text-slate-500 border-slate-800 hover:border-emerald-400'}`}
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
                                                            <div className="mt-8 pt-6 border-t border-slate-800 text-left">
                                                                <h3 className="text-sm font-bold text-slate-400 uppercase mb-4">Partner Program</h3>
                                                                {myRefCode ? (
                                                                    <div className="bg-slate-800 p-4 rounded-xl flex justify-between items-center border border-slate-700">
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
                                                                    <div className="relative group">
                                                                        <div className={`p-5 rounded-xl border transition-all duration-300 relative overflow-hidden ${lifetimeSpend >= 0.01 ? 'bg-gradient-to-br from-indigo-900/40 to-purple-900/40 border-indigo-500/50 shadow-[0_0_30px_rgba(99,102,241,0.15)]' : 'bg-slate-800/50 border-slate-700/50 blur-[0.5px] opacity-90'}`}>
                                                                            {/* Glassmorphism Shine */}
                                                                            {lifetimeSpend >= 0.01 && <div className="absolute inset-0 bg-gradient-to-tr from-white/5 to-transparent pointer-events-none"></div>}

                                                                            <div className="flex justify-between items-center mb-3 relative z-10">
                                                                                <h4 className={`text-xs font-bold uppercase tracking-widest ${lifetimeSpend >= 0.01 ? 'text-indigo-300 drop-shadow-[0_0_8px_rgba(165,180,252,0.5)]' : 'text-slate-500'}`}>
                                                                                    Sovereign Partner Keys
                                                                                </h4>
                                                                                {lifetimeSpend < 0.01 && (
                                                                                    <div className="text-[10px] bg-slate-200 dark:bg-slate-700 text-slate-500 px-2 py-0.5 rounded flex items-center gap-1 font-bold">
                                                                                        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
                                                                                        LOCKED
                                                                                    </div>
                                                                                )}
                                                                            </div>

                                                                            <div className="relative z-10">
                                                                                {lifetimeSpend >= 0.01 ? (
                                                                                    <button
                                                                                        onClick={generateReferralCode}
                                                                                        className="w-full py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold rounded-lg shadow-lg shadow-indigo-500/30 transition-all active:scale-95 flex items-center justify-center gap-2"
                                                                                    >
                                                                                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" /></svg>
                                                                                        ACTIVATE PARTNER KEYS
                                                                                    </button>
                                                                                ) : (
                                                                                    <button
                                                                                        onClick={() => setShowPartnerModal(true)}
                                                                                        className="w-full py-3 bg-slate-200 dark:bg-slate-800 text-slate-500 font-mono text-xs rounded-lg cursor-not-allowed opacity-70 hover:opacity-100 transition-opacity"
                                                                                    >
                                                                                        [GENERATE REFERRAL LINK]
                                                                                    </button>
                                                                                )}
                                                                            </div>
                                                                        </div>
                                                                    </div>
                                                                )}
                                                            </div>
                                                        )}

                                                    </div>
                                                </motion.div>
                                            ) : (
                                                <motion.div
                                                    key="audit-input"
                                                    initial={{ opacity: 0, y: 20 }}
                                                    animate={{ opacity: 1, y: 0 }}
                                                    exit={{ opacity: 0, y: -20 }}
                                                    transition={{ duration: 0.3 }}
                                                    className="relative"
                                                >
                                                    {analyzing ? (
                                                        <CrystallizationLoader tier={analysisTier} />
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
                                                                className={`w-full mt-4 py-4 text-white font-bold rounded-xl active:scale-95 transition-all disabled:opacity-50 shadow-lg
                                                        ${matchedHistoryItem
                                                                        ? matchedHistoryItem.is_proxy
                                                                            ? "bg-amber-600 hover:bg-amber-700 shadow-amber-900/20"
                                                                            : "bg-blue-600 hover:bg-blue-700 shadow-blue-900/20"
                                                                        : "bg-emerald-600 hover:bg-emerald-700"
                                                                    }`}
                                                            >
                                                                {analyzing ? 'INITIALIZING...' : matchedHistoryItem
                                                                    ? matchedHistoryItem.is_proxy
                                                                        ? "⚠️ LOGIC UPDATE DETECTED - RE-AUDIT"
                                                                        : "VIEW REPORT (FREE)"
                                                                    : 'START AUDIT'}
                                                            </button>
                                                        </>
                                                    )}

                                                    {/* Pre-Flight Triage Modal */}
                                                    <AnimatePresence>
                                                        {showTriage && triageConfig && (
                                                            <PreFlightTriage
                                                                address={triageConfig.address}
                                                                complexity={triageConfig.complexity}
                                                                isProxy={triageConfig.isProxy}
                                                                cost={triageConfig.cost}
                                                                isMember={isMember}
                                                                onMainAction={() => {
                                                                    setShowTriage(false);
                                                                    handleAudit(undefined, triageConfig.complexity === 'High', false, true);
                                                                }}
                                                                onBypass={triageConfig.complexity === 'High' ? () => {
                                                                    setShowTriage(false);
                                                                    handleAudit(undefined, false, true, true);
                                                                } : undefined}
                                                                onCancel={() => setShowTriage(false)}
                                                            />
                                                        )}
                                                    </AnimatePresence>

                                                    {/* Recent Targets (Smart Command History) */}
                                                    {history.length > 0 && (
                                                        <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800/50">
                                                            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2 ml-1">Recent Targets</div>
                                                            <div className="flex flex-wrap gap-2">
                                                                {history.map((item, i) => (
                                                                    <button
                                                                        key={i}
                                                                        onClick={() => handleHistoryClick(item)}
                                                                        className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 rounded-lg border border-slate-700 hover:border-emerald-500/50 active:scale-95 transition-all text-xs font-mono text-slate-300 group"
                                                                    >
                                                                        <div className={`w-2 h-2 rounded-full ${item.score < 50 ? 'bg-red-500' : item.score > 80 ? 'bg-emerald-500' : 'bg-amber-500'}`}></div>
                                                                        {item.address.substring(0, 6)}...{item.address.substring(item.address.length - 4)}
                                                                        <span className="opacity-0 group-hover:opacity-100 transition-opacity text-emerald-500">
                                                                            ↻
                                                                        </span>
                                                                    </button>
                                                                ))}
                                                            </div>
                                                        </div>
                                                    )}


                                                </motion.div>
                                            )}
                                        </AnimatePresence>
                                    </div>
                                )}

                                {score !== null && !analyzing && (
                                    <div className="animate-fade-in-up">
                                        <AuditReport
                                            score={score}
                                            warnings={warnings}
                                            riskSummary={riskSummary}
                                            milestones={milestones}
                                            vitals={vitals}
                                            redTeamLog={redTeamLog}
                                            reportHash={reportHash}
                                            cost={auditCost} // [NEW]
                                            creditSource={creditSource} // [NEW]
                                            initialDetection={initialDetection ?? undefined}  // [NEW] History of Suspicion
                                        />

                                        <div className="flex justify-center mt-8 mb-12">
                                            <button
                                                onClick={() => { setScore(null); setWarnings([]); setAddress(''); setRiskSummary(undefined); setMilestones([]); setVitals(undefined); setRedTeamLog([]); setReportHash(undefined); }}
                                                className="px-8 py-3 bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold rounded-full shadow-sm hover:bg-emerald-500 hover:text-white transition-all flex items-center gap-2"
                                            >
                                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
                                                Scan Another Contract
                                            </button>
                                        </div>
                                    </div>
                                )}

                                {!analyzing && (
                                    <div className="max-w-xl mx-auto mt-8 border-t border-slate-800 pt-8">
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

                                {score === null && !analyzing && !error && credits > 0 && (
                                    <div className="text-center opacity-40 mt-20">
                                        <div className="text-4xl mb-4 grayscale">🛡️</div>
                                        <p className="text-base font-medium">Ready to secure the chain.</p>
                                    </div>
                                )}

                                {showDeepDiveModal && (
                                    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/60 backdrop-blur-sm sm:p-4">
                                        <div className="bg-slate-900 w-full sm:max-w-md rounded-t-2xl sm:rounded-2xl p-6 shadow-2xl border-t sm:border border-slate-800 animate-slide-up">
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
                                                    <span className="bg-slate-800 px-2 py-0.5 rounded text-sm">
                                                        {isMember ? <><span className="line-through opacity-70 mr-1">3</span>2 Credits</> : "3 Credits"}
                                                    </span>
                                                </button>

                                                <button
                                                    onClick={() => handleAudit(undefined, false, true)}
                                                    className="w-full py-3 bg-slate-800 text-slate-400 font-bold rounded-xl border border-slate-700 hover:bg-slate-700 transition-colors mb-3 text-sm"
                                                >
                                                    Standard Scan ({isMember ? "Free" : "1 Credit"}) - Risk of False Negatives
                                                </button>

                                                <button
                                                    onClick={() => { setShowDeepDiveModal(false); setAnalyzing(false); }}
                                                    className="w-full py-3 text-slate-400 font-bold hover:text-slate-200 transition-colors text-sm"
                                                >
                                                    Cancel
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Partner Eligibility Modal */}
                                {showPartnerModal && (
                                    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-fade-in">
                                        <div className="bg-slate-900 w-full max-w-sm rounded-2xl p-6 shadow-2xl border border-slate-800 relative overflow-hidden">
                                            {/* Background Decor */}
                                            <div className="absolute -top-10 -right-10 w-32 h-32 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none"></div>

                                            <div className="flex justify-between items-start mb-4 relative z-10">
                                                <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                                                    <span className="text-xl">🏆</span> Partner Eligibility
                                                </h3>
                                                <button onClick={() => setShowPartnerModal(false)} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors p-1 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full">
                                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                                                </button>
                                            </div>

                                            <p className="text-sm text-slate-600 dark:text-slate-300 mb-6 leading-relaxed">
                                                Establish your reputation on-chain. Complete more audits to unlock the <span className="text-indigo-500 font-bold">Sovereign Partner Program</span> and earn rewards.
                                            </p>

                                            <div className="mb-6">
                                                <div className="flex justify-between text-xs font-bold mb-2">
                                                    <span className="text-slate-500">PROGRESS</span>
                                                    <span className="text-indigo-500">{lifetimeSpend.toFixed(4)} / 0.0100 ETH</span>
                                                </div>
                                                <div className="h-3 bg-slate-800 rounded-full overflow-hidden border border-slate-700">
                                                    <div
                                                        className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-1000 ease-out relative"
                                                        style={{ width: `${Math.min(100, (lifetimeSpend / 0.01) * 100)}%` }}
                                                    >
                                                        <div className="absolute inset-0 bg-slate-700/20 animate-[shimmer_2s_infinite]"></div>
                                                    </div>
                                                </div>
                                                <div className="text-[10px] text-right mt-1 text-slate-400">
                                                    {((lifetimeSpend / 0.01) * 100).toFixed(0)}% Complete
                                                </div>
                                            </div>

                                            <button
                                                onClick={() => setShowPartnerModal(false)}
                                                className="w-full py-3 bg-slate-800 text-white font-bold rounded-xl active:scale-95 transition-transform"
                                            >
                                                Keep Building Reputation
                                            </button>
                                        </div>
                                    </div>
                                )}

                                {/* Legal & Security Vitals Footer */}
                                <div className="max-w-7xl mx-auto mt-24 border-t border-slate-800 pt-8 pb-4 opacity-70 hover:opacity-100 transition-opacity">
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-[10px] text-slate-500 font-mono">
                                        <div>
                                            <h4 className="font-bold text-slate-400 mb-2 uppercase tracking-widest">Sovereign Guarantee</h4>
                                            <p className="mb-2">
                                                All credits are backed by the <a href="/Whitepaper.md" target="_blank" className="text-emerald-500 hover:underline">VeraAnchor Service Level Agreement</a>.
                                                Audit proofs are chronologically anchored to the Ethereum State Trie.
                                            </p>
                                            <div className="flex items-center gap-2">
                                                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
                                                <span>Restitution Timer: ACTIVE (24h)</span>
                                            </div>
                                        </div>
                                        <div className="text-center">
                                            <h4 className="font-bold text-slate-400 mb-2 uppercase tracking-widest">Insurance Multiplier</h4>
                                            <div className="text-2xl font-bold text-slate-300">3.42<span className="text-emerald-500">x</span></div>
                                            <p className="text-slate-600">Total War Chest / Active Escrow</p>
                                            <div className="mt-1 text-[9px] uppercase text-emerald-500/80">Solvency Verified</div>
                                        </div>
                                        <div className="text-right">
                                            <h4 className="font-bold text-slate-400 mb-2 uppercase tracking-widest">Compliance Vault</h4>
                                            <ul className="space-y-1">
                                                <li>MiCAR Status: <span className="text-amber-500">Self-Custodial Utility</span></li>
                                                <li>Data Retention: <span className="text-emerald-500">Ephemeral (Shredded)</span></li>
                                                <li>Jurisdiction: <span className="text-slate-400">On-Chain (Global)</span></li>
                                            </ul>
                                        </div>
                                    </div>
                                    <div className="text-center mt-8 text-[9px] text-slate-700">
                                        0xVeraGuard • Sovereign Code Audit Protocol • v2.1.0-beta
                                    </div>
                                </div>
                            </main>
                        </div>

                        {/* ── Tactical Rail: War Room ─────────────────────────── */}
                        {railOpen && (
                            <div className="w-[300px] shrink-0 border-l border-slate-800 bg-slate-950 flex flex-col overflow-y-auto animate-slide-left">
                                <WarRoom compact />
                            </div>
                        )}
                    </div>
                </>
            )
            }
        </div >
    );
}
