import time
import random
import json
from datetime import datetime
from collections import deque

class BaseScout:
    def __init__(self):
        self.daily_budget = 0.50 # Baseline daily budget in USD
        self.current_spend = 0.00
        self.cost_per_scan = 0.01 # Cost for a "Gemini Flash" scan
        self.last_reset = datetime.now().date()
        self.logs = deque(maxlen=50) # Buffer last 50 logs for UI

        # Load Private Heuristics or Fallback
        try:
            from core.private_logic.prompts import SCOUT_HEURISTICS
            self.heuristics = SCOUT_HEURISTICS
            self.log("[SCOUT] Private Heuristics Loaded.", "system")
        except ImportError:
            self.heuristics = {
                "min_liquidity": 10000,
                # Known-bad hex patterns — any address containing these is high-risk
                "zero_credit_filters": ["000dead", "badc0de", "deadbeef", "baddeed", "cafebabe", "phantom_mint"]
            }
            self.log("[SCOUT] Running in PUBLIC SHELL mode (Reduced capabilities).", "warning")


    def log(self, message: str, type: str = "info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        print(entry) # Keep stdout for debug
        self.logs.appendleft({"timestamp": timestamp, "message": message, "type": type})

    def check_liquidity(self, address: str) -> float:
        """
        Mocks a liquidity check on Base/Uniswap.
        In production, this would query a DEX subgraph or RPC.
        """
        # [OPEN CORE] Use loaded heuristics
        threshold = self.heuristics.get("min_liquidity", 5000)

        # Simulation: 
        # - Small contracts (< threshold) are filtered out.
        # - "High Value" scams have > $10k.
        if "scam" in address.lower() or "high" in address.lower():
            return random.uniform(10000, 50000)
        elif "low" in address.lower():
            return random.uniform(100, threshold - 1)
        else:
            return random.uniform(threshold, 15000) # Random realistic liquidity

    def manage_budget(self) -> bool:
        """
        Checks if we have budget for another scan.
        Resets budget if it's a new day.
        """
        today = datetime.now().date()
        if today > self.last_reset:
            self.current_spend = 0.00
            self.daily_budget = 5.00 # Reset to baseline (Increased via Value Filter optimization)
            self.last_reset = today
            self.log(f"New day. Budget reset to ${self.daily_budget}", "system")

        if self.current_spend + self.cost_per_scan <= self.daily_budget:
            return True
        return False

    def spend_budget(self):
        self.current_spend += self.cost_per_scan

    def refill_budget(self, amount: float):
        """
        Increases the daily budget. 
        Called when users pay for audits (Deep Hunter revenue share).
        """
        self.daily_budget += amount
        self.log(f"Budget refilled by ${amount}. New Budget: ${self.daily_budget:.2f}", "success")

    def stateless_triage(self, address: str) -> float:
        """
        Pre-Credit Filter checking:
        1) Verified Source Code (Mocked)
        2) Deployer History (Mocked)
        3) Interaction Volume (Mocked)
        Returns a Suspicion Score (0-100)
        """
        score = 0
        
        # 1. Source Code Verification
        # Unverified source is highly suspicious
        if "unverified" in address.lower() or random.random() < 0.2:
            score += 40
            
        # 2. Deployer History
        # New wallets or those with past rug pulls are suspicious
        if "fresh" in address.lower() or random.random() < 0.3:
            score += 35
            
        # 3. Interaction Volume
        # Low volume could be a sleeper contract
        if random.random() < 0.15:
            score += 25
            
        # Check Zero-Credit Brain Filters
        zero_credit_patterns = self.heuristics.get("zero_credit_filters", [])
        for pattern in zero_credit_patterns:
             if pattern in address.lower():
                 score += 50
                 
        return min(score, 100)
        
    def send_telegram_alert(self, message: str):
        import os, requests
        token = os.getenv("BOT_TOKEN")
        admin_id = os.getenv("ADMIN_TELEGRAM_ID")
        if not token or not admin_id:
            return
        
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": admin_id, "text": message, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload, timeout=5)
        except:
             pass

    def scan_contract(self, address: str) -> dict:
        """
        Orchestrates the scouting process.
        """
        
        # --- PRE-FLIGHT: Value Filter ---
        liquidity = self.check_liquidity(address)
        if liquidity <= 0:
            self.log(f"Skipping {address}: No initial value or verified source code.", "info")
            return {"status": "skipped", "reason": "No initial value/Verified source"}

        # --- 1. Stateless Triage (Pre-credit) ---
        suspicion_score = self.stateless_triage(address)
        self.log(f"Triage for {address}: Suspicion = {suspicion_score}%", "info")
        
        if suspicion_score > 65:
            alert = f"🚨 *Scout Triage Alert*\nAddress: `{address}`\nSuspicion: {suspicion_score}%"
            self.send_telegram_alert(alert)
            self.log(f"Alert Sent for {address} (Score: {suspicion_score}%)", "alert")
            
            # [NEW] Heartbeat Triggers
            try:
                from core import database
                import time
                import json
                
                database.increment_scout_leads()
                risk_data = {
                    "risk_summary": "Triage Alert (Stateless)",
                    "triage_score": suspicion_score,
                    "warnings": ["Matched Zero-Credit or High Suspicion Heuristics"]
                }
                database.save_audit_report(
                    report_id=f"triage_{int(time.time())}", 
                    report_hash="N/A", 
                    address=address, 
                    data=json.dumps(risk_data), 
                    vera_score=10, 
                    user_id="Scout_Auto"
                )
            except Exception as e:
                self.log(f"Failed to record triage lead: {e}", "warning")
            
        # --- 2. Live Scan Logic ---
        liquidity = self.check_liquidity(address)
        
        if liquidity < 5000:
            self.log(f"Skipping {address} (Low Liq: ${liquidity:.0f})", "skip")
            return {"status": "skipped", "reason": "low_liquidity"}

        if not self.manage_budget():
            self.log(f"Skipping {address} (Budget Depleted)", "warning")
            return {"status": "skipped", "reason": "budget_depleted"}

        # If we passed filters, we spend budget and trigger Red Team
        self.spend_budget()
        self.log(f"Found Potential Target: {address} ($ {liquidity:.0f})", "alert")
        return {"status": "triggered", "liquidity": liquidity}

# Singleton instance
scout = BaseScout()
