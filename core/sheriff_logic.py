import time
from . import database

class SheriffEngine:
    def __init__(self):
        pass

    def get_user_rank(self, user_id: str):
        # Mock Rank Logic based on history length or credits
        # Legendary: > 1000 Credits
        # Elite: > 100 Credits
        credits = database.get_credits(user_id)
        if credits > 1000: return "LEGENDARY"
        if credits > 100: return "ELITE"
        return "PUBLIC"

    def calc_points_with_fatigue(self, user_id: str, base_points: int):
        """
        Applies Fatigue Factor:
        1-10 scans: 100%
        11-20 scans: 40%
        21+ scans: 5%
        """
        daily_count = database.get_daily_scan_count(user_id)
        
        multiplier = 1.0
        if daily_count >= 20:
            multiplier = 0.05
        elif daily_count >= 10:
            multiplier = 0.40
            
        return int(base_points * multiplier)

    def process_royalty(self, contract_address: str, audit_fee_eth: float):
        """
        Finds the First-Finder and awards 2% of the audit fee.
        """
        first_finder = database.get_first_finder(contract_address)
        if not first_finder:
            return None # No one to pay
            
        royalty_amount = audit_fee_eth * 0.02
        if royalty_amount > 0:
            # Record it (This function updates DB and gives credits/eth)
            # Assuming we convert Royalty ETH to Credits for simplicity in this prototype
            # Or just track it.
            database.record_royalty_claim(contract_address, first_finder, royalty_amount)
            return {"finder": first_finder, "amount": royalty_amount}
            
        return None

    def check_conflict(self, user_id: str, contract_address: str):
        """
        Collision Detection.
        In production, this would query an Archive Node or Indexer (Etherscan API)
        to see if `user_address` has interacted with `contract_address`.
        
        For now, we return False (No conflict).
        """
        return False

    def get_visible_leads(self, user_id: str):
        """
        Asymmetric Alerting / LeadTime.
        Returns list of suspicious contracts.
        
        Rank Delays:
        - Legendary: 0m delay (Real-time)
        - Elite: 5m delay
        - Public: 10m delay
        """
        rank = self.get_user_rank(user_id)
        delay_seconds = 600 # Public: 10m
        if rank == "LEGENDARY": delay_seconds = 0
        elif rank == "ELITE": delay_seconds = 300
        
        # Mock Leads Data
        # In prod, this comes from the "Scout" module scanning mempool
        base_leads = [
            {"address": "0xScam...1", "risk": "High", "timestamp": time.time() - 120}, # 2 mins ago
            {"address": "0xSus...2", "risk": "Medium", "timestamp": time.time() - 400}, # 6 mins ago
            {"address": "0xSafe...3", "risk": "Low", "timestamp": time.time() - 1000} # 16 mins ago
        ]
        
        visible = []
        now = time.time()
        for lead in base_leads:
            # If (Lead Time + Delay) < Now, it is visible.
            if lead["timestamp"] + delay_seconds < now:
                lead["status"] = "VISIBLE"
                visible.append(lead)
            else:
                # Optionally return it as "LOCKED"?
                pass
                
        return {"rank": rank, "delay": delay_seconds, "leads": visible}

sheriff_engine = SheriffEngine()
