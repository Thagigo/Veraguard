from fastapi import FastAPI, HTTPException, Request, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import time
import hashlib
import json
import asyncio

# Core Modules
from core import database, payment_handler, payment_gate, auth, scout, brain_sync, red_team
# from .audit_logic import check_contract # Local import in endpoint to avoid circular issues if any

app = FastAPI(title="VeraGuard Audit Engine")

# --- Startup & Config ---

@app.on_event("startup")
async def startup_event():
    database.init_db()
    # Start Scheduler
    asyncio.create_task(scheduled_brain_flush())

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Scheduler ---
async def scheduled_brain_flush():
    while True:
        await asyncio.sleep(60) 
        try:
            brain_sync.brain.sync_to_drive()
        except Exception:
            pass

# --- Pydantic Models ---

class PaymentRequest(BaseModel):
    tx_hash: str
    user_id: str
    credits: int = 0
    is_subscription: bool = False
    referral_code: Optional[str] = None

class ReferralCreateRequest(BaseModel):
    user_id: str

class AuditRequest(BaseModel):
    address: str
    user_id: str
    confirm_deep_dive: bool = False
    bypass_deep_dive: bool = False

class ScanRequest(BaseModel):
    address: str

# --- Endpoints ---

@app.get("/")
async def root():
    return {"message": "VeraGuard Audit Engine is active."}

@app.get("/api/fee")
def get_fee():
    quote = payment_handler.calculate_dynamic_fee()
    return {"quote": quote, "note": "Quote valid for 60 seconds."}

@app.get("/api/credits/{user_id}")
def check_credits(user_id: str):
    creds = database.get_credits(user_id)
    sub_expiry = database.get_subscription_status(user_id)
    is_member = sub_expiry is not None and sub_expiry > time.time()
    return {"credits": creds, "is_member": is_member}

@app.post("/api/pay")
def process_payment(req: PaymentRequest, request: Request):
    # 1. Verify Payment (Mock or On-Chain)
    if not database.tx_exists(req.tx_hash):
        # Calculate USD Value
        amount_usd = 0.0
        amount_eth = 0.0
        
        # Get current price
        eth_price = payment_handler.get_eth_price()
        
        if req.is_subscription:
            amount_usd = 150.00
            amount_eth = amount_usd / eth_price
            database.activate_subscription(req.user_id)
            # Bonus Credits for Subscription
            database.db_add_credits(req.user_id, 50, req.tx_hash) # 50 Credits
        else:
            # Credit Bundle: $3.00 per credit
            amount_usd = req.credits * 3.00
            amount_eth = amount_usd / eth_price
            database.db_add_credits(req.user_id, req.credits, req.tx_hash)

        # Record Transaction
        database.record_tx(req.tx_hash, req.user_id, amount_eth, amount_usd)
        
        # [AUTONOMOUS BRAIN] Refill Scout Budget (10% of revenue)
        scout.scout.refill_budget(0.10) # Mock 10%

        # 2. Process Referral
        if req.referral_code:
            lifetime_spend = database.get_lifetime_spend(req.user_id)
            # First Purchase check (allowing variance for float precision or if this is the only tx)
            is_first_purchase = abs(lifetime_spend - amount_usd) < 0.1 

            if is_first_purchase:
                ref_data = database.validate_referral(req.referral_code)
                if ref_data:
                    # Sybil Check
                    client_ip = request.client.host
                    client_ua = request.headers.get('user-agent', '')
                    
                    ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()
                    ua_hash = hashlib.sha256(client_ua.encode()).hexdigest()
                    

                    if payment_handler.check_referral_security(ref_data, ip_hash, ua_hash):
                        # [NEW] Anti-Spam Velocity Check
                        # If the code is flagged (too many clicks/unique IPs with low conversion), we deny reward?
                        # Or checking if it's flagged happens at the `check_referral_security` level?
                        # Let's check the database flag explicitly or trust database.validate_referral
                        
                        # We re-verify the flag state
                        is_flagged = False
                        if len(ref_data) > 3: # Assuming we have the column, but validate_referral query might need update
                             # Let's just use check_referral_velocity logic or direct DB check
                             pass 

                        # Actually, let's rely on the velocity check that happens on the Live Link click.
                        # If a code is flagged, `is_flagged` in DB is 1.
                        # We should check that here.
                        
                        is_ref_valid = database.check_referral_velocity(req.referral_code, limit=999999) # Helper also checks flag
                        if is_ref_valid:
                            # Link and Reward Referrer (2 Credits)
                            referrer_id = ref_data[0]
                            database.processing_referral_reward(referrer_id, req.user_id, reward=2)
                        else:
                             print(f"Referral {req.referral_code} is flagged. No reward.")

    current_credits = database.get_credits(req.user_id)
    sub_status = database.get_subscription_status(req.user_id)
    is_member = sub_status is not None
    
    return {
        "status": "confirmed", 
        "credits": current_credits, 
        "is_member": is_member,
        "subscription_expiry": sub_status
    }

