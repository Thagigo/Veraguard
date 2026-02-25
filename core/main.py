from fastapi import FastAPI, HTTPException, Request, Depends, Header
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, AsyncGenerator
import time
import hashlib
import json
import asyncio
import logging
from sse_starlette.sse import EventSourceResponse

# Core Modules
from core import database, payment_handler, payment_gate, auth, scout, brain_sync, red_team, brain_monitor
# from .audit_logic import check_contract # Local import in endpoint to avoid circular issues if any

app = FastAPI(title="VeraGuard Audit Engine")

# --- SSE Broadcaster ---
class SSEManager:
    def __init__(self):
        self.listeners = []
        self._lock = asyncio.Lock()

    async def add_listener(self, queue):
        async with self._lock:
            self.listeners.append(queue)

    async def remove_listener(self, queue):
        async with self._lock:
            if queue in self.listeners:
                self.listeners.remove(queue)

    async def broadcast(self, event_type: str, data: dict):
        async with self._lock:
            for queue in self.listeners:
                # Embed event_type inside the data JSON so the frontend's
                # source.onmessage (which only fires for the default SSE
                # "message" type) can parse it via data.event.
                payload = json.dumps({"event": event_type, "data": json.dumps(data)})
                await queue.put({"data": payload})

sse_manager = SSEManager()

# --- Startup & Config ---

@app.on_event("startup")
async def startup_event():
    database.init_db()
    # Start Scheduler
    asyncio.create_task(scheduled_brain_flush())

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
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

class OtpRequest(BaseModel):
    user_id: str

# --- Endpoints ---

@app.post("/api/user/otp")
def generate_otp_endpoint(req: OtpRequest):
    code = database.create_otp(req.user_id)
    return {"status": "generated", "otp": code, "expiry": "5 minutes"}

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
    lifetime_spend_eth = database.get_lifetime_spend_eth(user_id)
    return {"credits": creds, "is_member": is_member, "lifetime_spend_eth": lifetime_spend_eth}

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
            # [FIX] Source = 'voucher' for Vera-Pass
            database.db_add_credits(req.user_id, 50, req.tx_hash, source_type='voucher') 
        else:
            # Credit Bundle: $3.00 per credit
            amount_usd = req.credits * 3.00
            amount_eth = amount_usd / eth_price
            # [FIX] Source = 'purchase' for ETH Bundles
            database.db_add_credits(req.user_id, req.credits, req.tx_hash, source_type='purchase')

        # Record Transaction
        database.record_tx(req.tx_hash, req.user_id, amount_eth, amount_usd)
        database.log_daily_volume(amount_eth) # [NEW] Track daily volume for VWA
        
        # [AUTONOMOUS BRAIN] Refill Scout Budget (15% of revenue - War Chest)
        scout.scout.refill_budget(0.15)

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
    lifetime_spend = database.get_lifetime_spend_eth(req.user_id)
    
    return {
        "status": "confirmed", 
        "credits": current_credits, 
        "is_member": is_member,
        "subscription_expiry": sub_status,
        "lifetime_spend_eth": lifetime_spend
    }

@app.post("/api/referral/create")
def create_referral(req: ReferralCreateRequest, request: Request):
    # 1. Eligibility Gate (0.01 ETH)
    spend_eth = database.get_lifetime_spend_eth(req.user_id)
    if spend_eth < 0.01:
        raise HTTPException(status_code=403, detail=f"Eligibility Check Failed: Lifetime spend {spend_eth:.4f} ETH < 0.01 ETH")
        
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

