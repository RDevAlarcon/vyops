"""Pruebas del manejo de errores con LangChain.

Bloque 20 de SkillNest.
"""

from langchain_core.runnables import RunnableLambda

from src.manejo_errores_langchain import construir_cadena_con_fallback


def test_fallback_se_activa_si_falla_cadena_principal() -> None:
    """Verifica que se utiliza el fallback ante una excepción."""

    def cadena_con_error(datos: dict) -> str:
        """Simula un fallo durante el procesamiento."""
        raise RuntimeError("Error simulado del modelo")

    modelo_simulado = RunnableLambda(cadena_con_error)

    cadena = construir_cadena_con_fallback(modelo_simulado)

    resultado = cadena.invoke({
        "mensaje": "¿Cómo puedo solicitar un permiso municipal?"
    })

    assert resultado == (
        "No fue posible procesar tu solicitud en este momento. "
        "Por favor, intenta nuevamente más tarde."
    )

def test_fallback_no_se_activa_si_cadena_funciona() -> None:
    """Verifica que una ejecución exitosa no active el fallback."""

    def cadena_exitosa(datos: dict) -> str:
        """Simula una respuesta correcta del modelo."""
        return "Solicitud procesada correctamente."

    modelo_simulado = RunnableLambda(cadena_exitosa)

    cadena = construir_cadena_con_fallback(modelo_simulado)

    resultado = cadena.invoke({
        "mensaje": "¿Cómo puedo obtener una patente comercial?"
    })

    assert resultado == "Solicitud procesada correctamente."

def test_ejecutar_cadena_segura_registra_error(caplog) -> None:
    """Verifica que se registre un error sin exponerlo al usuario."""
    import logging

    from src.manejo_errores_langchain import ejecutar_cadena_segura

    def cadena_con_error(datos: dict) -> str:
        """Simula un fallo inesperado del modelo."""
        raise RuntimeError("Error interno simulado")

    cadena = RunnableLambda(cadena_con_error)

    with caplog.at_level(logging.ERROR):
        resultado = ejecutar_cadena_segura(
            cadena,
            {"mensaje": "Necesito consultar un permiso municipal."},
        )

    assert resultado == (
        "No fue posible completar tu solicitud. "
        "Por favor, intenta nuevamente más tarde."
    )

    assert "Ocurrió un error al ejecutar la cadena LangChain." in caplog.text
    assert "Error interno simulado" in caplog.text
    assert "Error interno simulado" not in resultado

def test_ejecutar_cadena_segura_sin_errores(caplog) -> None:
    """Verifica que una ejecución exitosa conserve su respuesta."""
    import logging

    from src.manejo_errores_langchain import ejecutar_cadena_segura

    def cadena_exitosa(datos: dict) -> str:
        """Simula una respuesta correcta del modelo."""
        return "El procedimiento fue consultado correctamente."

    cadena = RunnableLambda(cadena_exitosa)

    with caplog.at_level(logging.ERROR):
        resultado = ejecutar_cadena_segura(
            cadena,
            {"mensaje": "¿Cómo solicito un permiso municipal?"},
        )

    assert resultado == "El procedimiento fue consultado correctamente."
    assert caplog.records == []

def test_fallback_enrutamiento_conserva_mensaje() -> None:
    """Verifica que el fallback conserve el mensaje original."""
    from src.manejo_errores_langchain import (
        construir_fallback_enrutamiento,
    )

    mensaje = "¿Qué documentos necesito para solicitar un permiso?"

    fallback = construir_fallback_enrutamiento()

    resultado = fallback.invoke({"mensaje": mensaje})

    assert resultado == {
        "mensaje": mensaje,
        "categoria": "error",
        "respuesta": (
            "No fue posible procesar tu solicitud en este momento. "
            "Por favor, intenta nuevamente más tarde."
        ),
    }

