"""
Complete Python Integration Example for RFID Reception System

This script demonstrates the full workflow:
1. Connect to Arduino RFID reader
2. Scan RFID cards
3. Add amounts to cards
4. Save transactions to database
5. Retrieve and display transaction history

Requirements:
- Arduino with MFRC522 RFID reader (sketch uploaded)
- Python packages: pyserial, sqlalchemy

Usage:
    python python_integration_example.py
"""

import sys
import time
from datetime import datetime

# Add parent directory to path to import rfid_reception modules
sys.path.insert(0, '..')

from rfid_reception.services.serial_comm import SerialCommunicationService
from rfid_reception.services.db_service import DatabaseService


def print_separator():
    """Print a separator line."""
    print("=" * 60)


def main():
    """Main function demonstrating the complete workflow."""
    print_separator()
    print("🎯 RFID Reception System - Complete Integration Example")
    print_separator()
    
    # Configuration
    COM_PORT = 'COM3'  # Change this to your Arduino's COM port
    BAUDRATE = 115200
    DB_PATH = '../rfid_reception.db'
    
    # Initialize services
    print("\n📡 Initializing Services...")
    serial_service = SerialCommunicationService(port=COM_PORT, baudrate=BAUDRATE)
    db_service = DatabaseService(db_path=DB_PATH)
    
    try:
        # Connect to Arduino
        print(f"🔌 Connecting to Arduino on {COM_PORT}...")
        serial_service.connect()
        print("✅ Successfully connected to Arduino!")
        
        # Test connection
        print("\n🏓 Testing connection with PING...")
        if serial_service.check_connection():
            print("✅ PING successful - Arduino is responding!")
        else:
            print("❌ PING failed - Check connection")
            return
        
        print_separator()
        print("📖 MENU - Choose an operation:")
        print("1. Read a card and display info")
        print("2. Add amount to a card (top-up)")
        print("3. View all cards in database")
        print("4. View transaction history")
        print("5. Exit")
        print_separator()
        
        while True:
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == '1':
                # Read card
                read_card_demo(serial_service, db_service)
                
            elif choice == '2':
                # Top-up card
                topup_card_demo(serial_service, db_service)
                
            elif choice == '3':
                # View all cards
                view_all_cards(db_service)
                
            elif choice == '4':
                # View transactions
                view_transactions(db_service)
                
            elif choice == '5':
                print("\n👋 Exiting... Goodbye!")
                break
                
            else:
                print("❌ Invalid choice. Please enter 1-5.")
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    finally:
        # Cleanup
        print("\n🔌 Disconnecting from Arduino...")
        serial_service.disconnect()
        print("✅ Disconnected successfully!")


def read_card_demo(serial_service, db_service):
    """Demonstrate reading a card."""
    print("\n" + "="*60)
    print("📖 READ CARD")
    print("="*60)
    print("📌 Please place an RFID card near the reader...")
    
    success, uid = serial_service.read_card()
    
    if success:
        print(f"✅ Card detected!")
        print(f"   Card UID: {uid}")
        
        # Get or create card in database
        card_info = db_service.create_or_get_card(uid)
        
        print(f"\n💾 Database Information:")
        print(f"   Card UID: {card_info['card_uid']}")
        print(f"   Balance: ${card_info['balance']:.2f}")
        print(f"   Created: {card_info['created_at']}")
        if card_info['last_topped_at']:
            print(f"   Last Top-up: {card_info['last_topped_at']}")
        
        # Log the read event
        db_service.log_card_read(uid, employee="System")
        print(f"   ✅ Read event logged to database")
        
    else:
        print(f"❌ Failed to read card: {uid}")