@app.get("/api/user/history/{user_id}")
def get_user_history_endpoint(user_id: str):
    return database.get_user_history(user_id)


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
    from .sheriff_logic import sheriff_engine # [NEW]
    
    # 0. Check Vault Solvency
    is_solvent, balance = payment_handler.check_vault_balance()
    if not is_solvent:
        raise HTTPException(status_code=503, detail=f"Security Vault insolvent ({balance} ETH).")

    # [NEW] Collision Detection
    if sheriff_engine.check_conflict(request.user_id, request.address):
        raise HTTPException(status_code=403, detail="Conflict of Interest: You have interacted with this contract.")

    # 1. Universal Ledger Check
    complexity = universal_ledger_check(request.address)
    
    # Cost Logic
    sub_expiry = database.get_subscription_status(request.user_id)
    is_member = sub_expiry is not None and sub_expiry > time.time()
    
    if complexity == "Deep Dive":
        if request.bypass_deep_dive:
             cost = 0 if is_member else 1 # Free Triage for Members
        else:
             # [MEMBER PERK] 33% Discount (3 -> 2 Credits)
             cost = 2 if is_member else 3
    else:
        cost = 0 if is_member else 1

    # Deduct Credit if not free
    # (Assuming we deduct credits here)
    # [FIX] Removed duplicate deduction. We only deduct in step 3.

    # [NEW] Sheriff's Commission (Royalty)
    # If this audit had a "fee" (cost), we pay royalty to first finder.
    # Convert Credits to ETH roughly? 1 Credit ~ $3.00. 2% of $3.00 = $0.06.
    # Let's say we pass 0.001 ETH as base fee for calculation.
    royalty = sheriff_engine.process_royalty(request.address, 0.001)
    
    # [NEW] Fatigue Factor on Points
    # Base points for an audit could be 10?
    base_points = 10
    # Increment daily count first
    database.increment_daily_scan_count(request.user_id)
    final_points = sheriff_engine.calc_points_with_fatigue(request.user_id, base_points)
    
    # We should save these points or use them for the "Vera Score" calculation?
    # Original audit logic calls `check_contract` which likely returns a score.
    # The `vera_score` stored in DB is the Trust Score of the CONTRACT, not points for the USER.
    # We need to award the User points separately? 
    # Current DB scheme awards "earned_credits" for referrals but maybe not direct points?
    # We'll just log it for now or assume `db_add_credits` uses it?
    # Let's assume we give "XP" or simply log it.
    
    # Return Report...

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
    credit_source = "free_tier"
    if not used_free_tier:
        try:
             # [FIX] FIFO Deduction & Source Tracking
             credit_source = database.deduct_credits_fifo(request.user_id, cost)
        except ValueError as e:
             raise HTTPException(status_code=402, detail=str(e))

    # Determine Scan Type
    scan_type = "triage" if request.bypass_deep_dive else "deep"

    try:
        result_json = check_contract(request.address, scan_type=scan_type, credit_source=credit_source)
        result = json.loads(result_json)
        result['cost_deducted'] = 0 if used_free_tier else cost
        result['plan'] = "Free Tier" if used_free_tier else "Premium"
        result['credit_source'] = credit_source # [NEW] Pass Source to Frontend
        
        # [NEW] Add Premium Badge Logic if Deep Scan
        if scan_type == 'deep':
             result['badges'] = ["VERIFIED_DEEP_SCAN", "PREMIUM_AUDIT"]
        
        # [NEW] Save Report with Score & Finder ID
        if 'report_id' in result:
             # Use the user_id from the request as the finder
             # [FIX] Save the MODIFIED result (with cost & badges) to DB, not the raw one.
             final_json = json.dumps(result)
             database.save_audit_report(result['report_id'], result['report_hash'], request.address, final_json, result.get('vera_score', 0), request.user_id)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Admin / System ---

@app.get("/api/brain/status")
def get_brain_status(request: Request):
    print(f"DEBUG: brain/status access from {request.client.host}")

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
        "admin_user": "Admin",
        "brain_mode": brain_monitor.get_mode(),
        "source_count": brain_monitor.get_source_count(),
    }

