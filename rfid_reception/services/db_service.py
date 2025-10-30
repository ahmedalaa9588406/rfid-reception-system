"""Database service for CRUD operations."""

import logging
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError
from rfid_reception.models.schema import Card, Transaction, init_db

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for managing database operations."""
    
    def __init__(self, db_path='rfid_reception.db'):
        """Initialize the database service."""
        self.db_path = db_path
        self.engine, self.Session = init_db(db_path)
        logger.info(f"Database initialized at {db_path}")
    
    def create_or_get_card(self, card_uid):
        """Create a new card or get existing one."""
        session = self.Session()
        try:
            card = session.query(Card).filter_by(card_uid=card_uid).first()
            if not card:
                card = Card(card_uid=card_uid, balance=0.0, offer_percent=0.0)
                session.add(card)
                session.commit()
                logger.info(f"Created new card: {card_uid}")
            
            # Return as dict to avoid detached instance issues
            result = {
                'id': card.id,
                'card_uid': card.card_uid,
                'balance': card.balance,
                'offer_percent': card.offer_percent,  # NEW: Include offer_percent
                'created_at': card.created_at,
                'last_topped_at': card.last_topped_at
            }
            return result
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error creating/getting card: {e}")
            raise
        finally:
            session.close()
    
    def top_up(self, card_uid, amount, employee=None, notes=None):
        """Add balance to a card and log transaction."""
        session = self.Session()
        try:
            card = session.query(Card).filter_by(card_uid=card_uid).first()
            if not card:
                card = Card(card_uid=card_uid, balance=0.0)
                session.add(card)
            
            card.balance += amount
            card.last_topped_at = datetime.now(timezone.utc)
            
            transaction = Transaction(
                card_uid=card_uid,
                type='topup',
                amount=amount,
                balance_after=card.balance,
                employee=employee,
                notes=notes
            )
            session.add(transaction)
            session.commit()
            
            logger.info(f"Top-up successful: {card_uid} + {amount} = {card.balance}")
            return card.balance, transaction.id
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error during top-up: {e}")
            raise
        finally:
            session.close()
    
    def get_transactions(self, start_date=None, end_date=None, card_uid=None):
        """Retrieve filtered transactions."""
        session = self.Session()
        try:
            query = session.query(Transaction)
            
            if card_uid:
                query = query.filter_by(card_uid=card_uid)
            if start_date:
                query = query.filter(Transaction.timestamp >= start_date)
            if end_date:
                query = query.filter(Transaction.timestamp <= end_date)
            
            query = query.order_by(Transaction.timestamp.desc())
            transactions = query.all()
            
            # Convert to list of dicts for easier handling
            result = [{
                'id': t.id,
                'card_uid': t.card_uid,
                'type': t.type,
                'amount': t.amount,
                'balance_after': t.balance_after,
                'employee': t.employee,
                'timestamp': t.timestamp,
                'notes': t.notes
            } for t in transactions]
            
            return result
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving transactions: {e}")
            raise
        finally:
            session.close()
    
    def get_card_balance(self, card_uid):
        """Get the current balance of a card."""
        session = self.Session()
        try:
            card = session.query(Card).filter_by(card_uid=card_uid).first()
            return card.balance if card else 0.0
        except SQLAlchemyError as e:
            logger.error(f"Error getting card balance: {e}")
            raise
        finally:
            session.close()
    
    def get_all_cards(self):
        """Get all cards with their most recent employee information."""
        session = self.Session()
        try:
            cards = session.query(Card).all()
            result = []
            
            for c in cards:
                # Get the most recent transaction for this card to fetch employee info
                recent_transaction = session.query(Transaction).filter_by(
                    card_uid=c.card_uid
                ).order_by(Transaction.timestamp.desc()).first()
                
                employee_name = recent_transaction.employee if recent_transaction else 'N/A'
                
                result.append({
                    'id': c.id,
                    'card_uid': c.card_uid,
                    'balance': c.balance,
                    'offer_percent': c.offer_percent,  # NEW: Include offer_percent
                    'created_at': c.created_at,
                    'last_topped_at': c.last_topped_at,
                    'employee_name': employee_name
                })
            
            return result
        except SQLAlchemyError as e:
            logger.error(f"Error getting all cards: {e}")
            raise
        finally:
            session.close()
    
    def log_card_read(self, card_uid, employee=None):
        """
        Log a card read event (audit trail).
        
        Args:
            card_uid: The card UID that was read
            employee: Optional employee name
        """
        session = self.Session()
        try:
            card = session.query(Card).filter_by(card_uid=card_uid).first()
            if not card:
                card = Card(card_uid=card_uid, balance=0.0)
                session.add(card)
            
            # Create a read event transaction (type='read')
            transaction = Transaction(
                card_uid=card_uid,
                type='read',
                amount=0.0,
                balance_after=card.balance,
                employee=employee,
                notes='Card read from Arduino'
            )
            session.add(transaction)
            session.commit()
            
            logger.info(f"Card read event logged: {card_uid}")
            return transaction.id
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error logging card read event: {e}")
            raise
        finally:
            session.close()
    
    def delete_card(self, card_uid):
        """Delete a card and all its transactions."""
        session = self.Session()
        try:
            # Delete all transactions for this card
            session.query(Transaction).filter_by(card_uid=card_uid).delete()
            
            # Delete the card itself
            card = session.query(Card).filter_by(card_uid=card_uid).first()
            if card:
                session.delete(card)
            
            session.commit()
            logger.info(f"Card {card_uid} and its transactions deleted")
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error deleting card {card_uid}: {e}")
            raise
        finally:
            session.close()
    
    # NEW METHOD: Update offer percentage for a card
    def update_card_offer(self, card_uid, offer_percent):
        """Update the offer percentage for a card.
        
        Args:
            card_uid: The card UID
            offer_percent: The offer percentage (0-100)
        """
        session = self.Session()
        try:
            card = session.query(Card).filter_by(card_uid=card_uid).first()
            if not card:
                logger.warning(f"Card {card_uid} not found for offer update")
                return False
            
            card.offer_percent = offer_percent
            session.commit()
            
            logger.info(f"Updated offer_percent to {offer_percent}% for card {card_uid}")
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error updating offer percent: {e}")
            raise
        finally:
            session.close()
