import json
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from app.agent.state import AgentState, MessageIntent
from app.agent.prompts import (
    CLASSIFIER_PROMPT, EXTRACTOR_PROMPT, QUERY_PROMPT, IMAGE_EXTRACTOR_PROMPT,
    ONBOARDING_WELCOME_PROMPT, ONBOARDING_BUDGET_PROMPT,
    ONBOARDING_DONE_PROMPT, ONBOARDING_INVALID_BUDGET_PROMPT,
)
from app.models.transaction import TransactionType
from app.models.user import OnboardingStep
from app.services.database import (
    save_transaction, get_summary,
    get_user, create_user, update_user_name, update_user_budget,
)

logger = logging.getLogger(__name__)

llm = ChatOpenAI(model="gpt-4o", temperature=0)


# ─────────────────────────────────────────
# NÓ 0: Onboarding
# Verifica se usuário existe e coleta dados
# ─────────────────────────────────────────
def onboarding_node(state: AgentState) -> AgentState:
    logger.info(f"👋 Verificando onboarding para {state.phone}")

    user = get_user(state.phone)

    # Usuário novo → cria e envia boas-vindas
    if not user:
        create_user(state.phone)
        return AgentState(**{**state.model_dump(), "response": ONBOARDING_WELCOME_PROMPT})

    # Aguardando nome
    if user.onboarding_step == OnboardingStep.WAITING_NAME:
        name = state.message.strip().title()
        update_user_name(state.phone, name)
        response = ONBOARDING_BUDGET_PROMPT.replace("{name}", name)
        return AgentState(**{**state.model_dump(), "response": response})

    # Aguardando orçamento
    if user.onboarding_step == OnboardingStep.WAITING_BUDGET:
        try:
            budget = float(state.message.strip().replace(",", ".").replace("R$", "").strip())
            update_user_budget(state.phone, budget)
            response = ONBOARDING_DONE_PROMPT.replace("{name}", user.name).replace("{budget:.2f}", f"{budget:.2f}")
            return AgentState(**{**state.model_dump(), "response": response})
        except ValueError:
            return AgentState(**{**state.model_dump(), "response": ONBOARDING_INVALID_BUDGET_PROMPT})

    # Onboarding já concluído → segue fluxo normal
    return AgentState(**{**state.model_dump(), "intent": None})


# ─────────────────────────────────────────
# NÓ 1: Classificador
# Decide o que o usuário quer fazer
# ─────────────────────────────────────────
def classifier_node(state: AgentState) -> AgentState:
    logger.info(f"🔍 Classificando mensagem: {state.message}")

    prompt = CLASSIFIER_PROMPT.format(message=state.message)
    response = llm.invoke([HumanMessage(content=prompt)])
    intent = response.content.strip().lower()

    if intent not in ["expense", "income", "query"]:
        intent = MessageIntent.UNKNOWN

    logger.info(f"✅ Intenção detectada: {intent}")
    return AgentState(**{**state.model_dump(), "intent": intent})


# ─────────────────────────────────────────
# NÓ 2: Extrator de texto
# Extrai valor, categoria e descrição da mensagem
# ─────────────────────────────────────────
def extractor_node(state: AgentState) -> AgentState:
    logger.info(f"📦 Extraindo dados da mensagem: {state.message}")

    prompt = EXTRACTOR_PROMPT.replace("{message}", state.message)
    response = llm.invoke([HumanMessage(content=prompt)])

    try:
        raw = response.content.strip()
        logger.info(f"🔍 Resposta bruta do extrator: {raw}")

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        data = json.loads(raw)
        transaction_type = (
            TransactionType.INCOME if state.intent == "income" else TransactionType.EXPENSE
        )
        return AgentState(**{
            **state.model_dump(),
            "amount": data.get("amount", 0.0),
            "category": data.get("category", "Outros"),
            "description": data.get("description", ""),
            "transaction_type": transaction_type,
        })
    except json.JSONDecodeError:
        logger.error(f"❌ Erro ao parsear JSON do extrator: {response.content}")
        return AgentState(**{**state.model_dump(), "amount": 0.0, "category": "Outros"})


# ─────────────────────────────────────────
# NÓ 2B: Extrator de imagem
# Extrai dados financeiros de foto de comprovante
# ─────────────────────────────────────────
def image_extractor_node(state: AgentState) -> AgentState:
    logger.info(f"🖼️ Extraindo dados da imagem: {state.image_url}")

    try:
        response = llm.invoke([
            HumanMessage(content=[
                {"type": "text", "text": IMAGE_EXTRACTOR_PROMPT},
                {"type": "image_url", "image_url": {"url": state.image_url}},
            ])
        ])

        raw = response.content.strip()
        logger.info(f"🔍 Resposta bruta do extrator de imagem: {raw}")

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        data = json.loads(raw)
        return AgentState(**{
            **state.model_dump(),
            "amount": data.get("amount", 0.0),
            "category": data.get("category", "Outros"),
            "description": data.get("description", ""),
            "transaction_type": TransactionType.EXPENSE,
        })

    except Exception as e:
        logger.error(f"❌ Erro ao processar imagem: {e}")
        return AgentState(**{
            **state.model_dump(),
            "amount": 0.0,
            "category": "Outros",
            "description": "erro ao processar imagem",
            "transaction_type": TransactionType.EXPENSE,
        })


# ─────────────────────────────────────────
# NÓ 3: Salvar transação
# Persiste no banco e gera resposta de confirmação
# ─────────────────────────────────────────
def saver_node(state: AgentState) -> AgentState:
    logger.info(f"💾 Salvando transação: {state.amount} - {state.category}")

    save_transaction(
        phone=state.phone,
        type=state.transaction_type,
        amount=state.amount,
        category=state.category,
        description=state.description,
    )

    emoji = "💸" if state.transaction_type == TransactionType.EXPENSE else "💰"
    tipo = "Gasto" if state.transaction_type == TransactionType.EXPENSE else "Entrada"

    response = (
        f"{emoji} *{tipo} registrado!*\n\n"
        f"📌 Categoria: {state.category}\n"
        f"💵 Valor: R$ {state.amount:.2f}\n"
        f"📝 Descrição: {state.description or '-'}"
    )

    return AgentState(**{**state.model_dump(), "response": response})


# ─────────────────────────────────────────
# NÓ 4: Consulta
# Busca resumo no banco e responde o usuário
# ─────────────────────────────────────────
def query_node(state: AgentState) -> AgentState:
    logger.info(f"📊 Consultando resumo para {state.phone}")

    summary = get_summary(phone=state.phone, days=30)

    prompt = QUERY_PROMPT.format(
        total_income=f"{summary['total_income']:.2f}",
        total_expense=f"{summary['total_expense']:.2f}",
        balance=f"{summary['balance']:.2f}",
        expenses_by_category=summary["expenses_by_category"],
        message=state.message,
    )

    response = llm.invoke([HumanMessage(content=prompt)])
    return AgentState(**{**state.model_dump(), "response": response.content.strip()})


# ─────────────────────────────────────────
# NÓ 5: Fallback
# Responde quando não entende a mensagem
# ─────────────────────────────────────────
def fallback_node(state: AgentState) -> AgentState:
    response = (
        "🤖 Não entendi sua mensagem. Tente algo como:\n\n"
        "💸 *Registrar gasto:* \"gastei 45 no ifood\"\n"
        "💰 *Registrar entrada:* \"recebi 3200 de salário\"\n"
        "📊 *Ver resumo:* \"quanto gastei esse mês?\"\n"
        "🖼️ *Comprovante:* envie uma foto do recibo"
    )
    return AgentState(**{**state.model_dump(), "response": response})