
"""Pruebas de la memoria conversacional temporal de VyOps."""

import pytest

from src.memoria_agente import (
    eliminar_historial,
    obtener_historial,
)
from langchain_core.runnables import RunnableLambda
from src.memoria_agente import construir_agente_con_memoria
from langchain_core.messages import AIMessage
from langchain_core.tools import tool

from src.agente_con_herramientas import construir_agente_municipal
from tests.test_agente_con_herramientas import FakeToolCallingModel

def test_sesiones_tienen_historiales_independientes() -> None:
    """Verifica que dos sesiones no compartan historial."""
    primera = obtener_historial("prueba_usuario_001")
    segunda = obtener_historial("prueba_usuario_002")

    try:
        primera.add_user_message("Mi solicitud es SOL-12345.")

        assert primera is not segunda
        assert len(primera.messages) == 1
        assert len(segunda.messages) == 0
    finally:
        eliminar_historial("prueba_usuario_001")
        eliminar_historial("prueba_usuario_002")


def test_misma_sesion_reutiliza_historial() -> None:
    """Verifica que una sesión conserve sus mensajes."""
    session_id = "prueba_reutilizacion"

    try:
        historial = obtener_historial(session_id)
        historial.add_user_message("Hola, soy un vecino.")

        recuperado = obtener_historial(session_id)

        assert recuperado is historial
        assert len(recuperado.messages) == 1
        assert recuperado.messages[0].content == "Hola, soy un vecino."
    finally:
        eliminar_historial(session_id)


def test_eliminar_historial_reinicia_sesion() -> None:
    """Verifica que eliminar una sesión borre su historial."""
    session_id = "prueba_eliminacion"

    try:
        historial = obtener_historial(session_id)
        historial.add_user_message("Mensaje temporal.")

        eliminar_historial(session_id)

        nuevo_historial = obtener_historial(session_id)

        assert nuevo_historial is not historial
        assert len(nuevo_historial.messages) == 0
    finally:
        eliminar_historial(session_id)


def test_rechaza_identificador_vacio() -> None:
    """Verifica que una sesión necesite un identificador válido."""
    with pytest.raises(ValueError):
        obtener_historial("   ")

def test_memoria_conserva_conversacion() -> None:
    """Verifica que una sesión recuerde mensajes anteriores."""
    session_id = "prueba_conversacion"

    def responder(datos: dict) -> dict:
        historial = datos.get("chat_history", [])
        return {
            "output": f"Mensajes anteriores: {len(historial)}"
        }

    agente_simulado = RunnableLambda(responder)
    agente_con_memoria = construir_agente_con_memoria(
        agente_simulado
    )

    configuracion = {
        "configurable": {
            "session_id": session_id,
        }
    }

    try:
        primera = agente_con_memoria.invoke(
            {"entrada": "Hola, soy un vecino."},
            config=configuracion,
        )

        segunda = agente_con_memoria.invoke(
            {"entrada": "¿Recuerdas mi mensaje anterior?"},
            config=configuracion,
        )

        assert primera["output"] == "Mensajes anteriores: 0"
        assert segunda["output"] == "Mensajes anteriores: 2"

        historial = obtener_historial(session_id)

        assert len(historial.messages) == 4
        assert historial.messages[0].content == (
            "Hola, soy un vecino."
        )
    finally:
        eliminar_historial(session_id)

def test_memoria_aisla_sesiones() -> None:
    """Verifica que las conversaciones no se mezclen entre sesiones."""
    def responder(datos: dict) -> dict:
        historial = datos.get("chat_history", [])
        return {
            "output": f"Mensajes anteriores: {len(historial)}"
        }

    agente_simulado = RunnableLambda(responder)
    agente_con_memoria = construir_agente_con_memoria(
        agente_simulado
    )

    sesion_a = "prueba_aislamiento_a"
    sesion_b = "prueba_aislamiento_b"

    try:
        configuracion_a = {
            "configurable": {"session_id": sesion_a}
        }
        configuracion_b = {
            "configurable": {"session_id": sesion_b}
        }

        agente_con_memoria.invoke(
            {"entrada": "Mi solicitud es SOL-12345."},
            config=configuracion_a,
        )

        respuesta_a = agente_con_memoria.invoke(
            {"entrada": "¿Recuerdas mi solicitud?"},
            config=configuracion_a,
        )

        respuesta_b = agente_con_memoria.invoke(
            {"entrada": "¿Qué mensajes anteriores tengo?"},
            config=configuracion_b,
        )

        assert respuesta_a["output"] == "Mensajes anteriores: 2"
        assert respuesta_b["output"] == "Mensajes anteriores: 0"

        historial_a = obtener_historial(sesion_a)
        historial_b = obtener_historial(sesion_b)

        assert len(historial_a.messages) == 4
        assert len(historial_b.messages) == 2

        assert "SOL-12345" in historial_a.messages[0].content
        assert "SOL-12345" not in str(historial_b.messages)
    finally:
        eliminar_historial(sesion_a)
        eliminar_historial(sesion_b)

def test_agente_municipal_con_memoria() -> None:
    """Verifica herramientas y memoria en una misma sesión."""
    session_id = "prueba_agente_municipal"

    modelo_simulado = FakeToolCallingModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "consultar_estado_solicitud",
                        "args": {
                            "numero_solicitud": "SOL-12345",
                            "incluir_historial": True,
                        },
                        "id": "consulta_municipal_1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(
                content=(
                    "La solicitud SOL-12345 está en revisión "
                    "por la unidad municipal."
                )
            ),
            AIMessage(
                content=(
                    "Sí, anteriormente consultaste "
                    "la solicitud SOL-12345."
                )
            ),
        ]
    )

    agente = construir_agente_municipal(
        modelo=modelo_simulado
    )
    agente_con_memoria = construir_agente_con_memoria(agente)

    configuracion = {
        "configurable": {
            "session_id": session_id,
        }
    }

    try:
        primera = agente_con_memoria.invoke(
            {
                "entrada": (
                    "Consulta el estado y el historial "
                    "de la solicitud SOL-12345."
                )
            },
            config=configuracion,
        )

        segunda = agente_con_memoria.invoke(
            {
                "entrada": (
                    "¿Recuerdas qué solicitud consulté?"
                )
            },
            config=configuracion,
        )

        assert "SOL-12345" in primera["output"]
        assert "SOL-12345" in segunda["output"]

        assert len(primera["intermediate_steps"]) == 1

        accion, observacion = primera["intermediate_steps"][0]

        assert accion.tool == "consultar_estado_solicitud"
        assert "Solicitud recibida." in observacion

        historial = obtener_historial(session_id)

        assert len(historial.messages) == 4
        assert historial.messages[0].content.startswith(
            "Consulta el estado"
        )
        assert "SOL-12345" in historial.messages[1].content
        assert historial.messages[2].content == (
            "¿Recuerdas qué solicitud consulté?"
        )
    finally:
        eliminar_historial(session_id)
