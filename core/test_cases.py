import json
import unittest
from unittest.mock import MagicMock, patch
from core.audit_logic import check_contract

class TestVeraGuardAudit(unittest.TestCase):

    @patch('core.audit_logic.Web3')
    def test_ghost_mint_signature(self, mock_web3):
        # Setup mock for a contract containing the ghost mint signature
        mock_w3_instance = MagicMock()
        mock_web3.return_value = mock_w3_instance
        mock_web3.HTTPProvider.return_value = MagicMock()
        mock_w3_instance.is_connected.return_value = True
        mock_w3_instance.is_address.return_value = True
        mock_w3_instance.to_checksum_address.return_value = "0xGhostContract"
        # Bytecode contains "6d696e74" ('mint')
        mock_w3_instance.eth.get_code.return_value = b'\x60\x80\x60\x40\x52\x6d\x69\x6e\x74\x00' 

        result_json = check_contract("0xRealGhost")
        result = json.loads(result_json)

        print(f"\nReal Bytecode Test (Ghost Mint): {result}")
        # Score might not be 0 because Triage/Hunter might not have deducted *everything*, 
        # but Signature check should set it to 0 (100 - 100).
        # Actually in logic: vera_score -= 100. So yes 0.
        self.assertEqual(result['vera_score'], 0) 
        self.assertTrue(any("Ghost Mint" in w for w in result['warnings']))

    @patch('core.audit_logic.Web3')
    def test_uups_bricking_risk(self, mock_web3):
        mock_w3_instance = MagicMock()
        mock_web3.return_value = mock_w3_instance
        mock_web3.HTTPProvider.return_value = MagicMock()
        mock_w3_instance.is_connected.return_value = True
        mock_w3_instance.is_address.return_value = True
        mock_w3_instance.to_checksum_address.return_value = "0xProxiableButBroken"
        
        # Bytecode has 'proxiableUUID' selector (c4d66de8) but NO 'upgradeTo' (3659cfe6)
        mock_w3_instance.eth.get_code.return_value = bytes.fromhex("6080604052c4d66de80000000000000000")

        result_json = check_contract("0xProxiableButBroken")
        result = json.loads(result_json)

        print(f"\nReal Bytecode Test (UUPS Brick): {result}")
        self.assertTrue(any("UUPS Silent Death" in w for w in result['warnings']))
        self.assertEqual(result['vera_score'], 0)

    @patch('core.audit_logic.Web3')
    def test_legacy_math_detection(self, mock_web3):
        mock_w3_instance = MagicMock()
        mock_web3.return_value = mock_w3_instance
        mock_web3.HTTPProvider.return_value = MagicMock()
        mock_w3_instance.is_connected.return_value = True
        mock_w3_instance.is_address.return_value = True
        mock_w3_instance.to_checksum_address.return_value = "0xOldContract"
        
        # Low score because Triage (-5 for small size) + Legacy Math (-40)
        mock_w3_instance.eth.get_code.return_value = bytes.fromhex("6080604052000000000000")

        result_json = check_contract("0xOldContract")
        result = json.loads(result_json)

        print(f"\nReal Bytecode Test (Legacy Math): {result}")
        self.assertTrue(any("Legacy Math" in w for w in result['warnings']))
        self.assertTrue(result['vera_score'] <= 60) 

    @patch('core.audit_logic.Web3')
    def test_simulation_ghost(self, mock_web3):
        # Testing the explicit simulation bypass string
        result_json = check_contract("0x...ghost")
        result = json.loads(result_json)
        self.assertEqual(result['vera_score'], 0)
        self.assertTrue("SIMULATION" in result['note'])

if __name__ == '__main__':
    unittest.main()
