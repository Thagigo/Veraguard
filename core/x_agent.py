import urllib.parse
import os

def draft_tweet(address: str, signature_name: str, hex_signature: str) -> str:
    """
    Auto-drafts a tweet for 100% Grounded Matches to push a Public Signal.
    """
    tweet_text = f"🚨 VERA-VERIFY ALERT 🚨\n\n🛡️ Veraguard Ancestral IQ has achieved a 100% Grounded Match on a live smart contract.\n\n📍 Target: {address}\n🦠 Vector: {signature_name}\n🧬 HEX Signature: {hex_signature}\n\nProtocol is compromised. Stay SAFU. 🦅\n\n#Veraguard #Web3Security #Bust"
    
    # In a real implementation this might hit the Twitter/X API via tweepy.
    # For now, we generate an intent URL and log it.
    
    encoded_text = urllib.parse.quote(tweet_text)
    intent_url = f"https://twitter.com/intent/tweet?text={encoded_text}"
    
    print(f"\n[X-AGENT] DRAFTED TWEET:\n{tweet_text}\n[X-AGENT] PUBLISH LINK: {intent_url}\n")
    
    return intent_url

def check_and_draft(address: str, warnings: list, bytecode: str) -> str | None:
    """
    Helper function to check warnings for known signatures and draft a tweet if found. 
    Returns the intent_url if a tweet was drafted.
    """
    # Extract signature info if a GROUNDED MATCH occurred (e.g. from SIGNATURES_OF_MALICE)
    # This maps warning names to hex signatures without importing audit_logic directly to avoid circular dependency
    
    known_vectors = {
        "Ghost Mint (Signature A)": "6d696e74",
        "UUPS Silent Death (Signature B)": "3659cfe6",
        "Hidden Proxy logic or DelegateCall": "f4|360894a13ba1a321...",
    }
    
    for warning in warnings:
        if warning.startswith("DETECTED: "):
            vector_name = warning.replace("DETECTED: ", "")
            if vector_name in known_vectors:
                hex_sig = known_vectors[vector_name]
                return draft_tweet(address, vector_name, hex_sig)
                
    return None
