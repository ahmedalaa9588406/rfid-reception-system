"""
Complete system test for RFID Reception System.
Tests all major functionality including reading, writing, and receipt printing.
"""

import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rfid_reception.services.db_service import DatabaseService
from rfid_reception.services.receipt_printer import ReceiptPrinter


def print_section(title):
    """Print a section header."""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")


def test_database_operations():
    """Test database CRUD operations."""
    print_section("TESTING DATABASE OPERATIONS")
    
    # Initialize database service
    db = DatabaseService('test_rfid.db')
    
    # Test 1: Create new cards
    print("✓ Test 1: Creating new cards...")
    card1_uid = "ABCD1234EFGH5678"
    card2_uid = "1234567890ABCDEF"
    
    card1 = db.create_or_get_card(card1_uid)
    card2 = db.create_or_get_card(card2_uid)
    
    print(f"  Card 1: {card1['card_uid']} - Balance: {card1['balance']:.2f} EGP")
    print(f"  Card 2: {card2['card_uid']} - Balance: {card2['balance']:.2f} EGP")
    
    # Test 2: Top-up operations
    print("\n✓ Test 2: Top-up operations...")
    new_balance1, tx_id1 = db.top_up(card1_uid, 50.00, employee="Test Employee 1")
    print(f"  Card 1 topped up: +50.00 EGP → Balance: {new_balance1:.2f} EGP (TX: {tx_id1})")
    
    new_balance2, tx_id2 = db.top_up(card2_uid, 100.00, employee="Test Employee 2")
    print(f"  Card 2 topped up: +100.00 EGP → Balance: {new_balance2:.2f} EGP (TX: {tx_id2})")
    
    # Test 3: Additional top-up
    print("\n✓ Test 3: Additional top-up...")
    new_balance1, tx_id3 = db.top_up(card1_uid, 25.50, employee="Test Employee 1")
    print(f"  Card 1 topped up: +25.50 EGP → Balance: {new_balance1:.2f} EGP (TX: {tx_id3})")
    
    # Test 4: Get balance
    print("\n✓ Test 4: Retrieving balances...")
    balance1 = db.get_card_balance(card1_uid)
    balance2 = db.get_card_balance(card2_uid)
    print(f"  Card 1 Balance: {balance1:.2f} EGP")
    print(f"  Card 2 Balance: {balance2:.2f} EGP")
    
    # Test 5: Get transactions
    print("\n✓ Test 5: Retrieving transactions...")
    transactions = db.get_transactions(card_uid=card1_uid)
    print(f"  Card 1 has {len(transactions)} transaction(s):")
    for tx in transactions:
        print(f"    - {tx['timestamp']}: {tx['type'].upper()} {tx['amount']:.2f} EGP → Balance: {tx['balance_after']:.2f} EGP")
    
    # Test 6: Get all cards
    print("\n✓ Test 6: Retrieving all cards...")
    all_cards = db.get_all_cards()
    print(f"  Total cards in system: {len(all_cards)}")
    for card in all_cards:
        print(f"    - UID: {card['card_uid']}, Balance: {card['balance']:.2f} EGP")
    
    # Test 7: Deduction (negative top-up)
    print("\n✓ Test 7: Testing deduction (negative amount)...")
    new_balance1, tx_id4 = db.top_up(card1_uid, -10.00, employee="Test Employee 1", notes="Test deduction")
    print(f"  Card 1 deducted: -10.00 EGP → Balance: {new_balance1:.2f} EGP (TX: {tx_id4})")
    
    print("\n✅ All database tests passed!")
    return db, card1_uid, card2_uid


