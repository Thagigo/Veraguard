from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
from .audit_logic import check_contract

app = FastAPI(title="VeraGuard Audit Engine")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AuditRequest(BaseModel):
    address: str

@app.post("/api/audit")
async def audit_contract(request: AuditRequest):
    """
    Analyzes a smart contract address using the Audit Engine.
    """
    try:
        # Call the audit logic
        # check_contract returns a JSON string, so we need to parse it
        result_json = check_contract(request.address)
        result = json.loads(result_json)
        
        # Check for error in the logic
        if "error" in result:
             # Just return it as part of the response for the UI to handle, 
             # or raise HTTPException if it's a critical server error.
             # Here we pass it through.
             pass

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "VeraGuard Audit Engine is active."}
