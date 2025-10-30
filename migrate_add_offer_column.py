"""One-time migration script to add offer_percent column to existing database."""

import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    db_path = 'rfid_reception.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(cards)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'offer_percent' not in columns:
            logger.info("Adding offer_percent column to cards table...")
            cursor.execute("ALTER TABLE cards ADD COLUMN offer_percent REAL DEFAULT 0")
            conn.commit()
            logger.info("✓ Column added successfully!")
        else:
            logger.info("offer_percent column already exists")
        
        conn.close()
        logger.info("Migration complete!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    migrate()
