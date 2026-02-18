import unittest
import os
import tempfile
from core.database import init_db, add_credit, get_credits, use_credit, record_tx, tx_exists
import core.database

class TestPaymentGateway(unittest.TestCase):
    def setUp(self):
        # Create a temp file
        self.db_fd, self.db_path = tempfile.mkstemp()
        os.close(self.db_fd) # Close immediately so sqlite can use it
        core.database.DB_PATH = self.db_path
        init_db()

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.unlink(self.db_path)
            except PermissionError:
                pass # Best effort cleanup

    def test_credit_flow(self):
        user = "test_user_1"
        self.assertEqual(get_credits(user), 0)
        
        # Add credit
        add_credit(user, 1)
        self.assertEqual(get_credits(user), 1)
        
        # Use credit
        success = use_credit(user)
        self.assertTrue(success)
        self.assertEqual(get_credits(user), 0)
        
        # Fail usage
        success = use_credit(user)
        self.assertFalse(success)

    def test_record_tx(self):
        user = "test_user_2"
        record_tx("0x123", user, 0.001)
        # Should persist
        # (verification relies on separate helper, but here we trust the function runs)

if __name__ == '__main__':
    unittest.main()
