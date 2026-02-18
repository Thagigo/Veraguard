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
            self.heuristics = {"min_liquidity": 10000} # Public Fallback
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
            self.daily_budget = 0.50 # Reset to baseline
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

    def scan_contract(self, address: str) -> dict:
        """
        Orchestrates the scouting process.
        """
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
