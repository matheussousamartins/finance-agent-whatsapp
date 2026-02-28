from sqlalchemy import Column, Integer, String, Float, DateTime, Enum
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime
import enum


class Base(DeclarativeBase):
    pass


class TransactionType(str, enum.Enum):
    EXPENSE = "expense"   # Gasto
    INCOME = "income"     # Entrada


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String, nullable=False, index=True)   # identifica o usuário pelo número
    type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=False)             # ex: alimentação, transporte, salário
    description = Column(String, nullable=True)          # ex: "ifood", "uber"
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return (
            f"<Transaction "
            f"type={self.type} "
            f"amount={self.amount} "
            f"category={self.category} "
            f"description={self.description}>"
        )

    def to_dict(self):
        return {
            "id": self.id,
            "phone": self.phone,
            "type": self.type.value,
            "amount": self.amount,
            "category": self.category,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
        }