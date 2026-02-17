import json
import hashlib
import time
import os

CACHE_FILE = "audit_cache.json"
CACHE_EXPIRY_SECONDS = 24 * 60 * 60  # 24 Hours

def get_contract_hash(bytecode: str) -> str:
    """Generates a SHA256 hash of the contract bytecode."""
    return hashlib.sha256(bytecode.encode()).hexdigest()

def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_cache(cache_data):
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache_data, f, indent=4)

def get_cached_audit(bytecode: str):
    """
    Retrieves cached audit result if exists and not expired.
    Returns None if cache miss or expired.
    """
    cache = load_cache()
    contract_hash = get_contract_hash(bytecode)
    
    if contract_hash in cache:
        entry = cache[contract_hash]
        if time.time() - entry['timestamp'] < CACHE_EXPIRY_SECONDS:
            return entry['result']
        else:
            # Expired
            del cache[contract_hash]
            save_cache(cache)
            
    return None

def set_cached_audit(bytecode: str, result: dict):
    """Saves audit result to cache."""
    cache = load_cache()
    contract_hash = get_contract_hash(bytecode)
    
    cache[contract_hash] = {
        "timestamp": time.time(),
        "result": result
    }
    save_cache(cache)
