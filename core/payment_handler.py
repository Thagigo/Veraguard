import random
from web3 import Web3

# Placeholder addresses to match contract
SECURITY_VAULT = "0x1111111111111111111111111111111111111111"

# Theoretical cost of a deep scan (100 scans threshold)
# Example: If 1 scan cost 0.0001 ETH in compute, 100 scans needs 0.01 ETH.
MIN_VAULT_BALANCE_WEI = Web3.to_wei(0.01, 'ether')

def calculate_dynamic_fee():
    """
    Calculates the 'Dynamic Fee' based on:
    1. Gemini Pro Input/Output token pricing (simulated).
    2. + 20% Safety Margin.
    """
    # Simulation of live pricing data
    # Base resource cost for AI reasoning (approx 0.0008 ETH)
    base_ai_cost = 0.0008 
    
    # Add some fluctuation to simulate market conditions
    market_fluctuation = random.uniform(0.95, 1.05) 
    
    current_cost = base_ai_cost * market_fluctuation
    
    # Add 20% Safety Margin
    total_fee = current_cost * 1.20
    
    return round(total_fee, 5)

def check_vault_balance():
    """
    Checks if the Security Vault has enough funds for 100 deep scans.
    Returns (bool, current_balance_eth).
    """
    # TODO: Connect to real Web3 provider to check balance of SECURITY_VAULT
    # For now, we simulate a healthy vault.
    # w3.eth.get_balance(SECURITY_VAULT)
    
    # Mock balance: 5.0 ETH (plenty)
    mock_balance_wei = Web3.to_wei(5.0, 'ether')
    
    if mock_balance_wei < MIN_VAULT_BALANCE_WEI:
        return False, Web3.from_wei(mock_balance_wei, 'ether')
    
    return True, Web3.from_wei(mock_balance_wei, 'ether')
