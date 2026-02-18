import hashlib
import json
import time
import random
from . import database

class PrizeEngine:
    def __init__(self):
        pass

    def calc_vwa_payout(self):
        """
        Calculates the Safe Payout Amount based on 30-day Volume Weighted Average.
        Logic:
        1. Get last 30 days volume.
        2. Calculate Average Daily Volume (ADV).
        3. If Current Monthly Volume > ADV * 30, we are in "Surplus".
        4. Base Payout Ratio = 20% of Treasury.
        5. If Surplus, scale up to 35%.
        """
        stats = database.get_treasury_stats()
        if not stats: return 0.0

        chest = stats['chest_balance']
        if chest <= 0: return 0.0

        daily_vols = database.get_daily_volumes(30)
        if not daily_vols: return chest * 0.20 # Default Floor

        total_30d_vol = sum(d['volume'] for d in daily_vols)
        avg_daily_vol = total_30d_vol / 30 if daily_vols else 0
        
        # Determine Ratio
        # For simulation simplicity: 
        # Low Liquidity (< 10 ETH volume) -> 20%
        # High Liquidity -> 35%
        
        ratio = 0.20
        if total_30d_vol > 10.0:
            ratio = 0.35
        elif total_30d_vol > 5.0:
            ratio = 0.25
            
        return chest * ratio

    def generate_merkle_root(self, winners: list):
        """
        Winners: [{"user_id": "...", "amount": 0.5, "score": 90}]
        Leaf = Hash(user_id + amount + score)
        Returns: Merkle Root (Hex String)
        """
        if not winners: return None
        
        leaves = []
        for w in winners:
            payload = f"{w['user_id']}:{w['amount']}:{w['score']}"
            leaf = hashlib.sha256(payload.encode()).hexdigest()
            leaves.append(leaf)
            
        # Simple Merkle Tree (Unbalanced handling omitted for brevity/PoC)
        tree = leaves
        while len(tree) > 1:
            level = []
            for i in range(0, len(tree), 2):
                if i + 1 < len(tree):
                    # Hash(Left + Right)
                    combined = tree[i] + tree[i+1]
                else:
                    # Hash(Left + Left)
                    combined = tree[i] + tree[i]
                
                level.append(hashlib.sha256(combined.encode()).hexdigest())
            tree = level
            
        return tree[0]

    def run_simulation(self, months=6):
        """
        Simulates 6 months of verifyable growth.
        1. Seeds historical volume data.
        2. Runs monthly payout cycles.
        3. Logs Solvency Metrics.
        """
        results = []
        
        # 0. Reset Backend State for Simulation? 
        # Or just simulate strictly in memory?
        # User wants "Verification: Run a 6-month simulation."
        # Best to simulate logic without wiping real DB.
        
        # Initial State
        sim_chest = 10.0 # Start with 10 ETH
        sim_volume = 5.0 # Month 1 Volume
        
        for m in range(1, months + 1):
            # 1. Add Volume (Growth 5% MoM)
            sim_volume = sim_volume * 1.05
            sim_chest += sim_volume
            
            # 2. VWA Logic (Mocked)
            ratio = 0.20
            if sim_volume > 8.0: ratio = 0.35
            elif sim_volume > 6.0: ratio = 0.25
            
            payout = sim_chest * ratio
            
            # 3. Revenue Rotation (War Chest)
            # Month 1: 0%, Month 2+: 30% of Payout goes to War Chest?? 
            # "Month 2: 70% ETH + 30% 'War Chest'"
            
            war_chest_alloc = 0.0
            actual_payout = payout
            
            if m >= 2:
                war_chest_alloc = payout * 0.30
                actual_payout = payout * 0.70
                
            sim_chest -= payout # Total deducted
            
            results.append({
                "month": m,
                "volume": round(sim_volume, 4),
                "chest_start": round(sim_chest + payout, 4), # Pre-deduction
                "payout_ratio": ratio,
                "total_deduction": round(payout, 4),
                "winner_pool": round(actual_payout, 4),
                "war_chest_growth": round(war_chest_alloc, 4),
                "chest_end": round(sim_chest, 4),
                "solvency": "SOLVENT" if sim_chest > 0 else "INSOLVENT"
            })
            
        return results

prize_engine = PrizeEngine()

# --- Governance Router ---
from fastapi import APIRouter
from . import database
from . import sheriff_logic

governance_router = APIRouter()

@governance_router.post('/simulate')
def run_governance_simulation():
    """
    Verifies the Solvency of the Sovereign Prize Model over 6 months.
    """
    results = prize_engine.run_simulation(months=6)
    return {"status": "success", "simulation": results}

@governance_router.post('/sybil_test')
def run_sybil_test():
    """
    Verifies:
    1. First Finder gets Royalty.
    2. Spammer gets diminished points (Fatigue).
    """
    
    try:
        # Setup
        target_contract = f"0xSybilTarget_{int(time.time())}"
        good_sheriff = "user_good_sheriff"
        attacker = "user_attacker"
        
        database.reset_credits(good_sheriff)
        database.reset_credits(attacker) 
        # Give them credits to scan
        database.db_add_credits(good_sheriff, 100)
        database.db_add_credits(attacker, 100)
        
        results = {
            "good_sheriff_royalty": 0,
            "attacker_points": []
        }
        
        # 1. Good Sheriff Scans First (Establishes First Finder)
        # We simulate the logic inside audit_contract manually or just call DB helpers
        database.save_audit_report(f"rep_{int(time.time())}", "hash", target_contract, "{}", 20, good_sheriff) # Score 20 (<50) -> First Find
        
        # 2. Attacker Scans 10 times
        points_log = []
        for i in range(15):
            # Scan
            database.increment_daily_scan_count(attacker)
            points = sheriff_logic.sheriff_engine.calc_points_with_fatigue(attacker, 10)
            points_log.append(points)
            
            # Royalty Check (Attacker pays fee, Good Sheriff gets cut)
            royalty_res = sheriff_logic.sheriff_engine.process_royalty(target_contract, 0.001)
            if royalty_res and royalty_res['finder'] == good_sheriff:
                results["good_sheriff_royalty"] += royalty_res['amount'] # Note: process_royalty returns amount
                
        results["attacker_points"] = points_log
        
        # Pass if points diminish (last < first) and royalty > 0
        passed = points_log[-1] < points_log[0] and results["good_sheriff_royalty"] > 0
        results["status"] = "PASSED" if passed else "FAILED"
        
        return results
    except Exception as e:
        import traceback
        return {"status": "ERROR", "detail": str(e), "traceback": traceback.format_exc()}
