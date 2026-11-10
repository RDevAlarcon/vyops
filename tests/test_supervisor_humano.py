
"""Pruebas del supervisor humano de VyOps."""

from src.supervisor_humano import SupervisorHumano


def test_supervisor_aprueba_cancelacion() -> None:
    """Permite una cancelación simulada aprobada."""
    supervisor = SupervisorHumano(
        solicitar_decision=lambda: True,
    )

    identificador = supervisor.autorizar_cancelacion(
        numero_solicitud="SOL-12345",
    )

    assert identificador is not None
    assert supervisor.verificar_y_consumir(
        identificador,
        "SOL-12345",
    ) is True


def test_supervisor_rechaza_cancelacion() -> None:
    """Bloquea una cancelación rechazada."""
    supervisor = SupervisorHumano(
        solicitar_decision=lambda: False,
    )

    identificador = supervisor.autorizar_cancelacion(
        numero_solicitud="SOL-12345",
    )

    assert identificador is None


def test_supervisor_impide_reutilizar_autorizacion() -> None:
    """Impide utilizar dos veces la misma autorización."""
    supervisor = SupervisorHumano(
        solicitar_decision=lambda: True,
    )

    identificador = supervisor.autorizar_cancelacion(
        numero_solicitud="SOL-12345",
    )

    assert identificador is not None

    assert supervisor.verificar_y_consumir(
        identificador,
        "SOL-12345",
    ) is True

    assert supervisor.verificar_y_consumir(
        identificador,
        "SOL-12345",
    ) is False


def test_supervisor_rechaza_otra_solicitud() -> None:
    """Impide autorizar una solicitud distinta."""
    supervisor = SupervisorHumano(
        solicitar_decision=lambda: True,
    )

    identificador = supervisor.autorizar_cancelacion(
        numero_solicitud="SOL-12345",
    )

    assert identificador is not None

    assert supervisor.verificar_y_consumir(
        identificador,
        "SOL-99999",
    ) is False


def test_supervisor_rechaza_timeout() -> None:
    """Bloquea una autorización con plazo agotado."""
    supervisor = SupervisorHumano(
        solicitar_decision=lambda: True,
    )

    identificador = supervisor.autorizar_cancelacion(
        numero_solicitud="SOL-12345",
        tiempo_limite_segundos=0,
    )

    assert identificador is None
