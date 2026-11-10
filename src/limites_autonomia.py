
"""Clasificación de riesgos y límites de autonomía de VyOps."""
from dataclasses import dataclass
from time import monotonic
from enum import Enum
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from threading import Lock
from uuid import uuid4

class NivelRiesgo(str, Enum):
    """Niveles de riesgo de las herramientas del agente."""

    BAJO = "bajo"
    MEDIO = "medio"
    ALTO = "alto"


RIESGOS_HERRAMIENTAS: dict[str, NivelRiesgo] = {
    "calcular_metricas": NivelRiesgo.BAJO,
    "consultar_documentacion": NivelRiesgo.BAJO,
    "analizar_datos": NivelRiesgo.BAJO,
    "consultar_estado_solicitud": NivelRiesgo.BAJO,
    "cancelar_solicitud_simulada": NivelRiesgo.ALTO,
}


def requiere_aprobacion(herramienta: str) -> bool:
    """Determina si una herramienta necesita aprobación humana."""
    nivel = RIESGOS_HERRAMIENTAS.get(herramienta)

    # Una herramienta desconocida nunca obtiene autorización implícita.
    if nivel is None:
        return True

    return nivel == NivelRiesgo.ALTO

def esperar_aprobacion(
    solicitar_decision: Callable[[], bool],
    tiempo_limite_segundos: float = 300,
) -> bool:
    """Espera una decisión humana y rechaza si vence el plazo."""
    if tiempo_limite_segundos <= 0:
        return False

    ejecutor = ThreadPoolExecutor(max_workers=1)

    try:
        tarea = ejecutor.submit(solicitar_decision)

        try:
            decision = tarea.result(timeout=tiempo_limite_segundos)
            return decision is True
        except (FutureTimeoutError, Exception):
            return False
    finally:
        ejecutor.shutdown(wait=False, cancel_futures=True)

@dataclass(frozen=True)
class AutorizacionHumana:
    """Representa una autorización limitada a una acción concreta."""

    herramienta: str
    identificador_solicitud: str
    aprobada: bool
    vence_en: float

    def es_valida(
        self,
        herramienta: str,
        identificador_solicitud: str,
    ) -> bool:
        """Verifica aprobación, alcance y vigencia."""
        return (
            self.aprobada is True
            and self.herramienta == herramienta
            and self.identificador_solicitud == identificador_solicitud
            and monotonic() < self.vence_en
        )

def solicitar_autorizacion(
    herramienta: str,
    identificador_solicitud: str,
    solicitar_decision: Callable[[], bool],
    tiempo_limite_segundos: float = 300,
) -> AutorizacionHumana:
    """Solicita aprobación y genera una autorización temporal."""
    inicio = monotonic()

    aprobada = esperar_aprobacion(
        solicitar_decision=solicitar_decision,
        tiempo_limite_segundos=tiempo_limite_segundos,
    )

    vence_en = inicio + max(0, tiempo_limite_segundos)

    return AutorizacionHumana(
        herramienta=herramienta,
        identificador_solicitud=identificador_solicitud,
        aprobada=aprobada and monotonic() < vence_en,
        vence_en=vence_en,
    )

class RegistroAutorizaciones:
    """Administra autorizaciones temporales de un solo uso."""

    def __init__(self) -> None:
        self._autorizaciones: dict[str, AutorizacionHumana] = {}
        self._lock = Lock()

    def registrar(self, autorizacion: AutorizacionHumana) -> str:
        """Registra una autorización y devuelve un identificador opaco."""
        identificador = uuid4().hex

        with self._lock:
            self._autorizaciones[identificador] = autorizacion

        return identificador

    def consumir(
        self,
        identificador: str,
        herramienta: str,
        identificador_solicitud: str,
    ) -> bool:
        """Valida y consume una autorización de forma atómica."""
        with self._lock:
            autorizacion = self._autorizaciones.pop(
                identificador,
                None,
            )

        if autorizacion is None:
            return False

        return autorizacion.es_valida(
            herramienta,
            identificador_solicitud,
        )
