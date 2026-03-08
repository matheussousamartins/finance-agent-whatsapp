from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

from app.models.transaction import Base, Transaction, TransactionType
from app.models.user import User, OnboardingStep

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./finza.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Cria as tabelas no banco se não existirem."""
    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    """Retorna uma sessão do banco."""
    return SessionLocal()


# ─────────────────────────────────────────
# FUNÇÕES DE USUÁRIO
# ─────────────────────────────────────────

def get_user(phone: str) -> User | None:
    """Busca um usuário pelo telefone."""
    with get_session() as session:
        return session.query(User).filter(User.phone == phone).first()


def create_user(phone: str) -> User:
    """Cria um novo usuário."""
    with get_session() as session:
        user = User(phone=phone, onboarding_step=OnboardingStep.WAITING_NAME)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def update_user_name(phone: str, name: str) -> User:
    """Atualiza o nome do usuário e avança o onboarding."""
    with get_session() as session:
        user = session.query(User).filter(User.phone == phone).first()
        user.name = name
        user.onboarding_step = OnboardingStep.WAITING_BUDGET
        session.commit()
        session.refresh(user)
        return user


def update_user_budget(phone: str, budget: float) -> User:
    """Atualiza o orçamento do usuário e finaliza o onboarding."""
    with get_session() as session:
        user = session.query(User).filter(User.phone == phone).first()
        user.monthly_budget = budget
        user.onboarding_step = OnboardingStep.DONE
        session.commit()
        session.refresh(user)
        return user


# ─────────────────────────────────────────
# FUNÇÕES DE TRANSAÇÃO
# ─────────────────────────────────────────

def save_transaction(phone: str, type: TransactionType, amount: float, category: str, description: str = None) -> Transaction:
    """Salva uma transação no banco."""
    with get_session() as session:
        transaction = Transaction(
            phone=phone,
            type=type,
            amount=amount,
            category=category,
            description=description,
        )
        session.add(transaction)
        session.commit()
        session.refresh(transaction)
        return transaction


def get_summary(phone: str, days: int = 30) -> dict:
    """Retorna um resumo financeiro dos últimos X dias."""
    since = datetime.utcnow() - timedelta(days=days)

    with get_session() as session:
        transactions = (
            session.query(Transaction)
            .filter(Transaction.phone == phone)
            .filter(Transaction.created_at >= since)
            .all()
        )

        total_income = sum(t.amount for t in transactions if t.type == TransactionType.INCOME)
        total_expense = sum(t.amount for t in transactions if t.type == TransactionType.EXPENSE)
        balance = total_income - total_expense

        expenses_by_category = {}
        for t in transactions:
            if t.type == TransactionType.EXPENSE:
                expenses_by_category[t.category] = expenses_by_category.get(t.category, 0) + t.amount

        return {
            "period_days": days,
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": balance,
            "expenses_by_category": expenses_by_category,
            "transactions_count": len(transactions),
        }


def get_recent_transactions(phone: str, limit: int = 5) -> list[Transaction]:
    """Retorna as últimas transações do usuário."""
    with get_session() as session:
        return (
            session.query(Transaction)
            .filter(Transaction.phone == phone)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
            .all()
        )