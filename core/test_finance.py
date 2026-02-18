import unittest
from core.payment_handler import calculate_dynamic_fee, check_vault_balance, MIN_VAULT_BALANCE_WEI

class TestFinanceCore(unittest.TestCase):
    
    def test_dynamic_fee_range(self):
        # Base is ~0.0008, + fluctuation, +20% margin. 
        # Expect roughly 0.0009 - 0.0012
        fee = calculate_dynamic_fee()
        print(f"Calculated Dynamic Fee: {fee} ETH")
        self.assertTrue(0.0008 < fee < 0.0015, f"Fee {fee} out of expected range")

    def test_vault_solvency(self):
        # Mocking logic is inside the function for now, but we verify the return structure
        is_solvent, balance = check_vault_balance()
        self.assertTrue(is_solvent)
        self.assertTrue(float(balance) > 0)
        print(f"Vault Balance: {balance} ETH (Solvent: {is_solvent})")

if __name__ == '__main__':
    unittest.main()
