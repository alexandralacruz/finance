"""SQLAlchemy ORM models for finance data."""
import enum
from datetime import date, datetime

from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, Enum, ForeignKey, Text, Boolean
)
from sqlalchemy.orm import relationship

from app.database import Base


# ── Enums ──────────────────────────────────────────────────────────

class TransactionType(str, enum.Enum):
    income = "income"
    expense = "expense"
    investment = "investment"
    transfer_in = "transfer_in"
    transfer_out = "transfer_out"
    return_ = "return"          # rendimiento
    fee = "fee"                 # comisión
    deposit = "deposit"
    withdrawal = "withdrawal"
    freelance = "freelance"
    balance = "balance"         # saldo a la fecha (amount = diff con balance anterior)


class EntityType(str, enum.Enum):
    bank = "bank"
    investment = "investment"
    crypto = "crypto"
    payment_processor = "payment_processor"
    pension_fund = "pension_fund"
    other = "other"


class AccountType(str, enum.Enum):
    checking = "checking"
    savings = "savings"
    cdt = "cdt"
    pension = "pension"
    cesantias = "cesantias"
    spot = "spot"
    earn = "earn"
    futures = "futures"
    investment_fund = "investment_fund"
    other = "other"


# ── Models ─────────────────────────────────────────────────────────

class Entity(Base):
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), unique=True, nullable=False)
    type = Column(Enum(EntityType), nullable=False, default=EntityType.bank)
    active = Column(Boolean, nullable=False, default=True)
    is_primary_income = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    accounts = relationship("Account", back_populates="entity", lazy="dynamic")

    def __repr__(self):
        return f"<Entity(id={self.id}, name='{self.name}', type='{self.type}')>"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    description = Column(String(512), nullable=False)
    amount = Column(Float, nullable=False)          # positive = credit, negative = debit
    balance = Column(Float, nullable=True)           # running balance after tx
    currency = Column(String(10), nullable=False, default="COP")
    type = Column(Enum(TransactionType), nullable=False, default=TransactionType.expense)
    category = Column(String(64), nullable=True)     # legacy string category
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    related_entity = Column(String(64), nullable=True)  # for transfers
    source_file = Column(String(512), nullable=True)    # traceability
    created_at = Column(DateTime, default=datetime.utcnow)

    account = relationship("Account", back_populates="transactions")
    category_rel = relationship("Category", lazy="joined")

    def __repr__(self):
        return (
            f"<Transaction(id={self.id}, date={self.date}, "
            f"amount={self.amount}, account_id={self.account_id})>"
        )


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False)
    account_type = Column(Enum(AccountType), nullable=False, default=AccountType.checking)
    currency = Column(String(10), nullable=False, default="COP")
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    entity = relationship("Entity", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", lazy="dynamic")

    def __repr__(self):
        return (
            f"<Account(id={self.id}, entity_id={self.entity_id}, "
            f"type='{self.account_type}', currency='{self.currency}')>"
        )


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False)
    type = Column(String(16), nullable=False, default="expense")  # expense | income
    active = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}', type='{self.type}')>"


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)           # 1-12
    category = Column(String(64), nullable=True)      # legacy string category
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    limit_amount = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False, default="COP")
    created_at = Column(DateTime, default=datetime.utcnow)

    category_rel = relationship("Category", lazy="joined")

    def __repr__(self):
        return (
            f"<Budget(id={self.id}, {self.year}-{self.month:02d}, "
            f"category='{self.category}', limit={self.limit_amount})>"
        )


class RetirementPlan(Base):
    __tablename__ = "retirement_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False, default="Plan de retiro")
    target_amount_cop = Column(Float, nullable=True)
    target_amount_usd = Column(Float, nullable=True)
    target_years = Column(Integer, nullable=False, default=20)
    annual_return_pct = Column(Float, nullable=False, default=5.0)
    current_savings_cop = Column(Float, nullable=True, default=0.0)
    current_savings_usd = Column(Float, nullable=True, default=0.0)
    monthly_savings_capacity = Column(Float, nullable=True)  # calculated from real data
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<RetirementPlan(id={self.id}, name='{self.name}')>"
