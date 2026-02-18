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
    user_id: str  # Required for credit check

class PaymentRequest(BaseModel):
    tx_hash: str
    user_id: str

@app.get("/api/fee")
async def get_fee():
    """Returns the current Dynamic Fee in ETH."""
    fee = calculate_dynamic_fee()
    return {"fee": fee, "currency": "ETH", "note": "Covers AI Reasoning & Security Vault contribution"}

@app.post("/api/pay")
async def process_payment(request: PaymentRequest):
    """
    Verifies a payment transaction and adds a credit.
    """
    # Using mock verification for development/demo ease
    # In production, swap with verify_payment(request.tx_hash, request.user_id)
    success, message = mock_verify_payment(request.tx_hash, request.user_id)
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
    Analyzes a smart contract address using the Audit Engine.
    Requires 1 credit.
    """
    # 0. Check Vault Solvency (Optimized Finance Core)
    is_solvent, balance = check_vault_balance()
    if not is_solvent:
        raise HTTPException(
            status_code=503,
            detail=f"Security Vault insolvent ({balance} ETH). Cannot guarantee audit safety."
        )

    # 1. Deduct Credit
    if not use_credit(request.user_id):
        raise HTTPException(
            status_code=402, 
            detail="Insufficient credits. Please pay the Dynamic Fee to continue."
        )

    try:
        # Call the audit logic
        result_json = check_contract(request.address)
        result = json.loads(result_json)
        
        if "error" in result:
             pass

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "VeraGuard Audit Engine is active."}
