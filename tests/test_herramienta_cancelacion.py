
"""Pruebas de la herramienta LangChain de cancelación simulada."""

from src.herramienta_cancelacion import (
    construir_herramienta_cancelacion,
)


def test_herramienta_expone_solo_numero_solicitud() -> None:
    """Impide que el modelo proporcione autorizaciones."""
    herramienta = construir_herramienta_cancelacion(
        solicitar_decision=lambda: False,
    )

    assert herramienta.name == "cancelar_solicitud_simulada"
    assert set(herramienta.args) == {"numero_solicitud"}


def test_herramienta_permite_cancelacion_aprobada() -> None:
    """Simula una cancelación con aprobación externa."""
    herramienta = construir_herramienta_cancelacion(
        solicitar_decision=lambda: True,
    )

    resultado = herramienta.invoke({
        "numero_solicitud": "SOL-12345",
    })

    assert resultado["estado"] == "simulada"
    assert resultado["numero_solicitud"] == "SOL-12345"


def test_herramienta_bloquea_cancelacion_rechazada() -> None:
    """Bloquea una operación rechazada por el supervisor."""
    herramienta = construir_herramienta_cancelacion(
        solicitar_decision=lambda: False,
    )

    resultado = herramienta.invoke({
        "numero_solicitud": "SOL-12345",
    })

    assert resultado["estado"] == "bloqueada"


def test_herramienta_solicita_aprobacion_por_operacion() -> None:
    """Solicita una decisión nueva para cada cancelación."""
    decisiones = iter([True, False])

    herramienta = construir_herramienta_cancelacion(
        solicitar_decision=lambda: next(decisiones),
    )

    primera = herramienta.invoke({
        "numero_solicitud": "SOL-12345",
    })

    segunda = herramienta.invoke({
        "numero_solicitud": "SOL-99999",
    })

    assert primera["estado"] == "simulada"
    assert segunda["estado"] == "bloqueada"


def test_herramienta_bloquea_error_del_supervisor() -> None:
    """Rechaza la operación cuando falla la aprobación."""
    def decision_con_error() -> bool:
        raise RuntimeError("Supervisor no disponible")

    herramienta = construir_herramienta_cancelacion(
        solicitar_decision=decision_con_error,
    )

    resultado = herramienta.invoke({
        "numero_solicitud": "SOL-12345",
    })

    assert resultado["estado"] == "bloqueada"
