"""Database schema definitions using SQLAlchemy."""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime, timezone

Base = declarative_base()


class Card(Base):
    """RFID Card model."""
    __tablename__ = 'cards'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    card_uid = Column(String, unique=True, nullable=False, index=True)
    balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_topped_at = Column(DateTime, nullable=True)
    
    transactions = relationship("Transaction", back_populates="card", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Card(card_uid='{self.card_uid}', balance={self.balance})>"


class Transaction(Base):
    """Transaction model."""
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    card_uid = Column(String, ForeignKey('cards.card_uid'), nullable=False, index=True)
    type = Column(String, default='topup')  # topup, refund, adjust
    amount = Column(Float, nullable=False)
    balance_after = Column(Float, nullable=False)
    employee = Column(String, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    notes = Column(String, nullable=True)
    
    card = relationship("Card", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction(card_uid='{self.card_uid}', type='{self.type}', amount={self.amount})>"


def init_db(db_path='rfid_reception.db'):
    """Initialize the database and create tables if they don't exist."""
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return engine, Session