@app.post("/api/referral/create")
def create_referral(req: ReferralCreateRequest, request: Request):
    # 1. Eligibility Gate ($30 USD)
    spend = database.get_lifetime_spend(req.user_id)
    if spend < 30.0:
        raise HTTPException(status_code=403, detail=f"Eligibility Check Failed: Lifetime spend ${spend:.2f} < $30.00")
        
    # 2. Capture Fingerprint
    client_ip = request.client.host
    client_ua = request.headers.get('user-agent', '')
    
    ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()
    ua_hash = hashlib.sha256(client_ua.encode()).hexdigest()
    
    code = database.create_referral_code(req.user_id, ip_hash, ua_hash)
    
    return {"code": code}

@app.get("/api/referral/{user_id}")
def get_referral_stats(user_id: str):
    code = database.get_referral_code(user_id)
    if not code:
        return {"code": None, "uses": 0, "earned": 0}
        
    with database.get_db() as conn:
        c = conn.cursor()
        row = c.execute("SELECT uses, earned_credits FROM referrals WHERE owner_id=?", (user_id,)).fetchone()
        if row:
            return {"code": code, "uses": row[0], "earned": row[1]}
    
    return {"code": code, "uses": 0, "earned": 0}

@app.get("/api/audit/live/{report_id}")
def get_live_audit(report_id: str, ref: Optional[str] = None, request: Request = None):
    # 1. Fetch Report
    data_json = database.get_audit_report(report_id)
    if not data_json:
        raise HTTPException(status_code=404, detail="Audit Report not found.")
    
    report = json.loads(data_json)
    
    # 2. Handle Referral Logic (Transparent Live-Link)
    referral_msg = None
    if ref:
        # Velocity / Spam Check
        client_ip = request.client.host
        ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()
        
        # Log the click
        database.log_referral_click(ref, ip_hash)
        
        # Check Safety
        is_safe = database.check_referral_velocity(ref) # Checks DB flag & 100 limit
        
        if is_safe:
             referral_msg = f"Referral Active: Supporting {ref}"
        else:
             referral_msg = "Referral Deactivated (Spam Protection)"
    
    return {"report": report, "referral_msg": referral_msg}

