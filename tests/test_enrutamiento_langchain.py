"""Pruebas del enrutamiento condicional del Bloque 19."""

from unittest.mock import MagicMock

from langchain_core.runnables import RunnableLambda

from src.enrutamiento_langchain import construir_cadena_enrutamiento


def test_enrutamiento_selecciona_ruta_queja() -> None:
    """Verifica que una queja active únicamente su ruta."""
    respuestas = MagicMock(
        side_effect=[
            "  QUEJA  ",
            "Respuesta de la ruta de quejas",
        ]
    )

    modelo_simulado = RunnableLambda(respuestas)
    cadena = construir_cadena_enrutamiento(modelo_simulado)

    resultado = cadena.invoke({
        "mensaje": "La aplicación se cierra al subir una foto."
    })

    assert resultado["categoria"] == "queja"
    assert resultado["respuesta"] == "Respuesta de la ruta de quejas"
    assert resultado["mensaje"] == "La aplicación se cierra al subir una foto."
    assert respuestas.call_count == 2

def test_enrutamiento_selecciona_ruta_pregunta() -> None:
    """Verifica que una pregunta active su ruta y conserve el mensaje."""
    from langchain_core.messages import AIMessage

    respuestas = MagicMock(
        side_effect=[
            AIMessage(content="pregunta"),
            AIMessage(content="Respuesta de la ruta de preguntas"),
        ]
    )

    modelo_simulado = RunnableLambda(respuestas)
    cadena = construir_cadena_enrutamiento(modelo_simulado)

    mensaje = "¿Qué documentos necesito para obtener una patente comercial?"

    resultado = cadena.invoke({"mensaje": mensaje})

    assert resultado["categoria"] == "pregunta"
    assert resultado["respuesta"] == "Respuesta de la ruta de preguntas"
    assert resultado["mensaje"] == mensaje
    assert respuestas.call_count == 2

    # La segunda llamada debe recibir el mensaje original.
    prompt_respuesta = respuestas.call_args_list[1].args[0].to_string()

    assert mensaje in prompt_respuesta
    assert "documentos" in prompt_respuesta

def test_enrutamiento_selecciona_ruta_sugerencia() -> None:
    """Verifica que una sugerencia active la ruta correspondiente."""
    from langchain_core.messages import AIMessage

    respuestas = MagicMock(
        side_effect=[
            AIMessage(content="SUGERENCIA"),
            AIMessage(content="Respuesta de la ruta de sugerencias"),
        ]
    )

    modelo_simulado = RunnableLambda(respuestas)
    cadena = construir_cadena_enrutamiento(modelo_simulado)

    mensaje = (
        "Sería útil automatizar la solicitud "
        "de documentos para permisos municipales."
    )

    resultado = cadena.invoke({"mensaje": mensaje})

    assert resultado["categoria"] == "sugerencia"
    assert resultado["respuesta"] == "Respuesta de la ruta de sugerencias"
    assert resultado["mensaje"] == mensaje
    assert respuestas.call_count == 2

    # Comprobar que la ruta recibe el mensaje original.
    prompt_respuesta = respuestas.call_args_list[1].args[0].to_string()

    assert mensaje in prompt_respuesta
    assert "analizar propuestas" in prompt_respuesta

def test_enrutamiento_selecciona_ruta_defecto() -> None:
    """Verifica la ruta por defecto ante una categoría desconocida."""
    from langchain_core.messages import AIMessage

    respuestas = MagicMock(
        side_effect=[
            AIMessage(content="  OTRO  "),
            AIMessage(content="Respuesta de la ruta por defecto"),
        ]
    )

    modelo_simulado = RunnableLambda(respuestas)
    cadena = construir_cadena_enrutamiento(modelo_simulado)

    mensaje = "Necesito orientación sobre un asunto."

    resultado = cadena.invoke({"mensaje": mensaje})

    assert resultado["categoria"] == "otro"
    assert resultado["respuesta"] == "Respuesta de la ruta por defecto"
    assert resultado["mensaje"] == mensaje
    assert respuestas.call_count == 2

    # Verificar que se utilizó la plantilla por defecto.
    prompt_respuesta = respuestas.call_args_list[1].args[0].to_string()

    assert mensaje in prompt_respuesta
    assert "no pudo clasificarse claramente" in prompt_respuesta

def test_enrutamiento_normaliza_pregunta() -> None:
    """Verifica la normalización de espacios y mayúsculas."""
    from langchain_core.messages import AIMessage

    respuestas = MagicMock(
        side_effect=[
            AIMessage(content=" \n PREGUNTA \n "),
            AIMessage(content="Respuesta normalizada"),
        ]
    )

    modelo_simulado = RunnableLambda(respuestas)
    cadena = construir_cadena_enrutamiento(modelo_simulado)

    resultado = cadena.invoke({
        "mensaje": "¿Cómo funciona el proceso de autorización sanitaria?"
    })

    assert resultado["categoria"] == "pregunta"
    assert resultado["respuesta"] == "Respuesta normalizada"
    assert resultado["mensaje"] == (
    "¿Cómo funciona el proceso de autorización sanitaria?"
    )
    assert respuestas.call_count == 2

    # Comprobar que se seleccionó la plantilla de preguntas.
    prompt_respuesta = respuestas.call_args_list[1].args[0].to_string()
    assert "orientación técnica" in prompt_respuesta