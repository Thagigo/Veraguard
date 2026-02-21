import time
try:
    from . import database
except ImportError:
    import database

# --- RANKING LOGIC ---

def update_sheriff_ranking(user_id: str, is_correct: bool, yield_amount: float = 0.0):
    """
    Updates a Sheriff's stats after an audit verification.
    """
    with database.get_db() as conn:
        c = conn.cursor()
        
        # Check if user exists in rankings
        c.execute("SELECT total_verifications, correct_verifications, accumulated_yield FROM sheriff_rankings WHERE user_id=?", (user_id,))
        row = c.fetchone()
        
        if row:
            total, correct, acc_yield = row
            new_total = total + 1
            new_correct = correct + (1 if is_correct else 0)
            new_yield = acc_yield + yield_amount
            
            c.execute("""
                UPDATE sheriff_rankings 
                SET total_verifications=?, correct_verifications=?, accumulated_yield=?, last_active=?
                WHERE user_id=?
            """, (new_total, new_correct, new_yield, time.time(), user_id))
        else:
            # Create new entry
            c.execute("""
                INSERT INTO sheriff_rankings (user_id, total_verifications, correct_verifications, accumulated_yield, last_active)
                VALUES (?, 1, ?, ?, ?)
            """, (user_id, 1 if is_correct else 0, yield_amount, time.time()))
            
        conn.commit()

def get_top_sheriffs(limit: int = 10):
    """
    Returns top Sheriffs sorted by Veracity Rate (DESC), then Yield (DESC).
    Includes 'multiplier_active' flag for Top 5%.
    """
    with database.get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT user_id, total_verifications, correct_verifications, accumulated_yield FROM sheriff_rankings")
        rows = c.fetchall()
        
        all_sheriffs = []
        for r in rows:
            uid, total, correct, acc_yield = r
            if total == 0: continue
            rate = (correct / total) * 100
            all_sheriffs.append({
                "user_id": uid,
                "total": total,
                "correct": correct,
                "veracity_rate": rate,
                "yield": acc_yield,
                "multiplier_active": False # Default
            })
            
        # Sort Logic: Veracity (DESC), Yield (DESC)
        all_sheriffs.sort(key=lambda x: (x['veracity_rate'], x['yield']), reverse=True)
        
        # Calculate Multiplier Eligibility (Top 5% of those with >= 5 verifications)
        qualified = [s for s in all_sheriffs if s['total'] >= 5]
        if qualified:
            cutoff_count = max(1, int(len(qualified) * 0.05))
            top_tier_ids = {s['user_id'] for s in qualified[:cutoff_count]}
            
            for s in all_sheriffs:
                if s['user_id'] in top_tier_ids:
                    s['multiplier_active'] = True
        
        return all_sheriffs[:limit]

def check_multiplier_eligibility(user_id: str) -> bool:
    """
    Returns True if user is in the Top 5% of Sheriffs (by Veracity).
    Minimum 5 verifications required to qualify.
    """
    rankings = get_top_sheriffs(limit=1000) # Get all for calculation
    
    # Filter for active/qualified
    qualified = [r for r in rankings if r['total'] >= 5]
    
    if not qualified:
        return False
        
    cutoff_index = int(len(qualified) * 0.05)
    # Ensure at least top 1 gets it if list is small
    cutoff_index = max(1, cutoff_index) 
    
    top_tier = qualified[:cutoff_index]
    
    return any(r['user_id'] == user_id for r in top_tier)

# --- BOUNTY FEED LOGIC ---

def get_recent_bounties(limit: int = 10):
    """
    Returns recent 'Busts' (Found Vulnerabilities) from audit_reports.
    Simulates a Bounty Feed.
    """
    with database.get_db() as conn:
        c = conn.cursor()
        # Find critical vulnerabilities (Score < 50)
        c.execute("""
            SELECT finder_id, address, vera_score, timestamp 
            FROM audit_reports 
            WHERE vera_score < 50 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))
        
        rows = c.fetchall()
        
        bounties = []
        for r in rows:
            uid, addr, score, ts = r
            # Mock Bounty Amount based on score Inverse 
            # (Lower score = Higher bounty)
            # e.g. Score 40 -> 0.5 ETH, Score 10 -> 5 ETH
            payout = (50 - score) * 0.1 
            
            is_triage = (uid == "Scout_Auto")
            
            bounties.append({
                "scout_alias": uid[:6] + "..." if uid and not is_triage else uid,
                "target": addr,
                "score": score,
                "payout_eth": round(payout, 3),
                "timestamp": ts,
                "type": "TRIAGE_ALERT" if is_triage else "BOUNTY_CLAIM"
            })
            
        return bounties
