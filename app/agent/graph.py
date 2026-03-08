import logging
from langgraph.graph import StateGraph, END

from app.agent.state import AgentState, MessageIntent
from app.agent.nodes import (
    classifier_node,
    extractor_node,
    image_extractor_node,
    saver_node,
    query_node,
    fallback_node,
)

logger = logging.getLogger(__name__)


def route(state: AgentState) -> str:
    """Decide qual nó executar após o classificador."""
    if state.intent in [MessageIntent.EXPENSE, "expense", "income"]:
        return "extractor"
    elif state.intent == "query":
        return "query"
    else:
        return "fallback"


def build_graph():
    graph = StateGraph(AgentState)

    # Adiciona os nós
    graph.add_node("classifier", classifier_node)
    graph.add_node("extractor", extractor_node)
    graph.add_node("image_extractor", image_extractor_node)  
    graph.add_node("saver", saver_node)
    graph.add_node("query", query_node)
    graph.add_node("fallback", fallback_node)

    # Define o nó de entrada
    graph.set_entry_point("classifier")

    # Roteamento condicional após o classificador
    graph.add_conditional_edges(
        "classifier",
        route,
        {
            "extractor": "extractor",
            "query": "query",
            "fallback": "fallback",
        }
    )

    # Após extrator de texto → salva no banco
    graph.add_edge("extractor", "saver")

    # Após extrator de imagem → salva no banco
    graph.add_edge("image_extractor", "saver")  

    # Nós finais → END
    graph.add_edge("saver", END)
    graph.add_edge("query", END)
    graph.add_edge("fallback", END)

    return graph.compile()


class FinanceAgent:
    def __init__(self):
        self.graph = build_graph()
        logger.info("🧠 FinanceAgent inicializado!")

    async def process(self, phone: str, message: str) -> str:
        """Processa uma mensagem de texto e retorna a resposta."""
        logger.info(f"📩 Processando mensagem de {phone}: {message}")

        initial_state = AgentState(phone=phone, message=message)
        final_state = self.graph.invoke(initial_state)

        return final_state["response"]

    async def process_image(self, phone: str, image_url: str, caption: str = "") -> str:
        """Processa uma imagem e retorna a resposta."""
        logger.info(f"🖼️ Processando imagem de {phone}: {image_url}")

        initial_state = AgentState(
            phone=phone,
            message=caption or "comprovante",
            image_url=image_url,
            intent="image",  # 👈 pula o classifier e vai direto pro image_extractor
        )
        final_state = self.graph.invoke(initial_state, {"override_entry": "image_extractor"})

        return final_state["response"]