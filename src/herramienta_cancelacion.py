
"""Herramienta de cancelación ficticia con supervisión externa."""

from collections.abc import Callable

from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field

from src.cancelacion_simulada import cancelar_solicitud_simulada
from src.supervisor_humano import SupervisorHumano


class ArgumentosCancelacion(BaseModel):
    """Argumentos que puede proporcionar el agente."""

    numero_solicitud: str = Field(
        min_length=1,
        description="Número de solicitud municipal ficticia.",
    )


def construir_herramienta_cancelacion(
    solicitar_decision: Callable[[], bool],
) -> BaseTool:
    """Construye una herramienta con aprobación externa."""

    supervisor = SupervisorHumano(
        solicitar_decision=solicitar_decision,
    )

    @tool(
        "cancelar_solicitud_simulada",
        args_schema=ArgumentosCancelacion,
    )
    def herramienta_cancelacion(
        numero_solicitud: str,
    ) -> dict[str, str]:
        """Simula cancelar una solicitud con aprobación humana."""
        autorizacion = supervisor.autorizar_cancelacion(
            numero_solicitud=numero_solicitud,
        )

        return cancelar_solicitud_simulada(
            numero_solicitud=numero_solicitud,
            supervisor=supervisor,
            identificador_autorizacion=autorizacion,
        )

    return herramienta_cancelacion