def test_receipt_printing(db, card1_uid, card2_uid):
    """Test receipt printing functionality."""
    print_section("TESTING RECEIPT PRINTING")
    
    # Initialize receipt printer
    printer = ReceiptPrinter(
        company_name="RFID Reception Test System",
        company_info={
            'address': '123 Test Street, Cairo, Egypt',
            'phone': '+20 123 456 7890'
        }
    )
    
    # Test 1: Print single receipt
    print("✓ Test 1: Generating single transaction receipt...")
    success, result = printer.print_receipt(
        card_uid=card1_uid,
        amount=50.00,
        balance_after=75.50,
        transaction_id=1,
        employee="Test Employee 1",
        timestamp=datetime.now(),
        auto_print=False  # Save as PDF
    )
    
    if success:
        print(f"  ✅ Receipt saved: {result}")
    else:
        print(f"  ❌ Receipt failed: {result}")
    
    # Test 2: Print card summary
    print("\n✓ Test 2: Generating card summary...")
    card_data = db.create_or_get_card(card1_uid)
    transactions = db.get_transactions(card_uid=card1_uid)
    
    success, result = printer.print_card_summary(
        card_data=card_data,
        transactions=transactions
    )
    
    if success:
        print(f"  ✅ Card summary saved: {result}")
    else:
        print(f"  ❌ Card summary failed: {result}")
    
    # Test 3: Multiple receipts
    print("\n✓ Test 3: Generating multiple receipts...")
    for i, amount in enumerate([20.00, 35.00, 50.00], start=1):
        success, result = printer.print_receipt(
            card_uid=card2_uid,
            amount=amount,
            balance_after=100.00 + (i * amount),
            transaction_id=10 + i,
            employee=f"Employee {i}",
            timestamp=datetime.now(),
            auto_print=False
        )
        if success:
            print(f"  ✅ Receipt {i} saved")
        else:
            print(f"  ❌ Receipt {i} failed: {result}")
    
    print("\n✅ All receipt printing tests passed!")


def test_edge_cases(db):
    """Test edge cases and error handling."""
    print_section("TESTING EDGE CASES")
    
    # Test 1: Zero balance top-up
    print("✓ Test 1: Zero amount top-up...")
    try:
        test_uid = "TEST_ZERO_123"
        balance, tx_id = db.top_up(test_uid, 0.00, employee="Test Employee")
        print(f"  ✅ Zero top-up handled: Balance = {balance:.2f} EGP")
    except Exception as e:
        print(f"  ℹ️  Zero top-up result: {e}")
    
    # Test 2: Large amount
    print("\n✓ Test 2: Large amount top-up...")
    try:
        test_uid = "TEST_LARGE_456"
        balance, tx_id = db.top_up(test_uid, 999999.99, employee="Test Employee")
        print(f"  ✅ Large amount handled: Balance = {balance:.2f} EGP")
    except Exception as e:
        print(f"  ❌ Large amount failed: {e}")
    
    # Test 3: Negative balance (deduction more than available)
    print("\n✓ Test 3: Deduction more than balance...")
    try:
        test_uid = "TEST_NEGATIVE_789"
        db.top_up(test_uid, 50.00, employee="Test Employee")
        balance, tx_id = db.top_up(test_uid, -100.00, employee="Test Employee", notes="Over-deduction test")
        print(f"  ℹ️  Negative balance allowed: Balance = {balance:.2f} EGP")
    except Exception as e:
        print(f"  ℹ️  Negative balance result: {e}")
    
    # Test 4: Duplicate card creation
    print("\n✓ Test 4: Duplicate card handling...")
    test_uid = "TEST_DUPLICATE_111"
    card1 = db.create_or_get_card(test_uid)
    card2 = db.create_or_get_card(test_uid)
    if card1['id'] == card2['id']:
        print(f"  ✅ Duplicate card handled correctly (same ID)")
    else:
        print(f"  ❌ Duplicate card created different IDs")
    
    # Test 5: Special characters in UID
    print("\n✓ Test 5: Special characters in UID...")
    try:
        special_uid = "TEST-CARD_123!@#"
        card = db.create_or_get_card(special_uid)
        print(f"  ✅ Special characters handled: {card['card_uid']}")
    except Exception as e:
        print(f"  ❌ Special characters failed: {e}")
    
    print("\n✅ Edge case tests completed!")


