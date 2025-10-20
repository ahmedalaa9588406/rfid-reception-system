"""Unit tests for manual entry mode functionality."""

import unittest
import tempfile
import os
from rfid_reception.services.db_service import DatabaseService


class TestManualMode(unittest.TestCase):
    """Test cases for manual entry mode."""
    
    def setUp(self):
        """Set up test database."""
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        self.db_service = DatabaseService(self.test_db.name)
    
    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.test_db.name):
            os.unlink(self.test_db.name)
    
    def test_manual_entry_card_creation(self):
        """Test creating a card with manual entry."""
        card_uid = 'MANUAL-TEST-123'
        card = self.db_service.create_or_get_card(card_uid)
        
        self.assertIsNotNone(card)
        self.assertEqual(card['card_uid'], card_uid)
        self.assertEqual(card['balance'], 0.0)
    
    def test_manual_entry_top_up(self):
        """Test top-up with manually entered UID."""
        card_uid = 'MANUAL-CARD-456'
        amount = 100.0
        
        # Perform manual top-up
        balance, transaction_id = self.db_service.top_up(
            card_uid, 
            amount,
            employee='Test Employee',
            notes='Manual entry mode'
        )
        
        self.assertEqual(balance, 100.0)
        self.assertIsNotNone(transaction_id)
        
        # Verify transaction was recorded
        transactions = self.db_service.get_transactions(card_uid=card_uid)
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0]['type'], 'topup')
        self.assertEqual(transactions[0]['notes'], 'Manual entry mode')
    
    def test_manual_entry_multiple_topups(self):
        """Test multiple top-ups on manually entered card."""
        card_uid = 'MANUAL-CARD-789'
        
        # First top-up
        balance1, _ = self.db_service.top_up(
            card_uid, 
            50.0,
            notes='Manual entry mode'
        )
        self.assertEqual(balance1, 50.0)
        
        # Second top-up
        balance2, _ = self.db_service.top_up(
            card_uid, 
            30.0,
            notes='Manual entry mode'
        )
        self.assertEqual(balance2, 80.0)
        
        # Third top-up
        balance3, _ = self.db_service.top_up(
            card_uid, 
            20.0,
            notes='Manual entry mode'
        )
        self.assertEqual(balance3, 100.0)
        
        # Verify all transactions
        transactions = self.db_service.get_transactions(card_uid=card_uid)
        self.assertEqual(len(transactions), 3)
    
    def test_manual_entry_special_characters_in_uid(self):
        """Test UIDs with hyphens and underscores."""
        test_uids = [
            'CARD-123-456',
            'CARD_789_012',
            'CARD-123_456',
            'ABC123DEF456'
        ]
        
        for uid in test_uids:
            balance, _ = self.db_service.top_up(uid, 10.0, notes='Manual entry mode')
            self.assertEqual(balance, 10.0)
            
            # Verify card exists
            retrieved_balance = self.db_service.get_card_balance(uid)
            self.assertEqual(retrieved_balance, 10.0)
    
    def test_manual_entry_get_balance(self):
        """Test getting balance for manually entered card."""
        card_uid = 'MANUAL-BALANCE-TEST'
        
        # Initially should be 0
        balance = self.db_service.get_card_balance(card_uid)
        self.assertEqual(balance, 0.0)
        
        # After top-up
        self.db_service.top_up(card_uid, 75.50, notes='Manual entry mode')
        balance = self.db_service.get_card_balance(card_uid)
        self.assertEqual(balance, 75.50)
    
    def test_manual_mode_transaction_filtering(self):
        """Test filtering manual mode transactions."""
        # Create manual mode transactions
        self.db_service.top_up('MANUAL-1', 50.0, notes='Manual entry mode')
        self.db_service.top_up('MANUAL-2', 30.0, notes='Manual entry mode')
        
        # Create regular transaction
        self.db_service.top_up('ARDUINO-1', 20.0, notes=None)
        
        # Get all transactions
        all_transactions = self.db_service.get_transactions()
        self.assertEqual(len(all_transactions), 3)
        
        # Count manual mode transactions
        manual_transactions = [t for t in all_transactions if t['notes'] == 'Manual entry mode']
        self.assertEqual(len(manual_transactions), 2)


if __name__ == '__main__':
    unittest.main()