def test_enrutamiento_seguro_recupera_error_clasificacion() -> None:
    """Verifica que un fallo de clasificación active el fallback."""
    from unittest.mock import MagicMock

    from src.manejo_errores_langchain import (
        construir_enrutamiento_seguro,
    )

    def modelo_con_error(entrada: object) -> str:
        """Simula un error del modelo durante la clasificación."""
        raise RuntimeError("Fallo simulado de Gemini")

    modelo_simulado = MagicMock(side_effect=modelo_con_error)

    cadena = construir_enrutamiento_seguro(
        RunnableLambda(modelo_simulado)
    )

    mensaje = "¿Qué documentos necesito para abrir un negocio?"

    resultado = cadena.invoke({"mensaje": mensaje})

    assert resultado["mensaje"] == mensaje
    assert resultado["categoria"] == "error"
    assert resultado["respuesta"] == (
        "No fue posible procesar tu solicitud en este momento. "
        "Por favor, intenta nuevamente más tarde."
    )

    # El fallo ocurre durante la primera llamada al modelo.
    assert modelo_simulado.call_count == 1

def test_enrutamiento_seguro_recupera_error_respuesta() -> None:
    """Verifica que un fallo posterior a la clasificación active el fallback."""
    from unittest.mock import MagicMock

    from langchain_core.messages import AIMessage

    from src.manejo_errores_langchain import (
        construir_enrutamiento_seguro,
    )

    def modelo_con_fallo_en_respuesta(entrada: object) -> AIMessage:
        """Clasifica correctamente, pero falla al generar la respuesta."""
        if modelo_simulado.call_count == 1:
            return AIMessage(content="pregunta")

        raise RuntimeError("Fallo simulado al generar respuesta")

    modelo_simulado = MagicMock(
        side_effect=modelo_con_fallo_en_respuesta
    )

    cadena = construir_enrutamiento_seguro(
        RunnableLambda(modelo_simulado)
    )

    mensaje = "¿Cómo solicito una patente comercial?"

    resultado = cadena.invoke({"mensaje": mensaje})

    assert resultado["mensaje"] == mensaje
    assert resultado["categoria"] == "error"
    assert resultado["respuesta"] == (
        "No fue posible procesar tu solicitud en este momento. "
        "Por favor, intenta nuevamente más tarde."
    )

    # Una llamada clasifica y la segunda intenta responder.
    assert modelo_simulado.call_count == 2

def test_enrutamiento_seguro_conserva_respuesta_exitosa() -> None:
    """Verifica que una ejecución correcta no active el fallback."""
    from unittest.mock import MagicMock

    from langchain_core.messages import AIMessage

    from src.manejo_errores_langchain import (
        construir_enrutamiento_seguro,
    )

    modelo_simulado = MagicMock(
        side_effect=[
            AIMessage(content="pregunta"),
            AIMessage(content="Estos son los pasos del procedimiento."),
        ]
    )

    cadena = construir_enrutamiento_seguro(
        RunnableLambda(modelo_simulado)
    )

    mensaje = "¿Cómo puedo realizar un trámite municipal?"

    resultado = cadena.invoke({"mensaje": mensaje})

    assert resultado == {
        "mensaje": mensaje,
        "categoria": "pregunta",
        "respuesta": "Estos son los pasos del procedimiento.",
    }

    assert modelo_simulado.call_count == 2

def test_enrutamiento_seguro_registra_error(caplog) -> None:
    """Verifica el registro de errores del enrutamiento seguro."""
    import logging

    from src.manejo_errores_langchain import (
        construir_enrutamiento_seguro,
    )

    def modelo_con_error(entrada: object) -> str:
        """Simula un fallo técnico del modelo."""
        raise RuntimeError("Fallo interno confidencial")

    cadena = construir_enrutamiento_seguro(
        RunnableLambda(modelo_con_error)
    )

    mensaje = "¿Cómo solicito una autorización municipal?"

    with caplog.at_level(logging.ERROR):
        resultado = cadena.invoke({"mensaje": mensaje})

    # La respuesta debe mantener el contrato de VyOps.
    assert resultado["mensaje"] == mensaje
    assert resultado["categoria"] == "error"

    # El error técnico debe quedar registrado.
    assert "Falló el enrutamiento de LangChain." in caplog.text
    assert "Se activó la respuesta alternativa." in caplog.text
    assert "Fallo interno confidencial" not in caplog.text

    # El usuario no debe recibir información interna.
    assert "Fallo interno confidencial" not in resultado["respuesta"]
