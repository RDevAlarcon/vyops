
"""Supervisión humana externa al agente VyOps."""

from collections.abc import Callable

from src.limites_autonomia import (
    RegistroAutorizaciones,
    solicitar_autorizacion,
)


class SupervisorHumano:
    """Gestiona decisiones humanas para operaciones simuladas."""

    def __init__(
        self,
        solicitar_decision: Callable[[], bool],
    ) -> None:
        self._solicitar_decision = solicitar_decision
        self._registro = RegistroAutorizaciones()

    def autorizar_cancelacion(
        self,
        numero_solicitud: str,
        tiempo_limite_segundos: float = 300,
    ) -> str | None:
        """Solicita aprobación para una cancelación concreta."""
        autorizacion = solicitar_autorizacion(
            herramienta="cancelar_solicitud_simulada",
            identificador_solicitud=numero_solicitud,
            solicitar_decision=self._solicitar_decision,
            tiempo_limite_segundos=tiempo_limite_segundos,
        )

        if not autorizacion.es_valida(
            "cancelar_solicitud_simulada",
            numero_solicitud,
        ):
            return None

        return self._registro.registrar(autorizacion)

    def verificar_y_consumir(
        self,
        identificador: str,
        numero_solicitud: str,
    ) -> bool:
        """Consume una autorización para la solicitud indicada."""
        return self._registro.consumir(
            identificador=identificador,
            herramienta="cancelar_solicitud_simulada",
            identificador_solicitud=numero_solicitud,
        )
