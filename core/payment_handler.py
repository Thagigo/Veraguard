import random
from web3 import Web3
import time
import hashlib

# Placeholder addresses to match contract
SECURITY_VAULT = "0x1111111111111111111111111111111111111111"

# Theoretical cost of a deep scan (100 scans threshold)
# Example: If 1 scan cost 0.0001 ETH in compute, 100 scans needs 0.01 ETH.
MIN_VAULT_BALANCE_WEI = Web3.to_wei(0.01, 'ether')

def get_eth_price():
    """
    MOCK Oracle: Fetches ETH/USD price.
    In prod, use Chainlink or CEX API.
    """
    try:
        import requests
        # Free API (Rate limits apply, handle gracefully)
        response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd", timeout=2)
        if response.status_code == 200:
            data = response.json()
            return float(data["ethereum"]["usd"])
    except Exception as e:
        print(f"Oracle Error: {e}")
    
    # Fallback: Mocking price fluctuation around $2000 (Current Market)
    base = 2000.0
    fluctuation = (time.time() % 100) - 50 # +/- $50
    return base + fluctuation

def calculate_dynamic_fee():
    """
    Returns a 'Signed Quote' object with 1% slippage buffer.
    Prices are pegged to USD.
    """
    eth_price = get_eth_price()
    
    # 1. Credit Bundle Price (Target: $0.05 per credit? No, strictly based on compute?
    # Let's say 7 credits = $20 USD (~$3/credit) for simplicity in this demo, 
    # Or keep the original loose peg. 
    # Logic: 7 credits = 0.007 ETH * 3000 = $21. Close enough.
    # Let's peg 1 Credit = $3.00 USD.
    
    usd_per_credit = 3.00
    eth_per_credit = usd_per_credit / eth_price
    
    bundle_size = 1 # We quote per 1 credit usually, or base fee?
    # The frontend multiplies this amount by 7 for the bundle.
    # So 'amount' should be price of 1 credit unit?
    # Existing frontend does: amount * (quote.amount || 0.001)
    # So Quote.amount = Price Per Credit (ETH).
    
    buffered_fee = eth_per_credit * 1.05 # 5% Buffer for volatility
    
    # 2. Vera-Pass Price (Target: $150 USD)
    subscription_usd = 150.00
    subscription_eth = subscription_usd / eth_price
    
    # 3. Expiry
    expiry = int(time.time()) + 60
    
    # 4. Signature
    payload = f"{buffered_fee:.6f}:{subscription_eth:.6f}:{expiry}:VERAGUARD_SECRET"
    signature = hashlib.sha256(payload.encode()).hexdigest()
    
    return {
        "amount": round(buffered_fee, 6),
        "currency": "ETH", 
        "expiry": expiry,
        "signature": signature,
        "subscription_amount": round(subscription_eth, 6),
        "eth_price_usd": round(eth_price, 2)
    }

def check_referral_security(referrer_data, referee_ip_hash, referee_ua_hash):
    """
    Sybil Resistance: Checks if Referrer IP or User-Agent matches Referee.
    Returns: True if safe, False if potential fraud.
    """
    if referrer_data:
        owner_id, owner_ip_hash, owner_ua_hash = referrer_data
        
        # 1. IP Hash Match
        if owner_ip_hash == referee_ip_hash:
            return False # Fraud: Self-referral (Same IP)
            
        # 2. User-Agent Hash Match (Basic Fingerprinting)
        # If both are same, high likelihood of same device if rare UA, but common for "iPhone".
        # We will flag it for Manual Review (or just deny reward automatically for strictness).
        # For this implementation: strict deny.
        if owner_ua_hash == referee_ua_hash:
             return False
            
        return True
    return False

def check_vault_balance():
    """
    Checks if the Security Vault (Relayer) has enough ETH to pay for Gas.
    Returns: (bool, balance_eth)
    """
    # In production, we would use Web3 to check balance of SECURITY_VAULT
    # balance_wei = w3.eth.get_balance(SECURITY_VAULT)
    # is_solvent = balance_wei > MIN_VAULT_BALANCE_WEI
    
    # Mock Solvency for Demo
    mock_balance = 1.5 # 1.5 ETH
    is_solvent = True
    return is_solvent, mock_balance

