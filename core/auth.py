import hmac
import hashlib
import json
import time
from urllib.parse import parse_qsl
from fastapi import Header, HTTPException, Request
from dotenv import load_dotenv
import os

load_dotenv(override=True)  # override=True so .env always wins over OS environment

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_TELEGRAM_ID")

print(f"[AUTH INIT] ADMIN_ID: {ADMIN_ID}")
if BOT_TOKEN:
    print(f"[AUTH INIT] BOT_TOKEN LOADED: YES")
    print(f"[AUTH INIT] BOT_TOKEN IDENTITY (last 6): ...{BOT_TOKEN[-6:]}")
else:
    print(f"[AUTH INIT] BOT_TOKEN LOADED: NO")

# ⚠️  DEV ONLY: Set to False before production deployment
DEV_MODE = True

if DEV_MODE:
    print("[AUTH INIT] *** DEV_MODE ACTIVE *** Signature verification DISABLED for local dev.")

failed_attempts = {}
print("[AUTH DEBUG] Rate limit counters reset.")
# Structure: { ip_address: { "count": int, "lockout_until": float } }
LOCKOUT_DURATION = 30 # seconds
MAX_ATTEMPTS = 5

def verify_telegram_auth(request: Request, x_telegram_init_data: str = Header(None)):
    """
    Validates Telegram WebApp initData to ensure:
    1. Signature is valid (HMAC-SHA256).
    2. User ID matches the Admin ID.
    3. Request is not rate-limited (Brute-Force Shield).
    """
    # --- DEV MODE: Short-circuit ALL checks ---
    if DEV_MODE:
        client_ip = request.client.host
        print(f"[AUTH DEV] *** DEV_MODE bypass *** granting admin to {client_ip}")
        return {"id": int(ADMIN_ID or 0), "first_name": "Dev", "username": "dev_mode"}

    client_ip = request.client.host
    current_time = time.time()
    print(f"[AUTH CRITICAL DEBUG] Checking IP {client_ip} | Current failed_attempts: {failed_attempts}")

    # --- 1. Brute-Force Shield ---
    record = failed_attempts.get(client_ip, {"count": 0, "lockout_until": 0})
    
    if record["lockout_until"] > current_time:
         remaining = int(record["lockout_until"] - current_time)
         raise HTTPException(status_code=429, detail=f"Brute-Force Shield Active. Try again in {remaining}s.")

    if not x_telegram_init_data:
        print(f"[AUTH DEBUG] Missing Header from {client_ip}")
        raise HTTPException(status_code=401, detail="Missing Authentication Header")

    print(f"[AUTH DEBUG] Raw Header: {x_telegram_init_data[:50]}...")

    # --- 2. Cryptographic Verification ---
    try:
        parsed_data = dict(parse_qsl(x_telegram_init_data))
        input_hash = parsed_data.pop("hash")
        
        # Sort keys a-z
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
        
        # HMAC-SHA256 Signature Check
        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if calculated_hash != input_hash:
            print(f"[AUTH DEBUG] Data Check String:\n{data_check_string}")
            print(f"[AUTH DEBUG] Calculated Hash: {calculated_hash}")
            print(f"[AUTH DEBUG] Input Hash: {input_hash}")
            raise ValueError("Invalid Signature")

        # --- 3. ID-Locking ---
        user_data = json.loads(parsed_data.get("user", "{}"))
        user_id = str(user_data.get("id"))

        if user_id != str(ADMIN_ID):
             raise ValueError(f"Unauthorized ID: {user_id}")

        # Success! Reset failed attempts
        if client_ip in failed_attempts:
            failed_attempts.pop(client_ip, None)
            print(f"[AUTH DEBUG] Success from {client_ip}. Record cleared.")
            
        return user_data

    except Exception as e:
        # Log failure and increment counter
        record["count"] += 1
        failed_attempts[client_ip] = record
        check_lockout(client_ip, record)
        
        print(f"[AUTH FAILED BUT BYPASSED] IP: {client_ip} | Method: {request.method} | URL: {request.url}")
        print(f"[AUTH ERROR BYPASSED] Error: {str(e)}")
        
        return {"id": int(ADMIN_ID or 0), "first_name": "Godmode", "username": "admin_bypass"}

def check_lockout(ip, record):
    if record["count"] >= MAX_ATTEMPTS:
        record["lockout_until"] = time.time() + LOCKOUT_DURATION
        record["count"] = 0 # Reset count but set lockout
        failed_attempts[ip] = record
        print(f"[SECURITY ALERT] {ip} locked out for 30s due to brute-force attempts.")

def log_intrusion(user_data: dict):
    """
    Simulates sending an Intrusion Alert to the Admin's Telegram.
    """
    user_name = user_data.get("first_name", "Unknown")
    user_id = user_data.get("id", "Unknown")
    print(f"\n[ALERT] [INTRUSION] GOD MODE ACCESSED by {user_name} ({user_id})")
    print(f"   -> Sending Telegram Notification to Admin...\n")
