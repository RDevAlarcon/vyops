
"""Pruebas unitarias del agente municipal con herramientas de VyOps.

Este módulo verifica el funcionamiento del agente construido
mediante construir_agente_municipal() y sus herramientas.

Las pruebas se organizan en seis áreas:

    1. Herramientas de cálculo y consulta documental.
    2. Selección, ejecución y trazabilidad de herramientas.
    3. Modelos de respaldo y límites de ejecución.
    4. Manejo seguro de errores y registros.
    5. Normalización de respuestas del agente.
    6. Supervisión humana de cancelaciones simuladas.

Se utiliza FakeMessagesListChatModel para proporcionar
respuestas controladas sin consultar un modelo externo.

La clase FakeToolCallingModel adapta ese modelo simulado
para permitir su utilización en agentes que requieren
la interfaz de vinculación de herramientas.

Las pruebas comprueban tanto los resultados entregados
al usuario como las acciones registradas en
intermediate_steps.

No se realizan operaciones municipales reales.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Herramientas, constructor del agente y funciones
# de ejecución y normalización utilizadas por VyOps.
from src.agente_con_herramientas import (
    analizar_datos,
    calcular_metricas,
    consultar_documentacion,
    construir_agente_municipal,
    ejecutar_agente_seguro,
    normalizar_respuesta_agente,
)

# Representa respuestas de un modelo de chat.
from langchain_core.messages import AIMessage

# Modelo simulado que devuelve mensajes predefinidos.
from langchain_core.language_models.fake_chat_models import (
    FakeMessagesListChatModel,
)


# ============================================================
# 2. MODELO SIMULADO CON SOPORTE DE HERRAMIENTAS
# ============================================================

class FakeToolCallingModel(FakeMessagesListChatModel):
    """Simula un modelo compatible con llamadas a herramientas.

    Extiende FakeMessagesListChatModel para permitir que
    el constructor del agente invoque bind_tools().

    Las respuestas y llamadas a herramientas se proporcionan
    mediante mensajes AIMessage previamente definidos.

    No realiza solicitudes a proveedores externos.
    """

    def bind_tools(
        self,
        tools: list,
        *,
        tool_choice: str | None = None,
        **kwargs,
    ):
        """Acepta herramientas para ejecutar pruebas sin una API externa.

        Args:
            tools:
                Herramientas que el agente intenta vincular.
            tool_choice:
                Preferencia opcional de selección de herramientas.
            **kwargs:
                Argumentos adicionales de configuración.

        Returns:
            FakeToolCallingModel:
                La misma instancia del modelo simulado.

        Esta implementación permite probar el flujo
        de herramientas sin configurar un proveedor real.
        """
        return self


# ============================================================
# 3. PRUEBAS DE HERRAMIENTAS INDIVIDUALES
# ============================================================

def test_calcular_metricas_promedio() -> None:
    """Verifica que la herramienta calcule correctamente el promedio.

    Utiliza los valores 100, 200 y 300.

    El promedio esperado es 200.0 y debe devolverse
    mediante el mensaje textual definido por la herramienta.
    """

    # Ejecuta la herramienta con la operación promedio.
    resultado = calcular_metricas.invoke(
        {
            "valores": [100, 200, 300],
            "operacion": "promedio",
        }
    )

    # Comprueba el resultado textual esperado.
    assert resultado == "El resultado de promedio es 200.0."


def test_calcular_metricas_lista_vacia() -> None:
    """Verifica el manejo de una lista sin valores.

    Comprueba que la herramienta devuelva un mensaje
    de error cuando se solicita calcular un promedio
    sin proporcionar datos.
    """

    # Intenta calcular el promedio de una lista vacía.
    resultado = calcular_metricas.invoke(
        {
            "valores": [],
            "operacion": "promedio",
        }
    )

    # La herramienta debe informar que faltan valores.
    assert resultado == (
        "Error: la lista de valores no puede estar vacía."
    )


def test_consultar_documentacion_tema_existente() -> None:
    """Verifica la consulta de un tema disponible en VyOps.

    Consulta la documentación correspondiente a LangChain.

    Comprueba que el resultado incluya información
    sobre la construcción de aplicaciones y el uso
    de herramientas y agentes.
    """

    # Consulta un tema presente en la documentación.
    resultado = consultar_documentacion.invoke(
        {"tema": "langchain"}
    )

    # Comprueba fragmentos relevantes de la respuesta.
    assert "LangChain permite construir aplicaciones" in resultado
    assert "herramientas y agentes" in resultado


def test_consultar_documentacion_tema_desconocido() -> None:
    """Verifica la respuesta ante documentación no disponible.

    Consulta un tema que no está disponible
    en la fuente documental utilizada por la prueba.

    La herramienta debe comunicar que no encontró
    documentación para el tema solicitado.
    """

    # Consulta un tema no disponible.
    resultado = consultar_documentacion.invoke(
        {"tema": "ordenanzas municipales"}
    )

    # Comprueba el mensaje de ausencia de documentación.
    assert resultado == (
        "No se encontró documentación para el tema: "
        "ordenanzas municipales."
    )


def test_analizar_datos_aumento_solicitudes() -> None:
    """Verifica el aumento de solicitudes municipales entre períodos.

    Compara un valor inicial de 120 solicitudes
    con un valor final de 150.

    Resultados esperados:
        - Variación absoluta: 30.
        - Variación porcentual: 25.0.
        - Tendencia: aumento.
    """

    # Calcula la variación entre ambos períodos.
    resultado = analizar_datos.invoke(
        {
            "valor_inicial": 120,
            "valor_final": 150,
        }
    )

    # Verifica la magnitud y dirección del cambio.
    assert resultado["variacion_absoluta"] == 30
    assert resultado["variacion_porcentual"] == 25.0
    assert resultado["tendencia"] == "aumento"


def test_analizar_datos_disminucion_solicitudes() -> None:
    """Verifica la disminución de solicitudes entre períodos.

    Compara 200 solicitudes iniciales con 150 finales.

    Resultados esperados:
        - Variación absoluta: -50.
        - Variación porcentual: -25.0.
        - Tendencia: disminucion.
    """

    # Calcula la variación de las solicitudes.
    resultado = analizar_datos.invoke(
        {
            "valor_inicial": 200,
            "valor_final": 150,
        }
    )

    # Comprueba que la disminución conserve el signo negativo.
    assert resultado["variacion_absoluta"] == -50
    assert resultado["variacion_porcentual"] == -25.0
    assert resultado["tendencia"] == "disminucion"


def test_analizar_datos_valor_inicial_cero() -> None:
    """Verifica el análisis cuando el valor inicial es cero.

    Compara cero solicitudes iniciales con 50 finales.

    Comprueba que:
        - La variación absoluta sea 50.
        - La variación porcentual sea None.
        - La tendencia indique aumento.

    El valor None evita representar un porcentaje
    que no puede calcularse usando una base igual a cero.
    """

    # Ejecuta el análisis con valor inicial cero.
    resultado = analizar_datos.invoke(
        {
            "valor_inicial": 0,
            "valor_final": 50,
        }
    )

    # Comprueba los resultados del escenario.
    assert resultado["variacion_absoluta"] == 50
    assert resultado["variacion_porcentual"] is None
    assert resultado["tendencia"] == "aumento"


# ============================================================
# 4. EJECUCIÓN Y TRAZABILIDAD DEL AGENTE
# ============================================================

def test_agente_selecciona_analizar_datos() -> None:
    """Verifica la ejecución y trazabilidad de analizar_datos.

    Simula un modelo que solicita ejecutar analizar_datos
    para comparar 120 y 150 solicitudes municipales.

    Comprueba:
        - La ejecución de una herramienta.
        - El nombre de la herramienta seleccionada.
        - El resultado porcentual registrado.
        - La respuesta final del agente.
    """

    # El primer mensaje solicita ejecutar la herramienta.
    # El segundo representa la respuesta final del modelo.
    modelo_simulado = FakeToolCallingModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "analizar_datos",
                        "args": {
                            "valor_inicial": 120,
                            "valor_final": 150,
                        },
                        "id": "llamada_analisis_1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(
                content="Las solicitudes aumentaron un 25 %."
            ),
        ]
    )

    # Construye el agente con el modelo simulado.
    agente = construir_agente_municipal(
        modelo=modelo_simulado
    )

    # Ejecuta una consulta municipal.
    resultado = agente.invoke(
        {
            "entrada": (
                "Compara las solicitudes municipales: "
                "120 en enero y 150 en febrero."
            )
        }
    )

    # Recupera las acciones y observaciones registradas.
    pasos = resultado["intermediate_steps"]

    # Verifica la herramienta, el cálculo y la respuesta.
    assert len(pasos) == 1
    assert pasos[0][0].tool == "analizar_datos"
    assert pasos[0][1]["variacion_porcentual"] == 25.0
    assert resultado["output"] == (
        "Las solicitudes aumentaron un 25 %."
    )


def test_agente_responde_sin_herramientas() -> None:
    """Verifica que el agente pueda responder sin ejecutar herramientas.

    Simula una respuesta directa sobre el propósito de VyOps.

    Comprueba que el agente devuelva el texto esperado
    y que intermediate_steps permanezca vacío.
    """

    # Configura una respuesta sin llamadas a herramientas.
    modelo_simulado = FakeToolCallingModel(
        responses=[
            AIMessage(
                content=(
                    "VyOps es un asistente de apoyo "
                    "a la gestión municipal."
                )
            )
        ]
    )

    # Construye el agente.
    agente = construir_agente_municipal(
        modelo=modelo_simulado
    )

    # Ejecuta una consulta informativa.
    resultado = agente.invoke(
        {
            "entrada": (
                "¿Cuál es el propósito general de VyOps?"
            )
        }
    )

    # Comprueba la respuesta y la ausencia de acciones.
    assert resultado["output"] == (
        "VyOps es un asistente de apoyo "
        "a la gestión municipal."
    )
    assert resultado["intermediate_steps"] == []


def test_agente_consulta_documentacion() -> None:
    """Verifica la ejecución y trazabilidad de una consulta documental.

    Simula una llamada a consultar_documentacion
    con el tema vyops.

    Comprueba que la herramienta se registre,
    que su observación contenga documentación
    y que el agente entregue la respuesta esperada.
    """

    # Configura una llamada documental y una respuesta final.
    modelo_simulado = FakeToolCallingModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "consultar_documentacion",
                        "args": {"tema": "vyops"},
                        "id": "llamada_documentacion_1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(
                content="VyOps apoya el aprendizaje y desarrollo de IA."
            ),
        ]
    )

    # Construye el agente municipal.
    agente = construir_agente_municipal(
        modelo=modelo_simulado
    )

    # Ejecuta la consulta documental.
    resultado = agente.invoke(
        {"entrada": "Consulta la documentación de VyOps."}
    )

    # Recupera las acciones registradas.
    pasos = resultado["intermediate_steps"]

    # Comprueba la ejecución y la respuesta.
    assert len(pasos) == 1
    assert pasos[0][0].tool == "consultar_documentacion"
    assert "VyOps es un proyecto" in pasos[0][1]
    assert resultado["output"] == (
        "VyOps apoya el aprendizaje y desarrollo de IA."
    )


def test_agente_utiliza_multiples_herramientas() -> None:
    """Verifica la ejecución de dos herramientas en una consulta.

    Solicita calcular el promedio de 100, 120 y 140
    solicitudes y analizar la variación entre 100 y 140.

    Comprueba:
        - La ejecución de dos herramientas.
        - El orden de las acciones registradas.
        - El promedio calculado.
        - La variación porcentual del 40 %.
    """

    # Simula dos llamadas a herramientas en un mismo mensaje.
    modelo_simulado = FakeToolCallingModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "calcular_metricas",
                        "args": {
                            "valores": [100, 120, 140],
                            "operacion": "promedio",
                        },
                        "id": "llamada_promedio_1",
                        "type": "tool_call",
                    },
                    {
                        "name": "analizar_datos",
                        "args": {
                            "valor_inicial": 100,
                            "valor_final": 140,
                        },
                        "id": "llamada_variacion_1",
                        "type": "tool_call",
                    },
                ],
            ),
            AIMessage(
                content=(
                    "El promedio fue de 120 solicitudes "
                    "y el aumento entre el primer y último mes fue del 40 %."
                )
            ),
        ]
    )

    # Construye el agente con las herramientas disponibles.
    agente = construir_agente_municipal(
        modelo=modelo_simulado
    )

    # Ejecuta una consulta que requiere dos cálculos.
    resultado = agente.invoke(
        {
            "entrada": (
                "Analiza las solicitudes municipales de enero, "
                "febrero y marzo: 100, 120 y 140. "
                "Calcula el promedio y la variación entre enero y marzo."
            )
        }
    )

    # Recupera las acciones ejecutadas.
    pasos = resultado["intermediate_steps"]

    # Comprueba la cantidad y el orden de las herramientas.
    assert len(pasos) == 2
    assert [paso[0].tool for paso in pasos] == [
        "calcular_metricas",
        "analizar_datos",
    ]

    # Verifica los resultados de ambas herramientas.
    assert "120.0" in pasos[0][1]
    assert pasos[1][1]["variacion_porcentual"] == 40.0


# ============================================================
# 5. MODELOS DE RESPALDO Y LÍMITES DE EJECUCIÓN
# ============================================================

def test_fallback_modelo_agente() -> None:
    """Verifica el respaldo cuando falla el modelo principal.

    Configura un Runnable principal que genera RuntimeError
    y otro que devuelve una respuesta válida.

    Comprueba que with_fallbacks() permita recuperar
    la operación mediante el modelo de respaldo.
    """

    # Importa el adaptador Runnable utilizado en la prueba.
    from langchain_core.runnables import RunnableLambda

    def modelo_principal_fallido(entrada):
        """Simula un fallo del modelo principal.

        Args:
            entrada:
                Consulta recibida por el modelo.

        Raises:
            RuntimeError:
                Indica que el modelo principal no está disponible.
        """
        raise RuntimeError("Modelo principal no disponible")

    # Configura el modelo principal y su alternativa.
    modelo_principal = RunnableLambda(modelo_principal_fallido)
    modelo_respaldo = RunnableLambda(
        lambda entrada: "Respuesta del modelo de respaldo"
    )

    # Vincula el modelo de respaldo al principal.
    modelo_con_respaldo = modelo_principal.with_fallbacks(
        [modelo_respaldo]
    )

    # Ejecuta la consulta utilizando la configuración de respaldo.
    resultado = modelo_con_respaldo.invoke(
        "Consulta municipal de prueba"
    )

    # Comprueba que se devuelva la respuesta alternativa.
    assert resultado == "Respuesta del modelo de respaldo"


def test_agente_respeta_limite_iteraciones() -> None:
    """Verifica que el agente detenga ejecuciones repetitivas.

    Simula un modelo que solicita reiteradamente
    la herramienta consultar_documentacion.

    Comprueba que el agente registre cinco acciones
    y devuelva el mensaje de detención por límite
    de iteraciones.
    """

    # Configura una llamada a herramienta que se repite
    # durante la ejecución del agente.
    modelo_simulado = FakeToolCallingModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "consultar_documentacion",
                        "args": {"tema": "vyops"},
                        "id": "llamada_repetida_1",
                        "type": "tool_call",
                    }
                ],
            )
        ]
    )

    # Construye el agente.
    agente = construir_agente_municipal(
        modelo=modelo_simulado
    )

    # Solicita una consulta repetitiva.
    resultado = agente.invoke(
        {"entrada": "Consulta repetidamente la documentación."}
    )

    # Verifica la detención después de cinco acciones.
    assert len(resultado["intermediate_steps"]) == 5
    assert resultado["output"] == "Agent stopped due to max iterations."


def test_fallback_propaga_error_si_ambos_modelos_fallan() -> None:
    """Verifica el error cuando fallan ambos modelos.

    Simula un fallo de conexión en el modelo principal
    y otro fallo en el modelo de respaldo.

    Comprueba que se propague ConnectionError
    cuando ninguna alternativa puede responder.
    """

    # Importa las dependencias utilizadas en este escenario.
    import pytest
    from langchain_core.runnables import RunnableLambda

    def modelo_principal(entrada):
        """Simula una falla de conexión del modelo principal.

        Args:
            entrada:
                Consulta recibida.

        Raises:
            ConnectionError:
                Indica la ausencia de conexión.
        """
        raise ConnectionError("Modelo principal sin conexión")

    def modelo_respaldo(entrada):
        """Simula una falla de conexión del modelo de respaldo.

        Args:
            entrada:
                Consulta recibida.

        Raises:
            ConnectionError:
                Indica la ausencia de conexión.
        """
        raise ConnectionError("Modelo de respaldo sin conexión")

    # Configura ambos modelos y su mecanismo de respaldo.
    modelo = RunnableLambda(
        modelo_principal
    ).with_fallbacks([
        RunnableLambda(modelo_respaldo)
    ])

    # La operación debe fallar cuando no existe
    # ningún modelo disponible.
    with pytest.raises(ConnectionError):
        modelo.invoke("Consulta municipal de prueba")


# ============================================================
# 6. MANEJO SEGURO DE ERRORES DEL AGENTE
# ============================================================

def test_ejecutar_agente_seguro_error_conexion() -> None:
    """Verifica una respuesta segura ante errores de conexión.

    Simula un ConnectionError que contiene el nombre
    del proveedor Gemini.

    Comprueba que la respuesta pública:
        - Clasifique el error como conexion.
        - Utilice un mensaje comprensible.
        - No incluya acciones ejecutadas.
        - No exponga el nombre del proveedor.
    """

    from langchain_core.runnables import RunnableLambda

    def simular_error(entrada: dict) -> dict:
        """Simula un fallo de conexión con el proveedor.

        Args:
            entrada:
                Datos recibidos por el agente.

        Raises:
            ConnectionError:
                Error de conexión simulado.
        """
        raise ConnectionError(
            "No fue posible establecer conexión con Gemini"
        )

    # Construye un agente simulado que siempre falla.
    agente_simulado = RunnableLambda(simular_error)

    # Ejecuta el agente mediante la interfaz segura.
    resultado = ejecutar_agente_seguro(
        agente=agente_simulado,
        entrada="Consulta de solicitudes municipales",
    )

    # Comprueba la clasificación y el mensaje público.
    assert resultado["error"] == "conexion"
    assert resultado["output"] == (
        "No fue posible conectar con el servicio de IA."
    )
    assert resultado["intermediate_steps"] == []
    assert "Gemini" not in resultado["output"]


def test_ejecutar_agente_seguro_timeout() -> None:
    """Verifica una respuesta segura ante un tiempo de espera agotado.

    Simula TimeoutError y comprueba que el agente
    entregue un mensaje público sin exponer
    detalles de la excepción original.
    """

    from langchain_core.runnables import RunnableLambda

    def simular_timeout(entrada: dict) -> dict:
        """Simula un tiempo de espera agotado.

        Args:
            entrada:
                Datos de entrada del agente.

        Raises:
            TimeoutError:
                Indica que se superó el tiempo permitido.
        """
        raise TimeoutError(
            "La conexión con el modelo excedió el tiempo permitido"
        )

    # Configura un agente que genera TimeoutError.
    agente_simulado = RunnableLambda(simular_timeout)

    # Ejecuta la consulta mediante el mecanismo seguro.
    resultado = ejecutar_agente_seguro(
        agente=agente_simulado,
        entrada="Analiza los indicadores municipales",
    )

    # Comprueba la respuesta pública.
    assert resultado["error"] == "timeout"
    assert resultado["output"] == (
        "La consulta excedió el tiempo de espera."
    )
    assert resultado["intermediate_steps"] == []
    assert "modelo" not in resultado["output"].lower()


def test_ejecutar_agente_seguro_error_inesperado() -> None:
    """Verifica una respuesta segura ante errores inesperados.

    Simula RuntimeError durante el procesamiento.

    Comprueba que el error se clasifique como inesperado
    y que la respuesta no exponga detalles internos.
    """

    from langchain_core.runnables import RunnableLambda

    def simular_error(entrada: dict) -> dict:
        """Simula un fallo interno del procesamiento.

        Args:
            entrada:
                Datos recibidos por el agente.

        Raises:
            RuntimeError:
                Error inesperado simulado.
        """
        raise RuntimeError(
            "Error interno inesperado durante el procesamiento"
        )

    # Configura el agente simulado.
    agente_simulado = RunnableLambda(simular_error)

    # Ejecuta la consulta mediante la interfaz segura.
    resultado = ejecutar_agente_seguro(
        agente=agente_simulado,
        entrada="Genera un análisis municipal",
    )

    # Comprueba que la respuesta no revele detalles internos.
    assert resultado["error"] == "inesperado"
    assert resultado["output"] == (
        "No fue posible procesar la solicitud."
    )
    assert resultado["intermediate_steps"] == []
    assert "Error interno" not in resultado["output"]


def test_agente_registra_error_inesperado(caplog) -> None:
    """Verifica el registro de errores sin exponerlos al usuario.

    Utiliza caplog para capturar los registros del módulo.

    Comprueba:
        - La clasificación del error inesperado.
        - La existencia de un mensaje de registro.
        - La presencia del tipo RuntimeError en el registro.
        - La ausencia del detalle interno en la respuesta pública.

    Args:
        caplog:
            Fixture de pytest que captura mensajes de logging.
    """

    import logging
    from langchain_core.runnables import RunnableLambda

    def simular_error(entrada: dict) -> dict:
        """Genera un RuntimeError para verificar su registro.

        Args:
            entrada:
                Datos recibidos por el agente.

        Raises:
            RuntimeError:
                Fallo interno simulado.
        """
        raise RuntimeError("Fallo interno simulado")

    # Construye el agente que genera la excepción.
    agente_simulado = RunnableLambda(simular_error)

    # Captura los mensajes de nivel ERROR del módulo.
    with caplog.at_level(
        logging.ERROR,
        logger="src.agente_con_herramientas",
    ):
        resultado = ejecutar_agente_seguro(
            agente=agente_simulado,
            entrada="Consulta municipal de prueba",
        )

    # Comprueba la clasificación pública del error.
    assert resultado["error"] == "inesperado"

    # Verifica el mensaje registrado para diagnóstico.
    assert (
        "Error inesperado durante la ejecución del agente."
        in caplog.text
    )

    # El registro debe incluir el tipo de excepción.
    assert "RuntimeError" in caplog.text

    # La respuesta pública no debe exponer el detalle interno.
    assert "Fallo interno simulado" not in resultado["output"]


# ============================================================
# 7. NORMALIZACIÓN DE RESPUESTAS
# ============================================================

def test_normalizar_respuesta_texto_simple() -> None:
    """Conserva una respuesta que ya contiene texto.

    Comprueba que una cadena de texto se devuelva
    sin modificar su contenido.
    """

    # Normaliza una respuesta textual.
    resultado = normalizar_respuesta_agente(
        "VyOps está funcionando."
    )

    # Verifica que el texto original se conserve.
    assert resultado == "VyOps está funcionando."


def test_normalizar_respuesta_multiples_bloques() -> None:
    """Une bloques de texto sin exponer metadatos.

    Simula una respuesta formada por dos bloques textuales.

    El primer bloque contiene metadatos adicionales
    que no deben incluirse en el texto público.

    Comprueba que ambos textos se unan mediante
    un salto de línea y que se excluya dato-interno.
    """

    # Define bloques con texto y metadatos adicionales.
    contenido = [
        {
            "type": "text",
            "text": "Se registraron 150 solicitudes.",
            "extras": {"signature": "dato-interno"},
        },
        {
            "type": "text",
            "text": "La variación fue de un 25 %.",
        },
    ]

    # Convierte los bloques en una respuesta textual.
    resultado = normalizar_respuesta_agente(contenido)

    # Comprueba la unión y la exclusión de metadatos.
    assert resultado == (
        "Se registraron 150 solicitudes.\n"
        "La variación fue de un 25 %."
    )
    assert "dato-interno" not in resultado


def test_normalizar_respuesta_sin_texto() -> None:
    """Devuelve texto vacío cuando no hay bloques de texto.

    Proporciona un bloque de tipo tool_use
    que no contiene una respuesta textual.

    Comprueba que la normalización devuelva
    una cadena vacía.
    """

    # Define un bloque de uso de herramienta.
    contenido = [
        {
            "type": "tool_use",
            "name": "analizar_datos",
        }
    ]

    # Normaliza el contenido.
    resultado = normalizar_respuesta_agente(contenido)

    # No debe producirse texto público.
    assert resultado == ""


# ============================================================
# 8. EJECUCIÓN SEGURA Y TRAZABILIDAD
# ============================================================

def test_ejecucion_segura_normaliza_y_conserva_trazas() -> None:
    """Verifica la normalización sin perder la trazabilidad.

    Simula la ejecución de calcular_metricas y una
    respuesta final con contenido estructurado.

    Comprueba:
        - La normalización a una cadena de texto.
        - La exclusión de metadatos internos.
        - La conservación de la acción ejecutada.
        - La ausencia de un error en el resultado.
    """

    # El modelo solicita calcular el promedio
    # y posteriormente devuelve un bloque textual.
    modelo_simulado = FakeToolCallingModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "calcular_metricas",
                        "args": {
                            "valores": [80, 100, 120],
                            "operacion": "promedio",
                        },
                        "id": "llamada_promedio_segura",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(
                content=[
                    {
                        "type": "text",
                        "text": "El promedio mensual fue de 100 solicitudes.",
                        "extras": {"signature": "dato-interno"},
                    }
                ]
            ),
        ]
    )

    # Construye el agente municipal.
    agente = construir_agente_municipal(
        modelo=modelo_simulado
    )

    # Ejecuta la consulta mediante el mecanismo seguro.
    resultado = ejecutar_agente_seguro(
        agente=agente,
        entrada="Calcula el promedio de 80, 100 y 120 solicitudes.",
    )

    # Comprueba el contenido y el tipo de respuesta.
    assert resultado["output"] == (
        "El promedio mensual fue de 100 solicitudes."
    )
    assert isinstance(resultado["output"], str)

    # Verifica que se conserve la traza de la herramienta.
    assert len(resultado["intermediate_steps"]) == 1
    assert resultado["intermediate_steps"][0][0].tool == (
        "calcular_metricas"
    )

    # Los metadatos no deben aparecer en el texto público.
    assert "dato-interno" not in resultado["output"]
    assert "error" not in resultado


def test_ejecucion_segura_detecta_limite_iteraciones() -> None:
    """Detecta una ejecución detenida por límite de iteraciones.

    Simula un agente que devuelve el mensaje interno
    de detención por máximo de iteraciones.

    Comprueba que ejecutar_agente_seguro() transforme
    ese resultado en un mensaje público controlado.
    """

    from langchain_core.runnables import RunnableLambda

    def simular_limite(entrada: dict) -> dict:
        """Devuelve un resultado de límite de iteraciones.

        Args:
            entrada:
                Datos recibidos por el agente.

        Returns:
            dict:
                Resultado simulado con el mensaje de detención
                y una lista vacía de acciones.
        """
        return {
            "output": "Agent stopped due to max iterations.",
            "intermediate_steps": [],
        }

    # Construye el agente simulado.
    agente_simulado = RunnableLambda(simular_limite)

    # Ejecuta la consulta mediante la interfaz segura.
    resultado = ejecutar_agente_seguro(
        agente=agente_simulado,
        entrada="Analiza los indicadores municipales.",
    )

    # Comprueba la clasificación y el mensaje público.
    assert resultado["error"] == "limite_iteraciones"
    assert resultado["output"] == (
        "No fue posible completar la consulta "
        "dentro del límite de ejecución."
    )
    assert resultado["intermediate_steps"] == []


# ============================================================
# 9. INTEGRACIÓN DE HERRAMIENTAS MUNICIPALES
# ============================================================

def test_agente_consulta_solicitud_municipal() -> None:
    """Verifica la integración de la herramienta municipal.

    Simula una llamada a consultar_estado_solicitud
    para obtener el estado y el historial de SOL-12345.

    Comprueba que la herramienta se ejecute,
    que la observación incluya eventos del historial
    y que la respuesta conserve el identificador.
    """

    # Configura la llamada a la herramienta municipal.
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
                        "id": "llamada_solicitud_1",
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
        ]
    )

    # Construye el agente.
    agente = construir_agente_municipal(
        modelo=modelo_simulado
    )

    # Ejecuta la consulta mediante la interfaz segura.
    resultado = ejecutar_agente_seguro(
        agente=agente,
        entrada=(
            "Consulta el estado y el historial "
            "de la solicitud SOL-12345."
        ),
    )

    # Comprueba el identificador y la acción registrada.
    assert "SOL-12345" in resultado["output"]
    assert len(resultado["intermediate_steps"]) == 1

    # Recupera la acción y su observación.
    accion, observacion = resultado["intermediate_steps"][0]

    # Verifica la herramienta y los eventos del historial.
    assert accion.tool == "consultar_estado_solicitud"
    assert "Solicitud recibida." in observacion
    assert "Documentación validada." in observacion
    assert "error" not in resultado


# ============================================================
# 10. DISPONIBILIDAD DE HERRAMIENTAS SEGÚN SUPERVISIÓN
# ============================================================

def test_agente_sin_supervisor_expone_cuatro_herramientas() -> None:
    """Mantiene deshabilitada la cancelación sin supervisor.

    Construye el agente sin configurar una función
    de aprobación humana.

    Comprueba que solo se encuentren disponibles
    las cuatro herramientas de consulta y análisis.
    """

    # Configura un modelo simulado sin llamadas a herramientas.
    modelo_simulado = FakeToolCallingModel(
        responses=[AIMessage(content="Consulta disponible.")]
    )

    # Construye el agente sin supervisor de cancelaciones.
    agente = construir_agente_municipal(
        modelo=modelo_simulado,
    )

    # Obtiene los nombres de las herramientas disponibles.
    nombres = {herramienta.name for herramienta in agente.tools}

    # Comprueba que no se exponga la cancelación simulada.
    assert nombres == {
        "calcular_metricas",
        "consultar_documentacion",
        "analizar_datos",
        "consultar_estado_solicitud",
    }


def test_agente_con_supervisor_expone_cinco_herramientas() -> None:
    """Habilita la cancelación solo con supervisor configurado.

    Construye el agente con una función de aprobación
    humana que devuelve False.

    Comprueba que la herramienta de cancelación
    se encuentre disponible y que su interfaz
    pública solicite únicamente numero_solicitud.

    La disponibilidad de la herramienta no implica
    que las operaciones sean aprobadas.
    """

    # Configura un modelo simulado.
    modelo_simulado = FakeToolCallingModel(
        responses=[AIMessage(content="Supervisor configurado.")]
    )

    # Construye el agente con una función de aprobación.
    agente = construir_agente_municipal(
        modelo=modelo_simulado,
        solicitar_aprobacion_cancelacion=lambda: False,
    )

    # Recupera los nombres de las herramientas.
    nombres = {herramienta.name for herramienta in agente.tools}

    # Comprueba que ahora se expongan cinco herramientas.
    assert nombres == {
        "calcular_metricas",
        "consultar_documentacion",
        "analizar_datos",
        "consultar_estado_solicitud",
        "cancelar_solicitud_simulada",
    }

    # Localiza la herramienta de cancelación.
    herramienta_cancelacion = next(
        herramienta
        for herramienta in agente.tools
        if herramienta.name == "cancelar_solicitud_simulada"
    )

    # Comprueba los argumentos públicos de la herramienta.
    assert set(herramienta_cancelacion.args) == {
        "numero_solicitud",
    }


# ============================================================
# 11. CANCELACIÓN SIMULADA CON SUPERVISIÓN HUMANA
# ============================================================

def test_agente_no_cancela_sin_aprobacion_humana() -> None:
    """Bloquea una cancelación solicitada por el modelo sin aprobación.

    Simula una llamada del modelo a cancelar_solicitud_simulada.

    La función externa de aprobación devuelve False.

    Comprueba que:
        - La herramienta se ejecute una vez.
        - La operación devuelva el estado bloqueada.
        - La respuesta final informe el bloqueo.
    """

    # El modelo solicita cancelar una solicitud municipal.
    modelo_simulado = FakeToolCallingModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "cancelar_solicitud_simulada",
                        "args": {
                            "numero_solicitud": "SOL-12345",
                        },
                        "id": "llamada_cancelacion_1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(
                content=(
                    "La cancelación simulada fue bloqueada "
                    "porque no recibió aprobación humana."
                )
            ),
        ]
    )

    # Configura un supervisor que rechaza la cancelación.
    agente = construir_agente_municipal(
        modelo=modelo_simulado,
        solicitar_aprobacion_cancelacion=lambda: False,
    )

    # Ejecuta la solicitud de cancelación.
    resultado = agente.invoke({
        "entrada": "Cancela la solicitud SOL-12345.",
    })

    # Recupera las acciones ejecutadas.
    pasos = resultado["intermediate_steps"]

    # Comprueba que la operación haya sido bloqueada.
    assert len(pasos) == 1
    assert pasos[0][0].tool == "cancelar_solicitud_simulada"
    assert pasos[0][1]["estado"] == "bloqueada"
    assert "bloqueada" in resultado["output"]


def test_agente_cancela_simulacion_con_aprobacion_humana() -> None:
    """Permite una cancelación ficticia con aprobación externa.

    Simula una solicitud de cancelación municipal
    y configura una función de aprobación que devuelve True.

    Comprueba:
        - Que la aprobación se solicite una sola vez.
        - Que la herramienta se ejecute una vez.
        - Que el estado sea simulada.
        - Que se conserve el número de solicitud.
        - Que la respuesta informe la autorización.

    No realiza una cancelación real.
    """

    # Configura una llamada a la herramienta de cancelación.
    modelo_simulado = FakeToolCallingModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "cancelar_solicitud_simulada",
                        "args": {
                            "numero_solicitud": "SOL-12345",
                        },
                        "id": "llamada_cancelacion_aprobada_1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(
                content=(
                    "La cancelación de SOL-12345 fue "
                    "autorizada y simulada correctamente."
                )
            ),
        ]
    )

    # Registra las decisiones de aprobación solicitadas.
    decisiones = []

    def aprobar_cancelacion() -> bool:
        """Simula una aprobación externa al agente.

        Returns:
            bool:
                True para aprobar la cancelación simulada.

        Registra la aprobación en decisiones para comprobar
        posteriormente cuántas veces fue solicitada.
        """
        decisiones.append(True)
        return True

    # Construye el agente con la función de aprobación.
    agente = construir_agente_municipal(
        modelo=modelo_simulado,
        solicitar_aprobacion_cancelacion=aprobar_cancelacion,
    )

    # Ejecuta la solicitud de cancelación simulada.
    resultado = agente.invoke({
        "entrada": "Simula cancelar la solicitud SOL-12345.",
    })

    # Recupera las acciones realizadas.
    pasos = resultado["intermediate_steps"]

    # Comprueba una aprobación y una ejecución.
    assert len(decisiones) == 1
    assert len(pasos) == 1

    # Verifica la herramienta, el estado y la solicitud.
    assert pasos[0][0].tool == "cancelar_solicitud_simulada"
    assert pasos[0][1]["estado"] == "simulada"
    assert pasos[0][1]["numero_solicitud"] == "SOL-12345"

    # La respuesta final debe informar la autorización.
    assert "autorizada" in resultado["output"]
