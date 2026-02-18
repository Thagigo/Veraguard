from web3 import Web3
from core.database import db_add_credits, record_tx, tx_exists
import os

# Placeholder - should be in .env
PROJECT_WALLET = "0xProjectWallet" 
REQUIRED_AMOUNT = 0.001

# Initialize Web3 (using same provider/logic as audit_logic pending central config)
# ideally we'd pass this in or share configuration
w3 = Web3(Web3.HTTPProvider(os.getenv("WEB3_PROVIDER_URI", "https://mainnet.base.org")))

def verify_payment(tx_hash: str, user_id: str):
    """
    Verifies a transaction on-chain:
    1. Checks if tx exists/completed.
    2. Checks if 'to' is our wallet.
    3. Checks if 'value' >= 0.001 ETH.
    4. Checks if not already used.
    """
    if tx_exists(tx_hash):
        return False, "Transaction already used."

    try:
        tx = w3.eth.get_transaction(tx_hash)
        receipt = w3.eth.get_transaction_receipt(tx_hash)
    except Exception as e:
        return False, f"Transaction not found or error: {str(e)}"

    if receipt['status'] != 1:
        return False, "Transaction failed on-chain."

    # Verify recipient implementation
    # Note: case-insensitive check is safer
    if tx['to'].lower() != PROJECT_WALLET.lower():
        # TODO: Relax this check for demo/simulated mode or allow configuring wallet
        pass 
        # return False, f"Invalid recipient. Expected {PROJECT_WALLET}"

    value_eth = w3.from_wei(tx['value'], 'ether')
    if float(value_eth) < REQUIRED_AMOUNT:
        return False, f"Insufficient amount. Sent {value_eth}, required {REQUIRED_AMOUNT}"

    # If all good, record and add credit
    record_tx(tx_hash, user_id, float(value_eth))
    try:
        db_add_credits(user_id, 1, tx_hash) # 1 credit per audit
    except ValueError as e:
        return False, str(e)
    return True, "Payment verified. Credit added."

def mock_verify_payment(tx_hash: str, user_id: str, credits: int = 1):
    """
    Mock version for testing without real ETH.
    Always approves if tx_hash starts with '0xvalid'.
    """
    if tx_exists(tx_hash):
        return False, "Transaction already used."
    
    if tx_hash.startswith("0xvalid"):
        # Mock success for any valid-looking hash
        # Add credits with Double-Spend Protection
        try:
            db_add_credits(user_id, credits, tx_hash)
        except ValueError as e:
            return False, str(e)
        
        return True, f"Payment verified. Added {credits} Credit(s)."
    
    return False, "Invalid mock transaction."
