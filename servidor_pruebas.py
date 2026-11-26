"""Servidor HTTP controlado para pruebas de integración de VyOps.

Utiliza la aplicación FastAPI real y sustituye exclusivamente
la lógica documental por respuestas deterministas.

No realiza llamadas a Gemini ni requiere acceso al índice vectorial.
"""

from unittest.mock import patch
from uuid import uuid4

import uvicorn

from casos import (
    FUENTE_ESPERADA,
    PREGUNTA_DOCUMENTAL,
)

from servicio.main import app


def responder_simulado(pregunta: str) -> dict:
    """Genera una respuesta documental controlada para las pruebas."""

    trace_id = str(uuid4())

    # La comparación exacta permite comprobar que Pydantic
    # elimina correctamente los espacios exteriores.
    if pregunta == PREGUNTA_DOCUMENTAL:
        return {
            "trace_id": trace_id,
            "respuesta": (
                "El horario de atención presencial los viernes "
                "es de 08:30 a 13:00 horas."
            ),
            "fuentes": [FUENTE_ESPERADA],
            "estado": "respuesta_generada",
        }

    return {
        "trace_id": trace_id,
        "respuesta": "No existe evidencia documental suficiente.",
        "fuentes": [],
        "estado": "abstencion_segura",
    }


def main() -> None:
    """Inicia Uvicorn con la lógica documental sustituida."""

    print("=== SERVIDOR DE PRUEBAS VYOPS ===")
    print("Modo: SIMULADO")
    print("Consumo de Gemini: deshabilitado\n")

    # La sustitución permanece activa mientras funciona el servidor.
    with patch(
        "servicio.logica.responder",
        side_effect=responder_simulado,
    ):
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            log_level="info",
        )


if __name__ == "__main__":
    main()