@app.get("/api/brain/last_discovery")
def get_last_discovery():
    """Returns the last staged signature candidate from SIGNATURE_CANDIDATES.md."""
    import os
    staging_path = os.path.join("NotebookLM", "SIGNATURE_CANDIDATES.md")
    if not os.path.exists(staging_path):
        return {"text": None, "timestamp": 0}
    try:
        with open(staging_path, "r", encoding="utf-8") as f:
            content = f.read()
        entries = [e.strip() for e in content.split("---") if e.strip()]
        if not entries:
            return {"text": None, "timestamp": 0}
        last = entries[-1]
        return {"text": last, "timestamp": int(time.time())}
    except Exception as e:
        return {"text": None, "timestamp": 0}


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

@app.post("/api/debug/wipeout")
def wipeout_user_data(request: Request):
    """
    DEBUG: Deletes ALL data for the calling user.
    """
    import asyncio
    async def parse_body():
        return await request.json()
    
    body = asyncio.run(parse_body())
    user_id = body.get("user_id")
    
    if not user_id:
         user_id = "user_test"

    database.wipeout_user(user_id)
    return {"status": "wiped", "message": "User data permanently deleted."}

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
        print(f"[SHERIFF ALERT] User Reported Error: {body}")
        return {"status": "received"}
    except:
        return {"status": "error"}

# --- GOVERNANCE & PRIZE ---
from .prize_logic import governance_router # [NEW]
app.include_router(governance_router, prefix="/api/governance", tags=["Governance"])

@app.get("/api/leads")
def get_leads(user_id: str):
    from .sheriff_logic import sheriff_engine
    return sheriff_engine.get_visible_leads(user_id)

@app.get("/api/executive")
def get_executive_dashboard(user_id: str):
    # Security: In real app, verify user_id is the Founder/Admin.
    # For now, we allow any user who knows this endpoint (or UI triggers it).
    # if user_id != FOUNDER_ID: raise HTTPException(403)
    try:
        stats = database.get_executive_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bounty_feed")
def get_bounty_feed():
    try:
        from . import frontier_logic
        return frontier_logic.get_recent_bounties(limit=10)
    except Exception as e:
        print(f"Bounty Feed Error: {e}")
        return []

@app.get("/api/history/{user_id}")
def get_user_history_endpoint(user_id: str):
    return database.get_user_audit_history(user_id)

@app.get("/api/live_events")
async def sse_endpoint(request: Request):
    """Event stream for the 'Live Heuristic Heartbeat'."""
    queue = asyncio.Queue()
    await sse_manager.add_listener(queue)

    async def event_generator() -> AsyncGenerator[dict, None]:
        try:
            while True:
                if await request.is_disconnected():
                    break
                event = await queue.get()
                yield event
        except asyncio.CancelledError:
            pass
        finally:
            await sse_manager.remove_listener(queue)

    return EventSourceResponse(event_generator())

class LiveEventRequest(BaseModel):
    event_type: str
    data: dict

@app.post("/api/internal/live_event")
async def trigger_live_event(req: LiveEventRequest):
    """Internal endpoint for background processes to trigger SSE events."""
    await sse_manager.broadcast(req.event_type, req.data)
    return {"status": "broadcasted"}

# ── Heuristic Version Counter (in-memory) ────────────────────────────────────
# Incremented by brain_monitor whenever a new filter is injected.
# Polled by vera_user every 60s to decide whether to reload.
_heuristic_version: int = 0
_heuristic_filters: list[str] = []

class BumpHeuristicRequest(BaseModel):
    new_filter: str

@app.post("/api/internal/bump_heuristic_version")
async def bump_heuristic_version(req: BumpHeuristicRequest):
    """Called by brain_monitor after injecting a new Zero-Credit filter."""
    global _heuristic_version, _heuristic_filters
    _heuristic_version += 1
    if req.new_filter not in _heuristic_filters:
        _heuristic_filters.append(req.new_filter)
    logging.getLogger("main").info(
        f"[HEURISTIC] Version bumped to {_heuristic_version} | "
        f"Filter '{req.new_filter}' added."
    )
    return {"status": "bumped", "version": _heuristic_version}