def topup_card_demo(serial_service, db_service):
    """Demonstrate adding amount to a card."""
    print("\n" + "="*60)
    print("💰 TOP-UP CARD")
    print("="*60)
    
    # Get amount from user
    try:
        amount = float(input("Enter amount to add: $"))
        if amount <= 0:
            print("❌ Amount must be greater than 0")
            return
    except ValueError:
        print("❌ Invalid amount")
        return
    
    # Get employee name (optional)
    employee = input("Enter employee name (or press Enter to skip): ").strip()
    if not employee:
        employee = "System"
    
    print(f"\n📌 Please place an RFID card near the reader...")
    
    # Write to card via Arduino
    success, uid, message = serial_service.write_card(amount)
    
    if success:
        print(f"✅ Card written successfully!")
        print(f"   Card UID: {uid}")
        print(f"   Amount Written: ${amount:.2f}")
        
        # Save to database
        new_balance, transaction_id = db_service.top_up(
            card_uid=uid,
            amount=amount,
            employee=employee,
            notes=f"Top-up via Arduino - {message}"
        )
        
        print(f"\n💾 Database Updated:")
        print(f"   New Balance: ${new_balance:.2f}")
        print(f"   Transaction ID: {transaction_id}")
        print(f"   Employee: {employee}")
        print(f"   ✅ Transaction saved successfully!")
        
    else:
        print(f"❌ Failed to write card: {message}")


def view_all_cards(db_service):
    """View all cards in the database."""
    print("\n" + "="*60)
    print("💳 ALL CARDS IN DATABASE")
    print("="*60)
    
    cards = db_service.get_all_cards()
    
    if not cards:
        print("📭 No cards found in database")
        return
    
    print(f"\nTotal Cards: {len(cards)}\n")
    
    for i, card in enumerate(cards, 1):
        print(f"{i}. Card UID: {card['card_uid']}")
        print(f"   Balance: ${card['balance']:.2f}")
        print(f"   Employee: {card['employee_name']}")
        print(f"   Created: {card['created_at']}")
        if card['last_topped_at']:
            print(f"   Last Top-up: {card['last_topped_at']}")
        print()


def view_transactions(db_service):
    """View transaction history."""
    print("\n" + "="*60)
    print("📊 TRANSACTION HISTORY")
    print("="*60)
    
    # Option to filter by card
    filter_choice = input("\nFilter by card UID? (y/n): ").strip().lower()
    card_uid = None
    
    if filter_choice == 'y':
        card_uid = input("Enter card UID: ").strip().upper()
    
    # Get transactions
    transactions = db_service.get_transactions(card_uid=card_uid)
    
    if not transactions:
        print("📭 No transactions found")
        return
    
    print(f"\nTotal Transactions: {len(transactions)}\n")
    
    for i, txn in enumerate(transactions, 1):
        print(f"{i}. Transaction ID: {txn['id']}")
        print(f"   Type: {txn['type'].upper()}")
        print(f"   Card UID: {txn['card_uid']}")
        print(f"   Amount: ${txn['amount']:.2f}")
        print(f"   Balance After: ${txn['balance_after']:.2f}")
        print(f"   Employee: {txn['employee'] or 'N/A'}")
        print(f"   Timestamp: {txn['timestamp']}")
        if txn['notes']:
            print(f"   Notes: {txn['notes']}")
        print()


def quick_test():
    """Quick test function for development."""
    print("🔧 Running Quick Test...")
    
    serial_service = SerialCommunicationService(port='COM3', baudrate=115200)
    db_service = DatabaseService(db_path='../rfid_reception.db')
    
    try:
        serial_service.connect()
        print("✅ Connected to Arduino")
        
        # Test PING
        if serial_service.check_connection():
            print("✅ PING successful")
        
        # Test READ
        print("\n📌 Place a card near the reader...")
        success, uid = serial_service.read_card()
        if success:
            print(f"✅ Card read: {uid}")
            
            # Get card info
            card_info = db_service.create_or_get_card(uid)
            print(f"💾 Balance: ${card_info['balance']:.2f}")
        
    finally:
        serial_service.disconnect()


if __name__ == "__main__":
    # Uncomment the line below for quick testing:
    # quick_test()
    
    # Run the full interactive demo:
    main()
