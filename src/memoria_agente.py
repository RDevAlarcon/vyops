
"""Memoria conversacional temporal de VyOps con LangGraph."""

from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages


class EstadoMemoria(TypedDict):
    """Estado persistente de mensajes por sesión."""

    messages: Annotated[list[BaseMessage], add_messages]


class HistorialSesion:
    """Interfaz de consulta y actualización del historial."""

    def __init__(self, session_id: str, grafo: Runnable):
        self.session_id = session_id
        self._grafo = grafo

    @property
    def messages(self) -> list[BaseMessage]:
        """Obtiene los mensajes almacenados."""
        estado = self._grafo.get_state(
            {"configurable": {"thread_id": self.session_id}}
        )
        return list(estado.values.get("messages", []))

    def add_user_message(self, contenido: str) -> None:
        """Agrega un mensaje del usuario."""
        self.agregar_mensajes([HumanMessage(content=contenido)])

    def agregar_mensajes(self, mensajes: list[BaseMessage]) -> None:
        """Guarda mensajes en el checkpoint de la sesión."""
        self._grafo.invoke(
            {"messages": mensajes},
            config={"configurable": {"thread_id": self.session_id}},
        )


class EstadoAgente(TypedDict, total=False):
    """Entradas y resultados del agente municipal."""

    entrada: str
    output: str
    intermediate_steps: list


checkpointer = InMemorySaver()
historiales: dict[str, HistorialSesion] = {}


def _crear_grafo_memoria():
    """Construye el grafo de persistencia conversacional."""

    def conservar(estado: EstadoMemoria) -> dict:
        return {}

    builder = StateGraph(EstadoMemoria)
    builder.add_node("conservar", conservar)
    builder.add_edge(START, "conservar")
    builder.add_edge("conservar", END)

    return builder.compile(checkpointer=checkpointer)


grafo_memoria = _crear_grafo_memoria()


def obtener_historial(session_id: str) -> HistorialSesion:
    """Obtiene o crea el historial de una sesión."""
    if not isinstance(session_id, str) or not session_id.strip():
        raise ValueError("El identificador de sesión no puede estar vacío.")

    if session_id not in historiales:
        historiales[session_id] = HistorialSesion(
            session_id, grafo_memoria
        )

    return historiales[session_id]


def eliminar_historial(session_id: str) -> None:
    """Elimina el historial y los checkpoints de una sesión."""
    historiales.pop(session_id, None)
    checkpointer.delete_thread(session_id)


def construir_agente_con_memoria(agente: Runnable):
    """Integra el agente municipal con memoria por sesión."""

    def ejecutar(estado: EstadoAgente, config: RunnableConfig):
        session_id = config.get("configurable", {}).get("session_id")
        historial = obtener_historial(session_id)

        anteriores = historial.messages

        resultado = agente.invoke(
            {
                "entrada": estado["entrada"],
                "chat_history": anteriores,
            }
        )

        historial.agregar_mensajes(
            [
                HumanMessage(content=estado["entrada"]),
                AIMessage(content=resultado["output"]),
            ]
        )

        return {
            "output": resultado["output"],
            "intermediate_steps": resultado.get(
                "intermediate_steps", []
            ),
        }

    builder = StateGraph(EstadoAgente)
    builder.add_node("agente", ejecutar)
    builder.add_edge(START, "agente")
    builder.add_edge("agente", END)

    return builder.compile()
