"""Unit tests for database service."""

import unittest
import tempfile
import os
from datetime import datetime, timedelta
from rfid_reception.services.db_service import DatabaseService


class TestDatabaseService(unittest.TestCase):
    """Test cases for DatabaseService."""
    
    def setUp(self):
        """Set up test database."""
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        self.db_service = DatabaseService(self.test_db.name)
    
    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.test_db.name):
            os.unlink(self.test_db.name)
    
    def test_create_card(self):
        """Test creating a new card."""
        card = self.db_service.create_or_get_card('TEST123')
        self.assertIsNotNone(card)
        self.assertEqual(card['card_uid'], 'TEST123')
        self.assertEqual(card['balance'], 0.0)
    
    def test_get_existing_card(self):
        """Test getting an existing card."""
        card1 = self.db_service.create_or_get_card('TEST123')
        card2 = self.db_service.create_or_get_card('TEST123')
        self.assertEqual(card1['card_uid'], card2['card_uid'])
    
    def test_top_up(self):
        """Test top-up operation."""
        card_uid = 'TEST123'
        amount = 50.0
        
        balance, transaction_id = self.db_service.top_up(card_uid, amount)
        
        self.assertEqual(balance, 50.0)
        self.assertIsNotNone(transaction_id)
        
        # Top up again
        balance, transaction_id = self.db_service.top_up(card_uid, 25.0)
        self.assertEqual(balance, 75.0)
    
    def test_get_card_balance(self):
        """Test getting card balance."""
        card_uid = 'TEST123'
        
        # Initially should be 0
        balance = self.db_service.get_card_balance(card_uid)
        self.assertEqual(balance, 0.0)
        
        # After top-up
        self.db_service.top_up(card_uid, 100.0)
        balance = self.db_service.get_card_balance(card_uid)
        self.assertEqual(balance, 100.0)
    
    def test_get_transactions(self):
        """Test retrieving transactions."""
        card_uid = 'TEST123'
        
        # Create some transactions
        self.db_service.top_up(card_uid, 50.0, employee='Alice')
        self.db_service.top_up(card_uid, 25.0, employee='Bob')
        
        # Get all transactions
        transactions = self.db_service.get_transactions()
        self.assertEqual(len(transactions), 2)
        
        # Check transaction details
        self.assertEqual(transactions[0]['amount'], 25.0)  # Most recent first
        self.assertEqual(transactions[0]['employee'], 'Bob')
    
    def test_get_transactions_filtered(self):
        """Test retrieving filtered transactions."""
        # Create transactions for different cards
        self.db_service.top_up('CARD1', 50.0)
        self.db_service.top_up('CARD2', 25.0)
        self.db_service.top_up('CARD1', 30.0)
        
        # Filter by card
        transactions = self.db_service.get_transactions(card_uid='CARD1')
        self.assertEqual(len(transactions), 2)
        
        # Filter by date
        tomorrow = datetime.now() + timedelta(days=1)
        transactions = self.db_service.get_transactions(end_date=tomorrow)
        self.assertEqual(len(transactions), 3)
    
    def test_get_all_cards(self):
        """Test getting all cards."""
        self.db_service.top_up('CARD1', 50.0)
        self.db_service.top_up('CARD2', 25.0)
        self.db_service.top_up('CARD3', 75.0)
        
        cards = self.db_service.get_all_cards()
        self.assertEqual(len(cards), 3)
        
        # Check balances
        card_balances = {c['card_uid']: c['balance'] for c in cards}
        self.assertEqual(card_balances['CARD1'], 50.0)
        self.assertEqual(card_balances['CARD2'], 25.0)
        self.assertEqual(card_balances['CARD3'], 75.0)


if __name__ == '__main__':
    unittest.main()
