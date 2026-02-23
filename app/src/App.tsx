import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import DashboardHome from './components/DashboardHome'
import Vault from './components/Vault'
import SecurityVerification from './components/SecurityVerification'
import WebApp from '@twa-dev/sdk'
import './App.css'
import ErrorBoundary from './components/ErrorBoundary';

export default function App() {
  const [verified, setVerified] = useState(false);
  const [userId, setUserId] = useState<string>('');

  useEffect(() => {
    // 1. Initialize Telegram
    WebApp.ready();
    WebApp.expand();

    // 2. Identify User
    let currentUserId = '';
    if (WebApp.initDataUnsafe.user) {
      currentUserId = String(WebApp.initDataUnsafe.user.id);
    } else {
      const stored = localStorage.getItem('veraguard_user_id');
      currentUserId = stored || 'user_' + Math.random().toString(36).substr(2, 9);
      if (!stored) localStorage.setItem('veraguard_user_id', currentUserId);
    }
    setUserId(currentUserId);

    // Theme Sync
    const syncTheme = () => {
      document.documentElement.classList.add('dark');
      const isDark = true; // Enforce dark aesthetic
      document.documentElement.style.setProperty('--tg-theme-bg-color', WebApp.backgroundColor || '#000000');
      document.documentElement.style.setProperty('--tg-theme-text-color', WebApp.themeParams.text_color || (isDark ? '#ffffff' : '#000000'));
    };
    syncTheme();
    WebApp.onEvent('themeChanged', syncTheme);

  }, []);

  const handleLogout = () => {
    // Sovereign Reset (Session Only)
    // localStorage.removeItem('veraguard_user_id'); // Keep User ID to retain credits
    localStorage.removeItem('veraguard_wallet');
    window.location.href = "/";
  };

  if (!verified) {
    return <SecurityVerification onComplete={() => setVerified(true)} />;
  }

  return (
    <ErrorBoundary>
      <BrowserRouter>
        <div className="min-h-screen bg-slate-900 text-white font-sans selection:bg-emerald-500/30">
          <Routes>
            <Route path="/" element={<DashboardHome userId={userId} onLogout={handleLogout} />} />
            <Route path="/vault" element={<Vault userId={userId} />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </BrowserRouter>
    </ErrorBoundary>
  )
}
