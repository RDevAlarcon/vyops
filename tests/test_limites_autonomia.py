
"""Pruebas de los límites de autonomía de VyOps."""

import pytest
import time
from time import monotonic
from concurrent.futures import ThreadPoolExecutor

from src.limites_autonomia import (
    NivelRiesgo,
    RIESGOS_HERRAMIENTAS,
    requiere_aprobacion,
    esperar_aprobacion,
    AutorizacionHumana,
    solicitar_autorizacion,
    RegistroAutorizaciones,
)


@pytest.mark.parametrize(
    "herramienta",
    [
        "calcular_metricas",
        "consultar_documentacion",
        "analizar_datos",
        "consultar_estado_solicitud",
    ],
)
def test_herramientas_bajo_riesgo_no_requieren_aprobacion(
    herramienta: str,
) -> None:
    """Verifica que las herramientas de consulta sean de bajo riesgo."""
    assert RIESGOS_HERRAMIENTAS[herramienta] == NivelRiesgo.BAJO
    assert requiere_aprobacion(herramienta) is False


def test_herramienta_alto_riesgo_requiere_aprobacion() -> None:
    """Verifica que una cancelación requiera supervisión humana."""
    herramienta = "cancelar_solicitud_simulada"

    assert RIESGOS_HERRAMIENTAS[herramienta] == NivelRiesgo.ALTO
    assert requiere_aprobacion(herramienta) is True


def test_herramienta_desconocida_requiere_aprobacion() -> None:
    """Impide autorizar automáticamente herramientas desconocidas."""
    assert requiere_aprobacion("herramienta_desconocida") is True

def test_aprobacion_humana_aceptada() -> None:
    """Permite continuar cuando existe aprobación explícita."""
    assert esperar_aprobacion(lambda: True) is True


def test_aprobacion_humana_rechazada() -> None:
    """Bloquea una acción rechazada por el supervisor."""
    assert esperar_aprobacion(lambda: False) is False


def test_aprobacion_humana_invalida() -> None:
    """No acepta valores distintos del booleano True."""
    assert esperar_aprobacion(lambda: "sí") is False


def test_aprobacion_humana_timeout() -> None:
    """Rechaza cuando la aprobación supera el tiempo permitido."""
    def decision_lenta() -> bool:
        time.sleep(0.2)
        return True

    resultado = esperar_aprobacion(
        solicitar_decision=decision_lenta,
        tiempo_limite_segundos=0.01,
    )

    assert resultado is False


def test_aprobacion_humana_tiempo_invalido() -> None:
    """Rechaza un plazo de aprobación no positivo."""
    assert esperar_aprobacion(
        solicitar_decision=lambda: True,
        tiempo_limite_segundos=0,
    ) is False

def test_autorizacion_vigente_es_valida() -> None:
    """Acepta una autorización vigente para la acción correcta."""
    autorizacion = AutorizacionHumana(
        herramienta="cancelar_solicitud_simulada",
        identificador_solicitud="SOL-12345",
        aprobada=True,
        vence_en=monotonic() + 60,
    )

    assert autorizacion.es_valida(
        "cancelar_solicitud_simulada",
        "SOL-12345",
    ) is True


def test_autorizacion_vencida_es_rechazada() -> None:
    """Impide utilizar una autorización cuyo plazo terminó."""
    autorizacion = AutorizacionHumana(
        herramienta="cancelar_solicitud_simulada",
        identificador_solicitud="SOL-12345",
        aprobada=True,
        vence_en=monotonic() - 1,
    )

    assert autorizacion.es_valida(
        "cancelar_solicitud_simulada",
        "SOL-12345",
    ) is False


def test_autorizacion_no_sirve_para_otra_solicitud() -> None:
    """Impide reutilizar la autorización en otra solicitud."""
    autorizacion = AutorizacionHumana(
        herramienta="cancelar_solicitud_simulada",
        identificador_solicitud="SOL-12345",
        aprobada=True,
        vence_en=monotonic() + 60,
    )

    assert autorizacion.es_valida(
        "cancelar_solicitud_simulada",
        "SOL-99999",
    ) is False


def test_autorizacion_no_sirve_para_otra_herramienta() -> None:
    """Impide utilizar la autorización en otra operación."""
    autorizacion = AutorizacionHumana(
        herramienta="cancelar_solicitud_simulada",
        identificador_solicitud="SOL-12345",
        aprobada=True,
        vence_en=monotonic() + 60,
    )

    assert autorizacion.es_valida(
        "modificar_solicitud",
        "SOL-12345",
    ) is False


def test_autorizacion_rechazada_no_es_valida() -> None:
    """Impide ejecutar acciones sin aprobación explícita."""
    autorizacion = AutorizacionHumana(
        herramienta="cancelar_solicitud_simulada",
        identificador_solicitud="SOL-12345",
        aprobada=False,
        vence_en=monotonic() + 60,
    )

    assert autorizacion.es_valida(
        "cancelar_solicitud_simulada",
        "SOL-12345",
    ) is False

