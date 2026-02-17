import sys
import os
import json
import time

# Add the current directory to sys.path so we can import 'core'
sys.path.append(os.getcwd())

from core import cache

def test_caching():
    print("Testing Semantic Caching...")
    
    # 1. Clear Cache
    if os.path.exists(cache.CACHE_FILE):
        os.remove(cache.CACHE_FILE)
        print("Cache cleared.")

    bytecode = "0x6080604052600436106100" # Dummy bytecode
    result = {"vera_score": 88, "warnings": ["Test Warning"]}

    # 2. Get (Miss)
    res = cache.get_cached_audit(bytecode)
    print(f"Cache Miss Check: {res is None} (Expected True)")

    # 3. Set
    cache.set_cached_audit(bytecode, result)
    print("Cache Set.")

    # 4. Get (Hit)
    res = cache.get_cached_audit(bytecode)
    # Using json.dumps to compare dicts with potential ordering differences is safer, 
    # but here direct comparison works if simple.
    print(f"Cache Hit Check: {res == result} (Expected True)")
    print(f"Cached Result: {res}")
    
    if res == result:
        print("\nSUCCESS: Caching logic verified.")
    else:
        print("\nFAILURE: Caching logic incorrect.")

if __name__ == "__main__":
    test_caching()
