"""
Migration script to add offer tracking columns to transactions table.

This script adds:
- amount_before_offer: Original payment amount before offer bonus
- offer_amount: Bonus amount from offer
- offer_percent: Offer percentage applied (in transactions table)

Run this script ONCE to update your existing database.
"""

import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = 'rfid_reception.db'


def migrate_database(db_path=DB_PATH):
    """Add offer tracking columns to transactions table."""
    
    if not Path(db_path).exists():
        logger.error(f"Database not found: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(transactions)")
        columns = [col[1] for col in cursor.fetchall()]
        
        migrations_needed = []
        
        if 'amount_before_offer' not in columns:
            migrations_needed.append(('amount_before_offer', 'REAL'))
        
        if 'offer_amount' not in columns:
            migrations_needed.append(('offer_amount', 'REAL'))
        
        if 'offer_percent' not in columns:
            migrations_needed.append(('offer_percent', 'REAL'))
        
        if not migrations_needed:
            logger.info("✓ Database already up to date! All columns exist.")
            return True
        
        # Add missing columns
        for column_name, column_type in migrations_needed:
            try:
                sql = f"ALTER TABLE transactions ADD COLUMN {column_name} {column_type}"
                logger.info(f"Adding column: {column_name}")
                cursor.execute(sql)
                logger.info(f"✓ Added column: {column_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    logger.info(f"Column {column_name} already exists, skipping...")
                else:
                    raise
        
        conn.commit()
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(transactions)")
        columns_after = [col[1] for col in cursor.fetchall()]
        
        logger.info("\n" + "="*60)
        logger.info("Migration completed successfully!")
        logger.info("="*60)
        logger.info("\nColumns in transactions table:")
        for col in columns_after:
            logger.info(f"  - {col}")
        
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  RFID Reception System - Database Migration")
    print("  Adding Offer Tracking to Transactions")
    print("="*60 + "\n")
    
    success = migrate_database()
    
    if success:
        print("\n✓ Migration completed successfully!")
        print("\nYou can now track:")
        print("  - Original payment amount (before offer)")
        print("  - Offer bonus amount")
        print("  - Offer percentage applied")
        print("\nAll new transactions will include these details.")
    else:
        print("\n✗ Migration failed! Check the logs above.")
    
    input("\nPress Enter to exit...")