def test_solicitar_autorizacion_aprobada() -> None:
    """Genera una autorización válida tras una aprobación explícita."""
    autorizacion = solicitar_autorizacion(
        herramienta="cancelar_solicitud_simulada",
        identificador_solicitud="SOL-12345",
        solicitar_decision=lambda: True,
        tiempo_limite_segundos=60,
    )

    assert autorizacion.es_valida(
        "cancelar_solicitud_simulada",
        "SOL-12345",
    ) is True


def test_solicitar_autorizacion_rechazada() -> None:
    """No autoriza una operación rechazada."""
    autorizacion = solicitar_autorizacion(
        herramienta="cancelar_solicitud_simulada",
        identificador_solicitud="SOL-12345",
        solicitar_decision=lambda: False,
        tiempo_limite_segundos=60,
    )

    assert autorizacion.es_valida(
        "cancelar_solicitud_simulada",
        "SOL-12345",
    ) is False


def test_solicitar_autorizacion_timeout() -> None:
    """No autoriza una aprobación recibida fuera del plazo."""
    def decision_lenta() -> bool:
        time.sleep(0.2)
        return True

    autorizacion = solicitar_autorizacion(
        herramienta="cancelar_solicitud_simulada",
        identificador_solicitud="SOL-12345",
        solicitar_decision=decision_lenta,
        tiempo_limite_segundos=0.01,
    )

    assert autorizacion.es_valida(
        "cancelar_solicitud_simulada",
        "SOL-12345",
    ) is False


def test_solicitar_autorizacion_no_acepta_respuesta_invalida() -> None:
    """Rechaza respuestas que no sean el booleano True."""
    autorizacion = solicitar_autorizacion(
        herramienta="cancelar_solicitud_simulada",
        identificador_solicitud="SOL-12345",
        solicitar_decision=lambda: "aprobado",
        tiempo_limite_segundos=60,
    )

    assert autorizacion.es_valida(
        "cancelar_solicitud_simulada",
        "SOL-12345",
    ) is False

def test_registro_permite_consumir_autorizacion() -> None:
    """Permite consumir una autorización válida una sola vez."""
    registro = RegistroAutorizaciones()

    autorizacion = AutorizacionHumana(
        herramienta="cancelar_solicitud_simulada",
        identificador_solicitud="SOL-12345",
        aprobada=True,
        vence_en=monotonic() + 60,
    )

    identificador = registro.registrar(autorizacion)

    assert registro.consumir(
        identificador,
        "cancelar_solicitud_simulada",
        "SOL-12345",
    ) is True


def test_registro_impide_reutilizar_autorizacion() -> None:
    """Rechaza una autorización que ya fue consumida."""
    registro = RegistroAutorizaciones()

    autorizacion = AutorizacionHumana(
        herramienta="cancelar_solicitud_simulada",
        identificador_solicitud="SOL-12345",
        aprobada=True,
        vence_en=monotonic() + 60,
    )

    identificador = registro.registrar(autorizacion)

    assert registro.consumir(
        identificador,
        "cancelar_solicitud_simulada",
        "SOL-12345",
    ) is True

    assert registro.consumir(
        identificador,
        "cancelar_solicitud_simulada",
        "SOL-12345",
    ) is False


def test_registro_rechaza_identificador_desconocido() -> None:
    """Rechaza identificadores que no están registrados."""
    registro = RegistroAutorizaciones()

    assert registro.consumir(
        "identificador_inexistente",
        "cancelar_solicitud_simulada",
        "SOL-12345",
    ) is False


def test_registro_rechaza_otra_solicitud() -> None:
    """Impide utilizar una autorización para otra solicitud."""
    registro = RegistroAutorizaciones()

    autorizacion = AutorizacionHumana(
        herramienta="cancelar_solicitud_simulada",
        identificador_solicitud="SOL-12345",
        aprobada=True,
        vence_en=monotonic() + 60,
    )

    identificador = registro.registrar(autorizacion)

    assert registro.consumir(
        identificador,
        "cancelar_solicitud_simulada",
        "SOL-99999",
    ) is False


def test_registro_rechaza_autorizacion_vencida() -> None:
    """Impide consumir una autorización fuera de plazo."""
    registro = RegistroAutorizaciones()

    autorizacion = AutorizacionHumana(
        herramienta="cancelar_solicitud_simulada",
        identificador_solicitud="SOL-12345",
        aprobada=True,
        vence_en=monotonic() - 1,
    )

    identificador = registro.registrar(autorizacion)

    assert registro.consumir(
        identificador,
        "cancelar_solicitud_simulada",
        "SOL-12345",
    ) is False

def test_registro_impide_consumo_concurrente() -> None:
    """Permite consumir una autorización solo una vez entre varios hilos."""
    registro = RegistroAutorizaciones()

    autorizacion = AutorizacionHumana(
        herramienta="cancelar_solicitud_simulada",
        identificador_solicitud="SOL-12345",
        aprobada=True,
        vence_en=monotonic() + 60,
    )

    identificador = registro.registrar(autorizacion)

    def intentar_consumir() -> bool:
        return registro.consumir(
            identificador,
            "cancelar_solicitud_simulada",
            "SOL-12345",
        )

    with ThreadPoolExecutor(max_workers=10) as ejecutor:
        resultados = list(
            ejecutor.map(
                lambda _: intentar_consumir(),
                range(10),
            )
        )

    assert resultados.count(True) == 1
    assert resultados.count(False) == 9
