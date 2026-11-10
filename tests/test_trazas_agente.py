
"""Pruebas del registro de trazas de VyOps."""

import json
from datetime import datetime

from langchain_core.agents import AgentAction

from src.trazas_agente import (
    marcar_repeticiones_sospechosas,
    registrar_traza,
)


def test_registrar_traza_sin_herramientas(tmp_path) -> None:
    """Registra una ejecución sin herramientas."""
    ruta = tmp_path / "trazas.jsonl"

    registrar_traza(
        session_id="sesion-prueba",
        entrada="Hola, VyOps.",
        resultado={
            "output": "Hola, ¿en qué puedo ayudarte?",
            "intermediate_steps": [],
        },
        ruta_archivo=ruta,
    )

    assert ruta.exists()

    registros = ruta.read_text(encoding="utf-8").splitlines()
    assert len(registros) == 1

    traza = json.loads(registros[0])

    assert traza["session_id"] == "sesion-prueba"
    assert traza["entrada"] == "Hola, VyOps."
    assert traza["acciones"] == []
    assert traza["respuesta_final"] == "Hola, ¿en qué puedo ayudarte?"

    fecha = datetime.fromisoformat(traza["timestamp"])
    assert fecha.tzinfo is not None


def test_registrar_traza_con_herramienta(tmp_path) -> None:
    """Registra la herramienta utilizada y su observación."""
    ruta = tmp_path / "trazas.jsonl"

    accion = AgentAction(
        tool="consultar_estado_solicitud",
        tool_input={"numero_solicitud": "SOL-12345"},
        log="Consulta simulada.",
    )

    registrar_traza(
        session_id="sesion-prueba",
        entrada="Consulta SOL-12345.",
        resultado={
            "output": "La solicitud está en revisión.",
            "intermediate_steps": [
                (accion, {"estado": "en_revision"}),
            ],
        },
        ruta_archivo=ruta,
    )

    traza = json.loads(ruta.read_text(encoding="utf-8"))

    assert len(traza["acciones"]) == 1
    assert traza["acciones"][0]["herramienta"] == (
        "consultar_estado_solicitud"
    )
    assert traza["acciones"][0]["argumentos"] == {
        "numero_solicitud": "SOL-12345"
    }
    assert traza["acciones"][0]["observacion"] == {
        "estado": "en_revision"
    }


def test_registrar_traza_agrega_lineas(tmp_path) -> None:
    """Conserva las ejecuciones anteriores del archivo JSONL."""
    ruta = tmp_path / "trazas.jsonl"

    for numero in range(3):
        registrar_traza(
            session_id=f"sesion-{numero}",
            entrada=f"Consulta {numero}",
            resultado={
                "output": f"Respuesta {numero}",
                "intermediate_steps": [],
            },
            ruta_archivo=ruta,
        )

    registros = ruta.read_text(encoding="utf-8").splitlines()

    assert len(registros) == 3

    sesiones = [
        json.loads(linea)["session_id"]
        for linea in registros
    ]

    assert sesiones == [
        "sesion-0",
        "sesion-1",
        "sesion-2",
    ]

def test_detectar_tres_llamadas_consecutivas(tmp_path) -> None:
    """Detecta tres llamadas consecutivas a la misma herramienta."""
    ruta = tmp_path / "trazas.jsonl"

    acciones = [
        (
            AgentAction(
                tool="consultar_documentacion",
                tool_input={"tema": "permisos"},
                log="Consulta simulada.",
            ),
            {"resultado": "Documento encontrado"},
        )
        for _ in range(3)
    ]

    registrar_traza(
        session_id="sesion-repetitiva",
        entrada="Consulta documentación municipal.",
        resultado={
            "output": "Consulta finalizada.",
            "intermediate_steps": acciones,
        },
        ruta_archivo=ruta,
    )

    alertas = marcar_repeticiones_sospechosas(ruta)

    assert len(alertas) == 1
    assert alertas[0]["session_id"] == "sesion-repetitiva"
    assert alertas[0]["herramienta"] == "consultar_documentacion"
    assert alertas[0]["repeticiones"] == 3


def test_no_alertar_herramientas_diferentes(tmp_path) -> None:
    """No genera alertas por herramientas distintas."""
    ruta = tmp_path / "trazas.jsonl"

    nombres = [
        "consultar_documentacion",
        "calcular_metricas",
        "consultar_estado_solicitud",
    ]

    acciones = [
        (
            AgentAction(
                tool=nombre,
                tool_input={},
                log="Acción simulada.",
            ),
            {"resultado": "correcto"},
        )
        for nombre in nombres
    ]

    registrar_traza(
        session_id="sesion-normal",
        entrada="Ejecutar consultas.",
        resultado={
            "output": "Consultas finalizadas.",
            "intermediate_steps": acciones,
        },
        ruta_archivo=ruta,
    )

    assert marcar_repeticiones_sospechosas(ruta) == []


def test_detector_archivo_inexistente(tmp_path) -> None:
    """Devuelve una lista vacía si no existen trazas."""
    ruta = tmp_path / "inexistente.jsonl"

    alertas = marcar_repeticiones_sospechosas(ruta)

    assert alertas == []
