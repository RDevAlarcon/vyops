"""Registro de costos estimados por sesión para VyOps.

Mantiene el historial de operaciones de una sesión de forma aislada.
Los importes se expresan en dólares estadounidenses (USD).
"""

import math


class RegistroCostosSesion:
    """Acumula los costos estimados de una sesión."""

    def __init__(self):
        """Inicializa una sesión sin operaciones registradas."""
        self._operaciones = []

    def registrar_operacion(self, costo_usd: float) -> None:
        """Registra el costo estimado de una operación exitosa."""
        if (
            isinstance(costo_usd, bool)
            or not isinstance(costo_usd, (int, float))
            or not math.isfinite(costo_usd)
            or costo_usd < 0
        ):
            raise ValueError(
                "El costo debe ser un número finito no negativo."
            )

        self._operaciones.append(float(costo_usd))

    def obtener_total(self) -> float:
        """Devuelve el costo acumulado de la sesión en USD."""
        return math.fsum(self._operaciones)

    def obtener_operaciones(self) -> list[float]:
        """Devuelve una copia de los costos registrados."""
        return self._operaciones.copy()
