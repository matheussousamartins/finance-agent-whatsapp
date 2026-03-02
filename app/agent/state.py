from typing import Optional
from pydantic import BaseModel
from app.models.transaction import TransactionType


class MessageIntent(str):
    EXPENSE = "expense"       # "gastei 45 no ifood"
    INCOME = "income"         # "recebi salário 3200"
    QUERY = "query"           # "quanto gastei essa semana?"
    UNKNOWN = "unknown"       # mensagem não reconhecida


class AgentState(BaseModel):
    # Dados da mensagem recebida
    phone: str
    message: str

    # Resultado da classificação
    intent: Optional[str] = None

    # Dados extraídos da mensagem (quando for gasto ou entrada)
    amount: Optional[float] = None
    category: Optional[str] = None
    description: Optional[str] = None
    transaction_type: Optional[TransactionType] = None

    # Resposta final que será enviada ao usuário
    response: Optional[str] = None