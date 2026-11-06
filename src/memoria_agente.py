
"""Administración de memoria conversacional temporal para VyOps."""

from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_classic.agents import AgentExecutor

historiales: dict[str, InMemoryChatMessageHistory] = {}


def obtener_historial(session_id: str) -> InMemoryChatMessageHistory:
    """Obtiene o crea el historial asociado a una sesión."""
    if not session_id.strip():
        raise ValueError("El identificador de sesión no puede estar vacío.")

    if session_id not in historiales:
        historiales[session_id] = InMemoryChatMessageHistory()

    return historiales[session_id]


def eliminar_historial(session_id: str) -> None:
    """Elimina el historial temporal de una sesión."""
    historiales.pop(session_id, None)

def construir_agente_con_memoria(
    agente: AgentExecutor,
) -> RunnableWithMessageHistory:
    """Incorpora memoria conversacional por sesión al agente VyOps."""
    return RunnableWithMessageHistory(
        runnable=agente,
        get_session_history=obtener_historial,
        input_messages_key="entrada",
        history_messages_key="chat_history",
        output_messages_key="output",
    )
