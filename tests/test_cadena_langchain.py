
"""Pruebas de la cadena LangChain de tres etapas.

Este módulo verifica el funcionamiento secuencial
de la cadena construida mediante construir_cadena(),
definida en src.cadena_langchain.

La cadena procesa un texto mediante tres etapas
consecutivas, utilizando el resultado de cada etapa
como entrada para la siguiente.

El escenario evaluado utiliza las siguientes respuestas:

    1. Primera etapa:
       HALLAZGOS_ETAPA_1

    2. Segunda etapa:
       SIMPLIFICACION_ETAPA_2

    3. Tercera etapa:
       - RESULTADO_FINAL

La prueba comprueba:

    - Que el modelo se invoque exactamente tres veces.
    - Que la primera etapa reciba el texto original.
    - Que la segunda etapa reciba la primera respuesta.
    - Que la tercera etapa reciba la segunda respuesta.
    - Que el resultado final sea el texto esperado.

Se utiliza MagicMock para controlar las respuestas
del modelo y RunnableLambda para integrarlo
en la cadena LangChain.

No se realizan llamadas a modelos externos
ni se consumen servicios de inteligencia artificial.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Permite simular las respuestas del modelo
# y registrar sus invocaciones.
from unittest.mock import MagicMock

# Representa los mensajes generados por un modelo
# de inteligencia artificial en LangChain.
from langchain_core.messages import AIMessage

# Adapta una función invocable a la interfaz Runnable
# utilizada por las cadenas de LangChain.
from langchain_core.runnables import RunnableLambda

# Función que construye la cadena de procesamiento
# de tres etapas utilizada por VyOps.
from src.cadena_langchain import construir_cadena


# ============================================================
# 2. VALIDACIÓN DE LA EJECUCIÓN SECUENCIAL
# ============================================================

def test_cadena_ejecuta_tres_etapas_en_orden() -> None:
    """Verifica que cada etapa reciba el resultado de la anterior.

    Configura un modelo simulado que devuelve tres respuestas
    consecutivas mediante MagicMock.

    Escenario:
        - Entrada original: INFORME_ORIGINAL.
        - Primera respuesta: HALLAZGOS_ETAPA_1.
        - Segunda respuesta: SIMPLIFICACION_ETAPA_2.
        - Tercera respuesta: - RESULTADO_FINAL.

    Verificaciones:
        - El modelo se invoca exactamente tres veces.
        - El primer prompt contiene el informe original.
        - El segundo prompt contiene la primera respuesta.
        - El tercer prompt contiene la segunda respuesta.
        - La cadena devuelve el resultado final esperado.

    Esta prueba comprueba la transferencia de información
    entre las etapas y el resultado de la composición.

    No evalúa la calidad semántica de las respuestas,
    ya que estas son proporcionadas por un modelo simulado.
    """

    # --------------------------------------------------------
    # 2.1. CONFIGURACIÓN DEL MODELO SIMULADO
    # --------------------------------------------------------

    # Define las respuestas consecutivas que devolverá
    # el modelo durante las tres etapas de procesamiento.
    respuestas = MagicMock(
        side_effect=[
            AIMessage(content="HALLAZGOS_ETAPA_1"),
            AIMessage(content="SIMPLIFICACION_ETAPA_2"),
            AIMessage(content="- RESULTADO_FINAL"),
        ]
    )

    # --------------------------------------------------------
    # 2.2. CONSTRUCCIÓN DE LA CADENA
    # --------------------------------------------------------

    # Adapta el mock a la interfaz Runnable de LangChain.
    modelo_simulado = RunnableLambda(respuestas)

    # Construye la cadena utilizando el modelo simulado.
    cadena = construir_cadena(modelo_simulado)

    # --------------------------------------------------------
    # 2.3. EJECUCIÓN DEL FLUJO
    # --------------------------------------------------------

    # Ejecuta la cadena con el texto de entrada original.
    # La cadena debe procesarlo mediante sus tres etapas.
    resultado = cadena.invoke({"texto": "INFORME_ORIGINAL"})

    # --------------------------------------------------------
    # 2.4. RECUPERACIÓN DE LOS PROMPTS
    # --------------------------------------------------------

    # Obtiene los prompts recibidos por el modelo
    # en cada una de sus invocaciones.
    #
    # to_string() permite inspeccionar su contenido
    # como texto para verificar la transferencia
    # de información entre etapas.
    prompts = [
        llamada.args[0].to_string()
        for llamada in respuestas.call_args_list
    ]

    # --------------------------------------------------------
    # 2.5. VERIFICACIÓN DEL NÚMERO DE ETAPAS
    # --------------------------------------------------------

    # El modelo debe ejecutarse exactamente tres veces.
    assert respuestas.call_count == 3

    # --------------------------------------------------------
    # 2.6. VERIFICACIÓN DE LA SECUENCIA
    # --------------------------------------------------------

    # La primera etapa debe recibir el texto original.
    assert "INFORME_ORIGINAL" in prompts[0]

    # La segunda etapa debe incorporar los hallazgos
    # generados durante la primera etapa.
    assert "HALLAZGOS_ETAPA_1" in prompts[1]

    # La tercera etapa debe incorporar la simplificación
    # generada durante la segunda etapa.
    assert "SIMPLIFICACION_ETAPA_2" in prompts[2]

    # --------------------------------------------------------
    # 2.7. VERIFICACIÓN DEL RESULTADO FINAL
    # --------------------------------------------------------

    # La cadena debe devolver el contenido textual
    # correspondiente a la tercera respuesta simulada.
    assert resultado == "- RESULTADO_FINAL"
