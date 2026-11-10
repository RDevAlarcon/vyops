
"""Pruebas de cancelación municipal simulada."""

from src.cancelacion_simulada import cancelar_solicitud_simulada
from src.supervisor_humano import SupervisorHumano


def test_cancelacion_autorizada() -> None:
    """Permite simular una cancelación aprobada."""
    supervisor = SupervisorHumano(lambda: True)
    autorizacion = supervisor.autorizar_cancelacion("SOL-12345")

    resultado = cancelar_solicitud_simulada(
        "SOL-12345",
        supervisor,
        autorizacion,
    )

    assert resultado["estado"] == "simulada"
    assert resultado["numero_solicitud"] == "SOL-12345"


def test_cancelacion_sin_autorizacion() -> None:
    """Bloquea una cancelación sin autorización humana."""
    supervisor = SupervisorHumano(lambda: True)

    resultado = cancelar_solicitud_simulada(
        "SOL-12345",
        supervisor,
        None,
    )

    assert resultado["estado"] == "bloqueada"


def test_cancelacion_rechazada_por_supervisor() -> None:
    """Bloquea una operación rechazada por el supervisor."""
    supervisor = SupervisorHumano(lambda: False)
    autorizacion = supervisor.autorizar_cancelacion("SOL-12345")

    resultado = cancelar_solicitud_simulada(
        "SOL-12345",
        supervisor,
        autorizacion,
    )

    assert resultado["estado"] == "bloqueada"


def test_cancelacion_no_reutiliza_autorizacion() -> None:
    """Impide ejecutar dos cancelaciones con una autorización."""
    supervisor = SupervisorHumano(lambda: True)
    autorizacion = supervisor.autorizar_cancelacion("SOL-12345")

    primero = cancelar_solicitud_simulada(
        "SOL-12345",
        supervisor,
        autorizacion,
    )

    segundo = cancelar_solicitud_simulada(
        "SOL-12345",
        supervisor,
        autorizacion,
    )

    assert primero["estado"] == "simulada"
    assert segundo["estado"] == "bloqueada"


def test_cancelacion_no_autoriza_otra_solicitud() -> None:
    """Impide cancelar una solicitud distinta de la autorizada."""
    supervisor = SupervisorHumano(lambda: True)
    autorizacion = supervisor.autorizar_cancelacion("SOL-12345")

    resultado = cancelar_solicitud_simulada(
        "SOL-99999",
        supervisor,
        autorizacion,
    )

    assert resultado["estado"] == "bloqueada"


def test_cancelacion_rechaza_numero_vacio() -> None:
    """Rechaza solicitudes sin identificador."""
    supervisor = SupervisorHumano(lambda: True)

    resultado = cancelar_solicitud_simulada(
        "",
        supervisor,
        None,
    )

    assert resultado["estado"] == "rechazada"
