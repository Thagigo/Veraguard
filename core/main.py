from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
from .audit_logic import check_contract

from core.database import init_db, get_credits, use_credit
from core.payment_gate import verify_payment, mock_verify_payment
from core.payment_handler import calculate_dynamic_fee, check_vault_balance

app = FastAPI(title="VeraGuard Audit Engine")

# Initialize DB on startup
@app.on_event("startup")
def startup_event():
    init_db()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AuditRequest(BaseModel):
    address: str
    user_id: str
    confirm_deep_dive: bool = False # User must opt-in for 3 credits

class PaymentRequest(BaseModel):
    tx_hash: str
    user_id: str
    credits: int = 1 # Default to 1, but supports 10, 50

@app.get("/api/fee")
async def get_fee():
    """Returns a Signed Quote with 60s expiry."""
    quote = calculate_dynamic_fee()
    return {"quote": quote, "note": "Quote valid for 60 seconds."}

@app.post("/api/pay")
async def process_payment(request: PaymentRequest):
    """
    Verifies a payment transaction and adds credits.
    """
    if request.credits not in [1, 10, 50]:
         raise HTTPException(status_code=400, detail="Invalid credit bundle.")

    # In production, we'd verify the AMOUNT match the bundle cost (credits * fee)
    success, message = mock_verify_payment(request.tx_hash, request.user_id, request.credits)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    new_balance = get_credits(request.user_id)
    return {"status": "success", "message": message, "credits": new_balance}

@app.get("/api/credits/{user_id}")
async def check_credits(user_id: str):
    return {"credits": get_credits(user_id)}

@app.post("/api/audit")
async def audit_contract(request: AuditRequest):
    """
    Analyzes a smart contract.
    Checks Complexity -> Enforces Tiered Pricing & Rate Limits.
    """
    from .audit_logic import universal_ledger_check
    from core.database import check_rate_limit, log_scan_attempt

    # 0. Check Vault Solvency
    is_solvent, balance = check_vault_balance()
    if not is_solvent:
        raise HTTPException(status_code=503, detail=f"Security Vault insolvent ({balance} ETH).")

    # 1. Universal Ledger Check (Stealth Triage)
    complexity = universal_ledger_check(request.address)
    cost = 3 if complexity == "Deep Dive" else 1

    if complexity == "Deep Dive" and not request.confirm_deep_dive:
        return {
            "status": "requires_approval",
            "complexity": "Deep Dive",
            "cost": 3,
            "message": "Universal Ledger Alert: Contract > 24KB. Deep Dive required."
        }

    # 2. Credit / Rate Limit Check
    current_credits = get_credits(request.user_id)
    used_free_tier = False

    if current_credits < cost:
        # If standard cost (1) and user has no credits, check Free Tier
        if cost == 1 and check_rate_limit(request.user_id):
            used_free_tier = True
            log_scan_attempt(request.user_id)
        else:
             detail = "Daily Free Limit Reached (3/24h). Please buy credits." if cost == 1 else f"Insufficient credits for Deep Dive ({cost} required)."
             raise HTTPException(status_code=402, detail=detail)
    
    # 3. Deduct Credits (if not free tier)
    if not used_free_tier:
        for _ in range(cost):
            use_credit(request.user_id)

    try:
        # Call the audit logic
        result_json = check_contract(request.address)
        result = json.loads(result_json)
        result['cost_deducted'] = 0 if used_free_tier else cost
        result['plan'] = "Free Tier" if used_free_tier else "Premium"
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "VeraGuard Audit Engine is active."}
