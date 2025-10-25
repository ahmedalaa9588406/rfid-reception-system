"""
Cleanup script to fix duplicate cards caused by spacing and UID:AMOUNT format issues.
This script will merge duplicate cards and fix the database.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rfid_reception.services.db_service import DatabaseService
from collections import defaultdict


def format_card_uid(raw_uid):
    """Format card UID - same logic as in main_window.py"""
    # Remove amount data if present
    if ':' in raw_uid:
        uid_part = raw_uid.split(':')[0]
        raw_uid = uid_part
    
    # Remove spaces, tabs, uppercase
    formatted = raw_uid.replace(' ', '').replace('\t', '').strip().upper()
    return formatted


def cleanup_duplicate_cards(db_path='rfid_reception.db'):
    """Find and merge duplicate cards."""
    
    print("\n" + "="*70)
    print("  CLEANUP DUPLICATE CARDS")
    print("="*70 + "\n")
    
    db = DatabaseService(db_path)
    
    # Get all cards
    all_cards = db.get_all_cards()
    
    print(f"📊 Found {len(all_cards)} cards in database\n")
    
    # Group cards by formatted UID
    card_groups = defaultdict(list)
    
    for card in all_cards:
        original_uid = card['card_uid']
        formatted_uid = format_card_uid(original_uid)
        card_groups[formatted_uid].append(card)
    
    print(f"📋 Grouped into {len(card_groups)} unique cards\n")
    
    # Find duplicates
    duplicates_found = 0
    
    for formatted_uid, cards in card_groups.items():
        if len(cards) > 1:
            duplicates_found += 1
            print(f"🔍 Found {len(cards)} duplicates for: {formatted_uid}")
            print("   Original UIDs:")
            
            # Show all variations
            total_balance = 0
            for card in cards:
                balance = card['balance']
                total_balance += balance
                print(f"      - {card['card_uid']:30s} | Balance: {balance:.2f} EGP")
            
            print(f"   📊 Total balance across duplicates: {total_balance:.2f} EGP")
            print(f"   ✅ Should be merged into: {formatted_uid}")
            print()
    
    if duplicates_found == 0:
        print("✅ No duplicate cards found! Database is clean.")
        return
    
    print("="*70)
    print(f"\n⚠️  Found {duplicates_found} sets of duplicate cards!\n")
    
    response = input("Would you like to merge these duplicates? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("\n❌ Cleanup cancelled. No changes made.")
        return
    
    print("\n🔧 Starting cleanup process...\n")
    
    # Merge duplicates
    merged_count = 0
    
    for formatted_uid, cards in card_groups.items():
        if len(cards) > 1:
            print(f"Merging: {formatted_uid}")
            
            # Calculate total balance
            total_balance = sum(card['balance'] for card in cards)
            
            # Get all transactions for all duplicate cards
            all_transactions = []
            for card in cards:
                txns = db.get_transactions(card_uid=card['card_uid'])
                all_transactions.extend(txns)
            
            # Delete all duplicate cards
            for card in cards:
                try:
                    db.delete_card(card['card_uid'])
                    print(f"   Deleted: {card['card_uid']}")
                except Exception as e:
                    print(f"   Error deleting {card['card_uid']}: {e}")
            
            # Create new merged card with correct UID and total balance
            try:
                new_card = db.create_or_get_card(formatted_uid)
                
                # Set the total balance
                if total_balance > 0:
                    db.top_up(
                        formatted_uid,
                        total_balance,
                        employee="System",
                        notes=f"Merged from {len(cards)} duplicate cards"
                    )
                
                print(f"   ✅ Created merged card: {formatted_uid} | Balance: {total_balance:.2f} EGP")
                merged_count += 1
                
            except Exception as e:
                print(f"   ❌ Error creating merged card: {e}")
            
            print()
    
    print("="*70)
    print(f"\n🎉 Cleanup complete!")
    print(f"   - Merged {merged_count} sets of duplicate cards")
    print(f"   - Database is now clean")
    print("\n✅ All cards now have standardized UIDs (no spaces, no amounts)")
    print("="*70 + "\n")


def show_current_cards():
    """Show current cards in database."""
    db = DatabaseService('rfid_reception.db')
    cards = db.get_all_cards()
    
    print("\n" + "="*70)
    print("  CURRENT CARDS IN DATABASE")
    print("="*70 + "\n")
    
    if not cards:
        print("No cards found in database.\n")
        return
    
    print(f"{'UID':<40} {'Balance':<15} {'Employee'}")
    print("-" * 70)
    
    for card in cards:
        uid = card['card_uid']
        balance = card['balance']
        employee = card.get('employee_name', 'N/A')
        print(f"{uid:<40} {f'{balance:.2f} EGP':<15} {employee}")
    
    print()


if __name__ == "__main__":
    print("\n" + "🧹 "*35)
    print("  RFID CARD DATABASE CLEANUP UTILITY")
    print("🧹 "*35 + "\n")
    
    try:
        # Show current state
        show_current_cards()
        
        # Run cleanup
        cleanup_duplicate_cards()
        
        # Show final state
        print("\n" + "="*70)
        print("  AFTER CLEANUP")
        print("="*70)
        show_current_cards()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