@app.post("/api/audit")
def audit_contract(request: AuditRequest):
    from .audit_logic import check_contract, universal_ledger_check
    
    # 0. Check Vault Solvency
    is_solvent, balance = payment_handler.check_vault_balance()
    if not is_solvent:
        raise HTTPException(status_code=503, detail=f"Security Vault insolvent ({balance} ETH).")

    # 1. Universal Ledger Check
    complexity = universal_ledger_check(request.address)
    
    # Cost Logic
    sub_expiry = database.get_subscription_status(request.user_id)
    is_member = sub_expiry is not None and sub_expiry > time.time()
    
    if complexity == "Deep Dive":
        if request.bypass_deep_dive:
             cost = 1 # Force Standard Price
        else:
             # [MEMBER PERK] 33% Discount (3 -> 2 Credits)
             cost = 2 if is_member else 3
    else:
        cost = 1

    # Tier Gateway Logic
    if complexity == "Deep Dive" and not request.confirm_deep_dive and not request.bypass_deep_dive:
        return {
            "status": "requires_approval",
            "complexity": "Deep Dive",
            "cost": 3,
            "message": "Universal Ledger Alert: Contract > 24KB. Deep Dive recommended."
        }

    # 2. Credit / Rate Limit Check
    current_credits = database.get_credits(request.user_id)
    used_free_tier = False

    if current_credits < cost:
        # If standard cost (1) and user has no credits, check Free Tier
        if cost == 1 and database.check_rate_limit(request.user_id):
            used_free_tier = True
            database.log_scan_attempt(request.user_id)
        else:
             detail = "Daily Free Limit Reached (3/24h). Please buy credits." if cost == 1 else f"Insufficient credits for Deep Dive ({cost} required)."
             raise HTTPException(status_code=402, detail=detail)
    
    # 3. Deduct Credits
    if not used_free_tier:
        for _ in range(cost):
            database.use_credit(request.user_id)

    try:
        result_json = check_contract(request.address)
        result = json.loads(result_json)
        result['cost_deducted'] = 0 if used_free_tier else cost
        result['plan'] = "Free Tier" if used_free_tier else "Premium"
        
        # [NEW] Save Report with Score & Finder ID
        if 'report_id' in result:
             # Use the user_id from the request as the finder
             database.save_audit_report(result['report_id'], result['report_hash'], request.address, result_json, result.get('vera_score', 0), request.user_id)
        
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Admin / System ---

@app.get("/api/brain/status")
def get_brain_status(user_data: dict = Depends(auth.verify_telegram_auth)):
    auth.log_intrusion(user_data)
    
    # Count staged signatures
    staged_count = 0
    try:
        with open(brain_sync.brain.staging_file, "r") as f:
            content = f.read()
            staged_count = content.count("## [New Signature Candidate]")
    except FileNotFoundError:
        staged_count = 0

    return {
        "scout_budget": round(scout.scout.daily_budget, 2),
        "scout_spend": round(scout.scout.current_spend, 2),
        "staged_signatures": staged_count,
        "vault_solvency": "SOLVENT",
        "status": "OPERATIONAL",
        "admin_user": user_data.get("first_name", "Admin")
    }

@app.get("/api/scout/logs")
async def get_scout_logs():
    return list(scout.scout.logs)

@app.post("/api/admin/scan")
async def admin_trigger_scan(req: ScanRequest):
    result = scout.scout.scan_contract(req.address)
    
    if result['status'] == 'triggered':
        fingerprint = red_team.red_team.simulate_exploit(req.address, result['liquidity'])
        if fingerprint:
             brain_sync.brain.stage_signature(fingerprint)
             
    return {"status": "processed", "scout_result": result}

@app.post("/api/debug/reset")
def reset_user_credits(request: Request):
    """
    DEBUG: Resets the calling user's credits to 0.
    Requires 'user_id' in body.
    """
    # Quick parse since we don't have a pydantic model for this debug tool
    import asyncio
    async def parse_body():
        return await request.json()
    
    body = asyncio.run(parse_body())
    user_id = body.get("user_id")
    
    if not user_id:
        # Fallback for simple testing
        user_id = "user_test" 

    database.reset_credits(user_id)
    return {"status": "reset", "credits": 0}

# --- Sheriff's Frontier Endpoints ---

@app.get("/api/shame-wall")
def get_shame_wall():
    return database.get_wall_of_shame()

@app.get("/api/leaderboard")
def get_leaderboard_data():
    return database.get_leaderboard()

@app.post("/api/report-error")
async def report_error(request: Request):
    try:
        body = await request.json()
        # In prod: Log to Discord/Slack webhook or Admin DB
        print(f"[SHERIFF ALERT] User Reported Error: {body}")
        return {"status": "received"}
    except:
        return {"status": "error"}
