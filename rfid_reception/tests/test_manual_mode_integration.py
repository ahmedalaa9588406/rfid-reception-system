"""Integration test for manual mode functionality."""

import unittest
import tempfile
import os
from rfid_reception.services.db_service import DatabaseService


class TestManualModeIntegration(unittest.TestCase):
    """Integration tests for manual entry mode workflow."""
    
    def setUp(self):
        """Set up test database."""
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        self.db_service = DatabaseService(self.test_db.name)
    
    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.test_db.name):
            os.unlink(self.test_db.name)
    
    def test_complete_manual_workflow(self):
        """Test complete manual entry workflow: create card, top-up, check balance."""
        # Step 1: User enters manual UID
        manual_uid = 'MANUAL-WORKFLOW-TEST'
        
        # Step 2: Check if card exists (simulates loading card)
        initial_balance = self.db_service.get_card_balance(manual_uid)
        self.assertEqual(initial_balance, 0.0)
        
        # Step 3: Perform first top-up (manual mode)
        new_balance, tx_id = self.db_service.top_up(
            manual_uid,
            50.0,
            employee='Test Receptionist',
            notes='Manual entry mode'
        )
        self.assertEqual(new_balance, 50.0)
        
        # Step 4: Verify balance updated
        balance_check = self.db_service.get_card_balance(manual_uid)
        self.assertEqual(balance_check, 50.0)
        
        # Step 5: Perform second top-up
        new_balance2, tx_id2 = self.db_service.top_up(
            manual_uid,
            30.0,
            employee='Test Receptionist',
            notes='Manual entry mode'
        )
        self.assertEqual(new_balance2, 80.0)
        
        # Step 6: Check transaction history
        transactions = self.db_service.get_transactions(card_uid=manual_uid)
        self.assertEqual(len(transactions), 2)
        
        # Verify transaction details (ordered by timestamp desc)
        self.assertEqual(transactions[0]['amount'], 30.0)
        self.assertEqual(transactions[0]['balance_after'], 80.0)
        self.assertEqual(transactions[0]['notes'], 'Manual entry mode')
        
        self.assertEqual(transactions[1]['amount'], 50.0)
        self.assertEqual(transactions[1]['balance_after'], 50.0)
        self.assertEqual(transactions[1]['notes'], 'Manual entry mode')
    
    def test_manual_vs_arduino_mode_distinction(self):
        """Test that manual mode transactions can be distinguished from Arduino mode."""
        # Create manual mode transaction
        manual_uid = 'MANUAL-123'
        self.db_service.top_up(
            manual_uid,
            100.0,
            employee='Receptionist A',
            notes='Manual entry mode'
        )
        
        # Create Arduino mode transaction (no notes or different notes)
        arduino_uid = 'ARDUINO-456'
        self.db_service.top_up(
            arduino_uid,
            100.0,
            employee='Receptionist A',
            notes=None
        )
        
        # Get all transactions
        all_transactions = self.db_service.get_transactions()
        self.assertEqual(len(all_transactions), 2)
        
        # Filter manual mode transactions
        manual_txs = [t for t in all_transactions if t['notes'] == 'Manual entry mode']
        self.assertEqual(len(manual_txs), 1)
        self.assertEqual(manual_txs[0]['card_uid'], manual_uid)
        
        # Filter Arduino transactions
        arduino_txs = [t for t in all_transactions if t['notes'] != 'Manual entry mode']
        self.assertEqual(len(arduino_txs), 1)
        self.assertEqual(arduino_txs[0]['card_uid'], arduino_uid)
    
    def test_switching_between_modes(self):
        """Test a card being used in both manual and Arduino mode."""
        card_uid = 'CARD-BOTH-MODES'
        
        # First top-up in manual mode
        balance1, _ = self.db_service.top_up(
            card_uid,
            50.0,
            notes='Manual entry mode'
        )
        self.assertEqual(balance1, 50.0)
        
        # Second top-up in Arduino mode (no special notes)
        balance2, _ = self.db_service.top_up(
            card_uid,
            30.0,
            notes=None
        )
        self.assertEqual(balance2, 80.0)
        
        # Third top-up back in manual mode
        balance3, _ = self.db_service.top_up(
            card_uid,
            20.0,
            notes='Manual entry mode'
        )
        self.assertEqual(balance3, 100.0)
        
        # Verify all transactions are recorded
        transactions = self.db_service.get_transactions(card_uid=card_uid)
        self.assertEqual(len(transactions), 3)
        
        # Check total balance
        final_balance = self.db_service.get_card_balance(card_uid)
        self.assertEqual(final_balance, 100.0)


if __name__ == '__main__':
    unittest.main()
