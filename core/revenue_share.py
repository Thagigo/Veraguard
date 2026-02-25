import uuid
import time
from typing import Optional, Dict
from core.database import get_db

def generate_bounty_link(report_id: str, original_auditor_id: str) -> str:
    """
    Generates a unique bounty claim link for a specific report and auditor.
    In a real app, this would be a URL like: https://veraguard.ai/claim/<bounty_id>
    For now, we generate a unique bounty_id and store it.
    """
    bounty_id = f"bty_{uuid.uuid4().hex[:8]}"
    
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS bounty_links (
                bounty_id TEXT PRIMARY KEY,
                report_id TEXT,
                auditor_id TEXT,
                created_at REAL,
                claims INTEGER DEFAULT 0
            )
        """)
        c.execute("INSERT INTO bounty_links (bounty_id, report_id, auditor_id, created_at) VALUES (?, ?, ?, ?)",
                  (bounty_id, report_id, original_auditor_id, time.time()))
        conn.commit()
        
    return bounty_id

def process_bounty_claim(bounty_id: str, claimer_id: str) -> Dict[str, any]:
    """
    Processes a claim. If valid, awards 10% kickback (1 credit) to the original auditor.
    """
    with get_db() as conn:
        c = conn.cursor()
        
        # 1. Verify Bounty Link
        c.execute("SELECT report_id, auditor_id FROM bounty_links WHERE bounty_id = ?", (bounty_id,))
        bounty = c.fetchone()
        if not bounty:
            return {"success": False, "error": "Invalid or expired bounty link."}
            
        report_id, auditor_id = bounty
        
        # Prevent self-claiming
        if auditor_id == claimer_id:
            return {"success": False, "error": "Cannot claim your own bounty."}
            
        # 2. Check if already claimed by this user
        c.execute("""
            CREATE TABLE IF NOT EXISTS bounty_claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bounty_id TEXT,
                claimer_id TEXT,
                timestamp REAL
            )
        """)
        
        c.execute("SELECT id FROM bounty_claims WHERE bounty_id = ? AND claimer_id = ?", (bounty_id, claimer_id))
        if c.fetchone():
            return {"success": False, "error": "Bounty already claimed by this user."}
            
        # 3. Process Reward (1 Credit as 10% kickback of standard 10 credit bundle)
        reward_credits = 1
        
        c.execute("UPDATE users SET credits = credits + ? WHERE user_id = ?", (reward_credits, auditor_id))
        c.execute("INSERT INTO bounty_claims (bounty_id, claimer_id, timestamp) VALUES (?, ?, ?)", 
                  (bounty_id, claimer_id, time.time()))
        c.execute("UPDATE bounty_links SET claims = claims + 1 WHERE bounty_id = ?", (bounty_id,))
                  
        conn.commit()
        
        return {
            "success": True, 
            "message": f"Bounty claimed! 10% kickback ({reward_credits} CRD) awarded to the original auditor."
        }
