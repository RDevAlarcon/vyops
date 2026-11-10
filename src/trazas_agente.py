
"""Registro de trazas de ejecución del agente VyOps."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def registrar_traza(
    session_id: str,
    entrada: str,
    resultado: dict[str, Any],
    ruta_archivo: str | Path = "trazas_agente.jsonl",
) -> None:
    """Registra las herramientas utilizadas y la respuesta del agente."""
    acciones = []

    for accion, observacion in resultado.get("intermediate_steps", []):
        acciones.append(
            {
                "herramienta": accion.tool,
                "argumentos": accion.tool_input,
                "observacion": observacion,
            }
        )

    traza = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "entrada": entrada,
        "acciones": acciones,
        "respuesta_final": resultado.get("output", ""),
    }

    ruta = Path(ruta_archivo)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    with ruta.open("a", encoding="utf-8") as archivo:
        archivo.write(
            json.dumps(traza, ensure_ascii=False, default=str) + "\n"
        )

def marcar_repeticiones_sospechosas(
    ruta_archivo: str | Path = "trazas_agente.jsonl",
    umbral: int = 3,
) -> list[dict[str, Any]]:
    """Detecta llamadas consecutivas repetidas a una herramienta."""
    if umbral < 2:
        raise ValueError("El umbral debe ser al menos 2.")

    ruta = Path(ruta_archivo)

    if not ruta.exists():
        return []

    alertas: list[dict[str, Any]] = []

    with ruta.open("r", encoding="utf-8") as archivo:
        for numero_linea, linea in enumerate(archivo, start=1):
            if not linea.strip():
                continue

            traza = json.loads(linea)
            acciones = traza.get("acciones", [])

            herramienta_anterior: str | None = None
            repeticiones = 0

            for accion in acciones:
                herramienta = accion.get("herramienta")

                if herramienta == herramienta_anterior:
                    repeticiones += 1
                else:
                    herramienta_anterior = herramienta
                    repeticiones = 1

                if repeticiones == umbral:
                    alertas.append(
                        {
                            "linea": numero_linea,
                            "session_id": traza.get("session_id"),
                            "herramienta": herramienta,
                            "repeticiones": repeticiones,
                        }
                    )

    return alertas