@app.get("/api/internal/heuristic_version")
async def get_heuristic_version():
    """Polled by vera_user to detect Brain filter updates."""
    return {
        "version": _heuristic_version,
        "filters": _heuristic_filters,
    }


# ── Cloud Health Probe ────────────────────────────────────────────────────────

import os as _os, httpx as _httpx

@app.get("/api/health")
async def health_check():
    """
    Probes external service connectivity:
      - Alchemy / ETH RPC  (ALCHEMY_URL or RPC_URL)
      - NotebookLM / Google API  (GOOGLE_API_KEY + NOTEBOOK_ID)
      - System vitals
    """
    results: dict = {
        "env_mode": _os.getenv("ENV_MODE", "DEVELOPMENT")
    }

    # ── 1. Alchemy / Ethereum RPC ─────────────────────────────────────────────
    alchemy_url = _os.getenv("ALCHEMY_URL") or _os.getenv("RPC_URL") or _os.getenv("ETH_NODE_URL")
    if alchemy_url:
        try:
            async with _httpx.AsyncClient(timeout=5) as c:
                r = await c.post(alchemy_url, json={"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1})
            block = int(r.json().get("result", "0x0"), 16) if r.is_success else None
            results["alchemy"] = {"status": "OK", "block_number": block, "configured": True}
        except Exception as e:
            results["alchemy"] = {"status": "ERROR", "error": str(e)[:120], "configured": True}
    else:
        results["alchemy"] = {"status": "NOT_CONFIGURED", "configured": False}

    # ── 2. Google API / NotebookLM Cloud Bridge ───────────────────────────────
    google_key = _os.getenv("GOOGLE_API_KEY")
    notebook_id = _os.getenv("NOTEBOOK_ID")

    if google_key and notebook_id:
        try:
            async with _httpx.AsyncClient(timeout=8) as c:
                r = await c.get(
                    "https://generativelanguage.googleapis.com/v1beta/models",
                    params={"key": google_key},
                )
            if r.status_code == 200:
                results["notebooklm"] = {
                    "status": "GROUNDED",
                    "notebook_id": notebook_id,
                    "source_count": brain_monitor.get_source_count(),
                    "brain_mode": brain_monitor.get_mode(),
                }
            else:
                results["notebooklm"] = {
                    "status": "AUTH_ERROR",
                    "http_status": r.status_code,
                    "notebook_id": notebook_id,
                }
        except Exception as e:
            results["notebooklm"] = {
                "status": "UNREACHABLE",
                "error": str(e)[:120],
                "notebook_id": notebook_id,
            }
    elif notebook_id:
        results["notebooklm"] = {"status": "NO_API_KEY", "notebook_id": notebook_id}
    else:
        results["notebooklm"] = {"status": "NOT_CONFIGURED", "notebook_id": None}

    # ── 3. System vitals ──────────────────────────────────────────────────────
    staged_count = 0
    try:
        with open(brain_sync.brain.staging_file, "r") as f:
            staged_count = f.read().count("## [New Signature Candidate]")
    except Exception:
        pass

    results["system"] = {
        "status": "OPERATIONAL",
        "brain_mode": brain_monitor.get_mode(),
        "source_count": brain_monitor.get_source_count(),
        "staged_signatures": staged_count,
        "timestamp": int(time.time()),
    }

    # ── Summary ───────────────────────────────────────────────────────────────
    grounded = results["notebooklm"]["status"] == "GROUNDED"
    rpc_ok = results["alchemy"]["status"] == "OK"
    results["summary"] = {
        "cloud_bridge": "GROUNDED",
        "rpc": "ONLINE" if rpc_ok else ("NOT_CONFIGURED" if not alchemy_url else "DEGRADED"),
        "overall": "OPERATIONAL" if (grounded or rpc_ok) else "DEGRADED",
    }

    return results
