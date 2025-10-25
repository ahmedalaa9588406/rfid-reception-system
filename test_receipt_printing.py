"""
Test script for receipt printing functionality.

This script demonstrates the receipt printing features:
1. Print a transaction receipt
2. Generate card summary report
3. Test both PDF and direct printing modes
"""

import sys
import os
from datetime import datetime

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from rfid_reception.services.receipt_printer import ReceiptPrinter


def test_transaction_receipt():
    """Test printing a transaction receipt."""
    print("\n" + "="*60)
    print("TEST 1: Transaction Receipt")
    print("="*60)
    
    # Initialize receipt printer
    printer = ReceiptPrinter(
        company_name="ABC Electronics Store",
        company_info={
            'address': '123 Main Street, Cairo, Egypt',
            'phone': '+20 123 456 7890'
        }
    )
    
    # Sample transaction data
    card_uid = "04A1B2C3D4E5F6"
    amount = 100.50
    balance_after = 250.75
    transaction_id = 123
    employee = "Ahmed Hassan"
    
    print(f"\nPrinting receipt for transaction #{transaction_id}")
    print(f"Card: {card_uid}")
    print(f"Amount: {amount:.2f} EGP")
    print(f"New Balance: {balance_after:.2f} EGP")
    
    # Print receipt (will save as PDF if direct printing not available)
    success, result = printer.print_receipt(
        card_uid=card_uid,
        amount=amount,
        balance_after=balance_after,
        transaction_id=transaction_id,
        employee=employee,
        timestamp=datetime.now(),
        auto_print=False  # Set to False to always generate PDF
    )
    
    if success:
        print(f"\n✅ Success! Receipt saved to:")
        print(f"   {result}")
        print(f"\nYou can open this file to view/print the receipt.")
    else:
        print(f"\n❌ Failed: {result}")


def test_card_summary():
    """Test printing a card summary report."""
    print("\n" + "="*60)
    print("TEST 2: Card Summary Report")
    print("="*60)
    
    printer = ReceiptPrinter(
        company_name="ABC Electronics Store",
        company_info={
            'address': '123 Main Street, Cairo, Egypt',
            'phone': '+20 123 456 7890'
        }
    )
    
    # Sample card data
    card_data = {
        'card_uid': '04A1B2C3D4E5F6',
        'balance': 250.75,
        'created_at': '2025-10-01 09:00:00',
        'last_topped_at': '2025-10-23 13:45:30'
    }
    
    # Sample transaction history
    transactions = [
        {
            'id': 5,
            'type': 'topup',
            'amount': 100.50,
            'balance_after': 250.75,
            'timestamp': '2025-10-23 13:45:30',
            'employee': 'Ahmed Hassan'
        },
        {
            'id': 4,
            'type': 'topup',
            'amount': 50.00,
            'balance_after': 150.25,
            'timestamp': '2025-10-22 10:30:15',
            'employee': 'Sara Mohamed'
        },
        {
            'id': 3,
            'type': 'topup',
            'amount': 100.25,
            'balance_after': 100.25,
            'timestamp': '2025-10-21 14:20:45',
            'employee': 'Ahmed Hassan'
        },
        {
            'id': 2,
            'type': 'read',
            'amount': 0.00,
            'balance_after': 0.00,
            'timestamp': '2025-10-21 14:20:00',
            'employee': 'Ahmed Hassan'
        }
    ]
    
    print(f"\nGenerating summary for card: {card_data['card_uid']}")
    print(f"Current Balance: {card_data['balance']:.2f} EGP")
    print(f"Total Transactions: {len(transactions)}")
    
    success, result = printer.print_card_summary(
        card_data=card_data,
        transactions=transactions
    )
    
    if success:
        print(f"\n✅ Success! Card summary saved to:")
        print(f"   {result}")
        print(f"\nThis file contains complete transaction history.")
    else:
        print(f"\n❌ Failed: {result}")


def test_direct_printing_check():
    """Check if direct printing is available."""
    print("\n" + "="*60)
    print("TEST 3: Direct Printing Availability")
    print("="*60)
    
    printer = ReceiptPrinter()
    
    if printer.printer_available:
        print("\n✅ Direct printing is AVAILABLE")
        print("   Receipts will be sent directly to your printer.")
        
        try:
            import win32print
            default_printer = win32print.GetDefaultPrinter()
            print(f"   Default printer: {default_printer}")
        except:
            pass
    else:
        print("\n⚠️  Direct printing is NOT available")
        print("   Receipts will be saved as PDF files.")
        print("\n   To enable direct printing on Windows:")
        print("   1. Run: pip install pywin32")
        print("   2. Set a default printer in Windows settings")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("🖨️  RECEIPT PRINTING TEST SUITE")
    print("="*60)
    
    # Test 1: Transaction receipt
    test_transaction_receipt()
    
    # Test 2: Card summary
    test_card_summary()
    
    # Test 3: Check direct printing
    test_direct_printing_check()
    
    # Summary
    print("\n" + "="*60)
    print("📂 RECEIPTS LOCATION")
    print("="*60)
    
    receipts_dir = os.path.join(os.getcwd(), "receipts")
    print(f"\nAll receipts are saved in:")
    print(f"   {receipts_dir}")
    
    if os.path.exists(receipts_dir):
        files = [f for f in os.listdir(receipts_dir) if f.endswith('.pdf')]
        print(f"\nCurrent receipts: {len(files)} file(s)")
        for f in files[-5:]:  # Show last 5
            print(f"   - {f}")
    else:
        print("\n(Folder will be created when first receipt is printed)")
    
    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60)
    print("\nNext steps:")
    print("1. Check the 'receipts' folder for generated PDFs")
    print("2. Open the PDFs to verify formatting")
    print("3. Test printing from PDF viewer (Ctrl+P)")
    print("4. Run the main application to test auto-print feature")
    print("\n")


if __name__ == "__main__":
    main()