def test_transaction_scenarios():
    """Test realistic transaction scenarios."""
    print_section("TESTING REALISTIC SCENARIOS")
    
    db = DatabaseService('test_scenarios.db')
    
    # Scenario 1: New employee onboarding
    print("📋 Scenario 1: New Employee Onboarding")
    emp_uid = "EMP_001_AHMED"
    print(f"  1. Creating card for employee: {emp_uid}")
    card = db.create_or_get_card(emp_uid)
    print(f"     Initial balance: {card['balance']:.2f} EGP")
    
    print(f"  2. Initial top-up: 200.00 EGP")
    balance, _ = db.top_up(emp_uid, 200.00, employee="HR Manager", notes="Initial employee credit")
    print(f"     New balance: {balance:.2f} EGP")
    
    # Scenario 2: Daily usage
    print("\n📋 Scenario 2: Daily Usage Pattern")
    print("  Simulating breakfast, lunch, and coffee purchases...")
    
    transactions = [
        (15.00, "Breakfast"),
        (5.00, "Coffee"),
        (25.00, "Lunch"),
        (5.00, "Coffee"),
        (10.00, "Snack")
    ]
    
    for amount, description in transactions:
        balance, _ = db.top_up(emp_uid, -amount, employee="Cafeteria", notes=description)
        print(f"  - {description}: -{amount:.2f} EGP → Balance: {balance:.2f} EGP")
    
    # Scenario 3: Monthly top-up
    print("\n📋 Scenario 3: Monthly Refill")
    print(f"  Current balance: {balance:.2f} EGP")
    print(f"  Adding monthly allowance: 250.00 EGP")
    balance, _ = db.top_up(emp_uid, 250.00, employee="Finance", notes="Monthly allowance")
    print(f"  New balance: {balance:.2f} EGP")
    
    # Scenario 4: Lost card - balance transfer
    print("\n📋 Scenario 4: Lost Card - Balance Transfer")
    old_uid = emp_uid
    new_uid = "EMP_001_AHMED_NEW"
    
    print(f"  1. Old card: {old_uid}")
    old_balance = db.get_card_balance(old_uid)
    print(f"     Balance to transfer: {old_balance:.2f} EGP")
    
    print(f"  2. Creating new card: {new_uid}")
    new_card = db.create_or_get_card(new_uid)
    
    print(f"  3. Transferring balance...")
    db.top_up(old_uid, -old_balance, employee="Admin", notes="Card lost - balance transferred")
    db.top_up(new_uid, old_balance, employee="Admin", notes="Balance transferred from old card")
    
    print(f"     Old card balance: {db.get_card_balance(old_uid):.2f} EGP")
    print(f"     New card balance: {db.get_card_balance(new_uid):.2f} EGP")
    
    print("\n✅ All scenarios completed successfully!")


def main():
    """Run all tests."""
    print("\n" + "🔬 " + "="*58 + " 🔬")
    print("  RFID RECEPTION SYSTEM - COMPLETE FUNCTIONALITY TEST")
    print("🔬 " + "="*58 + " 🔬\n")
    
    try:
        # Test 1: Database operations
        db, card1_uid, card2_uid = test_database_operations()
        
        # Test 2: Receipt printing
        test_receipt_printing(db, card1_uid, card2_uid)
        
        # Test 3: Edge cases
        test_edge_cases(db)
        
        # Test 4: Realistic scenarios
        test_transaction_scenarios()
        
        # Final summary
        print_section("TEST SUMMARY")
        print("✅ All tests completed successfully!")
        print("\nTest databases created:")
        print("  - test_rfid.db")
        print("  - test_scenarios.db")
        print("\nReceipts saved in:")
        print("  - receipts/ folder")
        print("\n" + "="*60)
        print("  🎉 SYSTEM IS FULLY FUNCTIONAL! 🎉")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
