
"""Pruebas del enrutamiento condicional del Bloque 19.

Este módulo verifica el comportamiento de la cadena
de enrutamiento construida mediante LangChain.

El sistema clasifica los mensajes recibidos y selecciona
una ruta de respuesta según la categoría identificada.

Las categorías evaluadas son:

    - queja: mensajes que comunican problemas.
    - pregunta: consultas que requieren orientación.
    - sugerencia: propuestas de mejora.
    - otro: mensajes que no corresponden a las categorías
      reconocidas por el enrutamiento.

Las pruebas comprueban:

    1. Selección de la ruta de quejas.
    2. Selección de la ruta de preguntas.
    3. Selección de la ruta de sugerencias.
    4. Selección de la ruta predeterminada.
    5. Normalización de categorías con espacios
       y diferencias entre mayúsculas y minúsculas.

Se utiliza MagicMock para controlar las respuestas
del modelo y RunnableLambda para integrarlas
en la interfaz ejecutable de LangChain.

Cada escenario verifica que el modelo sea invocado
dos veces: una para clasificar el mensaje y otra
para generar la respuesta correspondiente.

Las pruebas no realizan llamadas a modelos externos.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Permite simular las respuestas del modelo
# y registrar las invocaciones realizadas.
from unittest.mock import MagicMock

# Adapta una función invocable a la interfaz
# Runnable utilizada por LangChain.
from langchain_core.runnables import RunnableLambda

# Constructor de la cadena que clasifica mensajes
# y selecciona la ruta de respuesta correspondiente.
from src.enrutamiento_langchain import construir_cadena_enrutamiento


# ============================================================
# 2. ENRUTAMIENTO DE QUEJAS
# ============================================================

def test_enrutamiento_selecciona_ruta_queja() -> None:
    """Verifica que una queja active únicamente su ruta.

    Simula dos respuestas consecutivas del modelo:

        1. Clasificación: "  QUEJA  ".
        2. Respuesta: texto de la ruta de quejas.

    Verificaciones:
        - La categoría se normaliza como "queja".
        - Se devuelve la respuesta simulada.
        - El mensaje original permanece intacto.
        - El modelo recibe exactamente dos invocaciones.

    Este escenario comprueba la selección de la ruta
    de quejas cuando la clasificación contiene espacios
    y caracteres en mayúsculas.
    """

    # Configura las respuestas secuenciales del modelo:
    # primero la clasificación y después la respuesta.
    respuestas = MagicMock(
        side_effect=[
            "  QUEJA  ",
            "Respuesta de la ruta de quejas",
        ]
    )

    # Construye una cadena utilizando el modelo simulado.
    modelo_simulado = RunnableLambda(respuestas)
    cadena = construir_cadena_enrutamiento(modelo_simulado)

    # Envía un mensaje que describe un problema
    # con el funcionamiento de una aplicación.
    resultado = cadena.invoke({
        "mensaje": "La aplicación se cierra al subir una foto."
    })

    # Comprueba la categoría, la respuesta
    # y la conservación del mensaje original.
    assert resultado["categoria"] == "queja"
    assert resultado["respuesta"] == "Respuesta de la ruta de quejas"
    assert resultado["mensaje"] == "La aplicación se cierra al subir una foto."

    # Una invocación corresponde a la clasificación
    # y la otra a la generación de la respuesta.
    assert respuestas.call_count == 2


# ============================================================
# 3. ENRUTAMIENTO DE PREGUNTAS
# ============================================================

def test_enrutamiento_selecciona_ruta_pregunta() -> None:
    """Verifica que una pregunta active su ruta y conserve el mensaje.

    Simula una clasificación mediante AIMessage
    con la categoría "pregunta".

    Verificaciones:
        - La categoría resultante es "pregunta".
        - Se devuelve la respuesta de la ruta seleccionada.
        - El mensaje original se conserva.
        - El modelo recibe dos invocaciones.
        - El prompt de respuesta incluye la consulta original.
        - El prompt contiene el término "documentos".

    La inspección del segundo prompt permite comprobar
    que la ruta de preguntas recibe el contenido
    necesario para generar su respuesta.
    """

    # Importa el tipo de mensaje utilizado para representar
    # respuestas de un modelo de chat de LangChain.
    from langchain_core.messages import AIMessage

    # Simula la clasificación y la respuesta
    # mediante objetos AIMessage.
    respuestas = MagicMock(
        side_effect=[
            AIMessage(content="pregunta"),
            AIMessage(content="Respuesta de la ruta de preguntas"),
        ]
    )

    # Construye la cadena con el modelo simulado.
    modelo_simulado = RunnableLambda(respuestas)
    cadena = construir_cadena_enrutamiento(modelo_simulado)

    # Define una consulta sobre documentación municipal.
    mensaje = "¿Qué documentos necesito para obtener una patente comercial?"

    # Ejecuta el enrutamiento.
    resultado = cadena.invoke({"mensaje": mensaje})

    # Comprueba la categoría y el contenido devuelto.
    assert resultado["categoria"] == "pregunta"
    assert resultado["respuesta"] == "Respuesta de la ruta de preguntas"
    assert resultado["mensaje"] == mensaje
    assert respuestas.call_count == 2

    # La segunda llamada debe recibir el mensaje original.
    # Se inspecciona el prompt enviado para generar
    # la respuesta, no el prompt de clasificación.
    prompt_respuesta = respuestas.call_args_list[1].args[0].to_string()

    # Verifica que la consulta y su contexto documental
    # estén presentes en el prompt.
    assert mensaje in prompt_respuesta
    assert "documentos" in prompt_respuesta


# ============================================================
# 4. ENRUTAMIENTO DE SUGERENCIAS
# ============================================================

def test_enrutamiento_selecciona_ruta_sugerencia() -> None:
    """Verifica que una sugerencia active la ruta correspondiente.

    Simula una clasificación con la categoría
    "SUGERENCIA" en mayúsculas.

    Verificaciones:
        - La categoría se normaliza como "sugerencia".
        - Se utiliza la respuesta de la ruta correspondiente.
        - El mensaje original se conserva.
        - El modelo recibe dos invocaciones.
        - El prompt incluye el mensaje original.
        - El prompt contiene "analizar propuestas".

    Esta prueba comprueba que la cadena seleccione
    una plantilla orientada al tratamiento de sugerencias.
    """

    # Utiliza AIMessage para simular respuestas
    # compatibles con modelos de chat.
    from langchain_core.messages import AIMessage

    # Configura la clasificación y la respuesta simuladas.
    respuestas = MagicMock(
        side_effect=[
            AIMessage(content="SUGERENCIA"),
            AIMessage(content="Respuesta de la ruta de sugerencias"),
        ]
    )

    # Construye la cadena de enrutamiento.
    modelo_simulado = RunnableLambda(respuestas)
    cadena = construir_cadena_enrutamiento(modelo_simulado)

    # Define una propuesta de mejora relacionada
    # con trámites municipales.
    mensaje = (
        "Sería útil automatizar la solicitud "
        "de documentos para permisos municipales."
    )

    # Ejecuta la clasificación y generación de respuesta.
    resultado = cadena.invoke({"mensaje": mensaje})

    # Verifica la categoría normalizada,
    # la respuesta y el mensaje original.
    assert resultado["categoria"] == "sugerencia"
    assert resultado["respuesta"] == "Respuesta de la ruta de sugerencias"
    assert resultado["mensaje"] == mensaje
    assert respuestas.call_count == 2

    # Comprobar que la ruta recibe el mensaje original.
    prompt_respuesta = respuestas.call_args_list[1].args[0].to_string()

    # Comprueba que el prompt contenga el mensaje
    # y la instrucción asociada a sugerencias.
    assert mensaje in prompt_respuesta
    assert "analizar propuestas" in prompt_respuesta


# ============================================================
# 5. ENRUTAMIENTO PREDETERMINADO
# ============================================================

def test_enrutamiento_selecciona_ruta_defecto() -> None:
    """Verifica la ruta por defecto ante una categoría desconocida.

    Simula una clasificación con el texto "  OTRO  ".

    Verificaciones:
        - La categoría resultante es "otro".
        - Se devuelve la respuesta de la ruta predeterminada.
        - Se conserva el mensaje original.
        - El modelo recibe dos invocaciones.
        - El prompt contiene el mensaje original.
        - El prompt incluye la instrucción
          "no pudo clasificarse claramente".

    Este escenario comprueba el tratamiento de mensajes
    que no pertenecen a las categorías específicas.
    """

    # Importa el tipo de mensaje de respuesta de LangChain.
    from langchain_core.messages import AIMessage

    # Simula una clasificación fuera de las rutas específicas.
    respuestas = MagicMock(
        side_effect=[
            AIMessage(content="  OTRO  "),
            AIMessage(content="Respuesta de la ruta por defecto"),
        ]
    )

    # Construye la cadena utilizando el modelo simulado.
    modelo_simulado = RunnableLambda(respuestas)
    cadena = construir_cadena_enrutamiento(modelo_simulado)

    # Define un mensaje sin una categoría específica.
    mensaje = "Necesito orientación sobre un asunto."

    # Ejecuta el enrutamiento.
    resultado = cadena.invoke({"mensaje": mensaje})

    # Comprueba la categoría y la respuesta predeterminadas.
    assert resultado["categoria"] == "otro"
    assert resultado["respuesta"] == "Respuesta de la ruta por defecto"
    assert resultado["mensaje"] == mensaje
    assert respuestas.call_count == 2

    # Verificar que se utilizó la plantilla por defecto.
    prompt_respuesta = respuestas.call_args_list[1].args[0].to_string()

    # Comprueba que el prompt conserve el mensaje
    # e incluya la instrucción de la ruta alternativa.
    assert mensaje in prompt_respuesta
    assert "no pudo clasificarse claramente" in prompt_respuesta


# ============================================================
# 6. NORMALIZACIÓN DE CATEGORÍAS
# ============================================================

def test_enrutamiento_normaliza_pregunta() -> None:
    """Verifica la normalización de espacios y mayúsculas.

    Simula una clasificación que contiene:

        - Espacios iniciales y finales.
        - Saltos de línea.
        - La categoría PREGUNTA en mayúsculas.

    Verificaciones:
        - La categoría resultante es "pregunta".
        - Se conserva la respuesta simulada.
        - El mensaje original permanece intacto.
        - El modelo recibe dos invocaciones.
        - Se utiliza una plantilla que contiene
          la expresión "orientación técnica".

    Este escenario comprueba que las diferencias
    de formato en la clasificación no impidan
    seleccionar la ruta de preguntas.
    """

    # Importa AIMessage para representar
    # las respuestas simuladas del modelo.
    from langchain_core.messages import AIMessage

    # Configura una categoría con espacios,
    # saltos de línea y letras mayúsculas.
    respuestas = MagicMock(
        side_effect=[
            AIMessage(content=" \n PREGUNTA \n "),
            AIMessage(content="Respuesta normalizada"),
        ]
    )

    # Construye la cadena con el modelo simulado.
    modelo_simulado = RunnableLambda(respuestas)
    cadena = construir_cadena_enrutamiento(modelo_simulado)

    # Envía una consulta sobre autorización sanitaria.
    resultado = cadena.invoke({
        "mensaje": "¿Cómo funciona el proceso de autorización sanitaria?"
    })

    # Comprueba que la clasificación se normalice
    # y que la respuesta corresponda a la ruta seleccionada.
    assert resultado["categoria"] == "pregunta"
    assert resultado["respuesta"] == "Respuesta normalizada"
    assert resultado["mensaje"] == (
    "¿Cómo funciona el proceso de autorización sanitaria?"
    )
    assert respuestas.call_count == 2

    # Comprobar que se seleccionó la plantilla de preguntas.
    prompt_respuesta = respuestas.call_args_list[1].args[0].to_string()

    # La plantilla debe incluir la instrucción
    # asociada a la orientación técnica.
    assert "orientación técnica" in prompt_respuesta
