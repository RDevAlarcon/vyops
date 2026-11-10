
from src.agente_con_herramientas import (
    analizar_datos,
    calcular_metricas,
    consultar_documentacion,
    construir_agente_municipal,
    ejecutar_agente_seguro,
    normalizar_respuesta_agente,
)

from langchain_core.messages import AIMessage
from langchain_core.language_models.fake_chat_models import (
    FakeMessagesListChatModel,
)

class FakeToolCallingModel(FakeMessagesListChatModel):
    """Simula un modelo compatible con llamadas a herramientas."""

    def bind_tools(
        self,
        tools: list,
        *,
        tool_choice: str | None = None,
        **kwargs,
    ):
        """Acepta herramientas para ejecutar pruebas sin una API externa."""
        return self

def test_calcular_metricas_promedio() -> None:
    """Verifica que la herramienta calcule correctamente el promedio."""
    resultado = calcular_metricas.invoke(
        {
            "valores": [100, 200, 300],
            "operacion": "promedio",
        }
    )

    assert resultado == "El resultado de promedio es 200.0."

def test_calcular_metricas_lista_vacia() -> None:
    """Verifica el manejo de una lista sin valores."""
    resultado = calcular_metricas.invoke(
        {
            "valores": [],
            "operacion": "promedio",
        }
    )

    assert resultado == (
        "Error: la lista de valores no puede estar vacía."
    )

def test_consultar_documentacion_tema_existente() -> None:
    """Verifica la consulta de un tema disponible en VyOps."""
    resultado = consultar_documentacion.invoke(
        {"tema": "langchain"}
    )

    assert "LangChain permite construir aplicaciones" in resultado
    assert "herramientas y agentes" in resultado

def test_consultar_documentacion_tema_desconocido() -> None:
    """Verifica la respuesta ante documentación no disponible."""
    resultado = consultar_documentacion.invoke(
        {"tema": "ordenanzas municipales"}
    )

    assert resultado == (
        "No se encontró documentación para el tema: "
        "ordenanzas municipales."
    )

def test_analizar_datos_aumento_solicitudes() -> None:
    """Verifica el aumento de solicitudes municipales entre períodos."""
    resultado = analizar_datos.invoke(
        {
            "valor_inicial": 120,
            "valor_final": 150,
        }
    )

    assert resultado["variacion_absoluta"] == 30
    assert resultado["variacion_porcentual"] == 25.0
    assert resultado["tendencia"] == "aumento"

def test_analizar_datos_disminucion_solicitudes() -> None:
    """Verifica la disminución de solicitudes entre períodos."""
    resultado = analizar_datos.invoke(
        {
            "valor_inicial": 200,
            "valor_final": 150,
        }
    )

    assert resultado["variacion_absoluta"] == -50
    assert resultado["variacion_porcentual"] == -25.0
    assert resultado["tendencia"] == "disminucion"

def test_analizar_datos_valor_inicial_cero() -> None:
    """Verifica el análisis cuando el valor inicial es cero."""
    resultado = analizar_datos.invoke(
        {
            "valor_inicial": 0,
            "valor_final": 50,
        }
    )

    assert resultado["variacion_absoluta"] == 50
    assert resultado["variacion_porcentual"] is None
    assert resultado["tendencia"] == "aumento"

def test_agente_selecciona_analizar_datos() -> None:
    """Verifica la ejecución y trazabilidad de analizar_datos."""
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

    agente = construir_agente_municipal(
        modelo=modelo_simulado
    )

    resultado = agente.invoke(
        {
            "entrada": (
                "Compara las solicitudes municipales: "
                "120 en enero y 150 en febrero."
            )
        }
    )

    pasos = resultado["intermediate_steps"]

    assert len(pasos) == 1
    assert pasos[0][0].tool == "analizar_datos"
    assert pasos[0][1]["variacion_porcentual"] == 25.0
    assert resultado["output"] == (
        "Las solicitudes aumentaron un 25 %."
    )

def test_agente_responde_sin_herramientas() -> None:
    """Verifica que el agente pueda responder sin ejecutar herramientas."""
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

    agente = construir_agente_municipal(
        modelo=modelo_simulado
    )

    resultado = agente.invoke(
        {
            "entrada": (
                "¿Cuál es el propósito general de VyOps?"
            )
        }
    )

    assert resultado["output"] == (
        "VyOps es un asistente de apoyo "
        "a la gestión municipal."
    )
    assert resultado["intermediate_steps"] == []

def test_agente_consulta_documentacion() -> None:
    """Verifica la ejecución y trazabilidad de una consulta documental."""
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

    agente = construir_agente_municipal(
        modelo=modelo_simulado
    )

    resultado = agente.invoke(
        {"entrada": "Consulta la documentación de VyOps."}
    )

    pasos = resultado["intermediate_steps"]

    assert len(pasos) == 1
    assert pasos[0][0].tool == "consultar_documentacion"
    assert "VyOps es un proyecto" in pasos[0][1]
    assert resultado["output"] == (
        "VyOps apoya el aprendizaje y desarrollo de IA."
    )

def test_agente_utiliza_multiples_herramientas() -> None:
    """Verifica la ejecución de dos herramientas en una consulta."""
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

    agente = construir_agente_municipal(
        modelo=modelo_simulado
    )

    resultado = agente.invoke(
        {
            "entrada": (
                "Analiza las solicitudes municipales de enero, "
                "febrero y marzo: 100, 120 y 140. "
                "Calcula el promedio y la variación entre enero y marzo."
            )
        }
    )

    pasos = resultado["intermediate_steps"]

    assert len(pasos) == 2
    assert [paso[0].tool for paso in pasos] == [
        "calcular_metricas",
        "analizar_datos",
    ]
    assert "120.0" in pasos[0][1]
    assert pasos[1][1]["variacion_porcentual"] == 40.0

def test_fallback_modelo_agente() -> None:
    """Verifica el respaldo cuando falla el modelo principal."""
    from langchain_core.runnables import RunnableLambda

    def modelo_principal_fallido(entrada):
        raise RuntimeError("Modelo principal no disponible")

    modelo_principal = RunnableLambda(modelo_principal_fallido)
    modelo_respaldo = RunnableLambda(
        lambda entrada: "Respuesta del modelo de respaldo"
    )

    modelo_con_respaldo = modelo_principal.with_fallbacks(
        [modelo_respaldo]
    )

    resultado = modelo_con_respaldo.invoke(
        "Consulta municipal de prueba"
    )

    assert resultado == "Respuesta del modelo de respaldo"

def test_agente_respeta_limite_iteraciones() -> None:
    """Verifica que el agente detenga ejecuciones repetitivas."""
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

    agente = construir_agente_municipal(
        modelo=modelo_simulado
    )

    resultado = agente.invoke(
        {"entrada": "Consulta repetidamente la documentación."}
    )

    assert len(resultado["intermediate_steps"]) == 5
    assert resultado["output"] == "Agent stopped due to max iterations."

def test_fallback_propaga_error_si_ambos_modelos_fallan() -> None:
    """Verifica el error cuando fallan ambos modelos."""
    import pytest
    from langchain_core.runnables import RunnableLambda

    def modelo_principal(entrada):
        raise ConnectionError("Modelo principal sin conexión")

    def modelo_respaldo(entrada):
        raise ConnectionError("Modelo de respaldo sin conexión")

    modelo = RunnableLambda(
        modelo_principal
    ).with_fallbacks([
        RunnableLambda(modelo_respaldo)
    ])

    with pytest.raises(ConnectionError):
        modelo.invoke("Consulta municipal de prueba")

def test_ejecutar_agente_seguro_error_conexion() -> None:
    """Verifica una respuesta segura ante errores de conexión."""
    from langchain_core.runnables import RunnableLambda

    def simular_error(entrada: dict) -> dict:
        raise ConnectionError(
            "No fue posible establecer conexión con Gemini"
        )

    agente_simulado = RunnableLambda(simular_error)

    resultado = ejecutar_agente_seguro(
        agente=agente_simulado,
        entrada="Consulta de solicitudes municipales",
    )

    assert resultado["error"] == "conexion"
    assert resultado["output"] == (
        "No fue posible conectar con el servicio de IA."
    )
    assert resultado["intermediate_steps"] == []
    assert "Gemini" not in resultado["output"]

def test_ejecutar_agente_seguro_timeout() -> None:
    """Verifica una respuesta segura ante un tiempo de espera agotado."""
    from langchain_core.runnables import RunnableLambda

    def simular_timeout(entrada: dict) -> dict:
        raise TimeoutError(
            "La conexión con el modelo excedió el tiempo permitido"
        )

    agente_simulado = RunnableLambda(simular_timeout)

    resultado = ejecutar_agente_seguro(
        agente=agente_simulado,
        entrada="Analiza los indicadores municipales",
    )

    assert resultado["error"] == "timeout"
    assert resultado["output"] == (
        "La consulta excedió el tiempo de espera."
    )
    assert resultado["intermediate_steps"] == []
    assert "modelo" not in resultado["output"].lower()

def test_ejecutar_agente_seguro_error_inesperado() -> None:
    """Verifica una respuesta segura ante errores inesperados."""
    from langchain_core.runnables import RunnableLambda

    def simular_error(entrada: dict) -> dict:
        raise RuntimeError(
            "Error interno inesperado durante el procesamiento"
        )

    agente_simulado = RunnableLambda(simular_error)

    resultado = ejecutar_agente_seguro(
        agente=agente_simulado,
        entrada="Genera un análisis municipal",
    )

    assert resultado["error"] == "inesperado"
    assert resultado["output"] == (
        "No fue posible procesar la solicitud."
    )
    assert resultado["intermediate_steps"] == []
    assert "Error interno" not in resultado["output"]

def test_agente_registra_error_inesperado(caplog) -> None:
    """Verifica el registro de errores sin exponerlos al usuario."""
    import logging
    from langchain_core.runnables import RunnableLambda

    def simular_error(entrada: dict) -> dict:
        raise RuntimeError("Fallo interno simulado")

    agente_simulado = RunnableLambda(simular_error)

    with caplog.at_level(
        logging.ERROR,
        logger="src.agente_con_herramientas",
    ):
        resultado = ejecutar_agente_seguro(
            agente=agente_simulado,
            entrada="Consulta municipal de prueba",
        )

    assert resultado["error"] == "inesperado"

    assert (
        "Error inesperado durante la ejecución del agente."
        in caplog.text
    )

    assert "RuntimeError" in caplog.text

    assert "Fallo interno simulado" not in resultado["output"]

def test_normalizar_respuesta_texto_simple() -> None:
    """Conserva una respuesta que ya contiene texto."""
    resultado = normalizar_respuesta_agente(
        "VyOps está funcionando."
    )

    assert resultado == "VyOps está funcionando."

def test_normalizar_respuesta_multiples_bloques() -> None:
    """Une bloques de texto sin exponer metadatos."""
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

    resultado = normalizar_respuesta_agente(contenido)

    assert resultado == (
        "Se registraron 150 solicitudes.\n"
        "La variación fue de un 25 %."
    )
    assert "dato-interno" not in resultado

def test_normalizar_respuesta_sin_texto() -> None:
    """Devuelve texto vacío cuando no hay bloques de texto."""
    contenido = [
        {
            "type": "tool_use",
            "name": "analizar_datos",
        }
    ]

    resultado = normalizar_respuesta_agente(contenido)

    assert resultado == ""

def test_ejecucion_segura_normaliza_y_conserva_trazas() -> None:
    """Verifica la normalización sin perder la trazabilidad."""
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

    agente = construir_agente_municipal(
        modelo=modelo_simulado
    )

    resultado = ejecutar_agente_seguro(
        agente=agente,
        entrada="Calcula el promedio de 80, 100 y 120 solicitudes.",
    )

    assert resultado["output"] == (
        "El promedio mensual fue de 100 solicitudes."
    )
    assert isinstance(resultado["output"], str)
    assert len(resultado["intermediate_steps"]) == 1
    assert resultado["intermediate_steps"][0][0].tool == (
        "calcular_metricas"
    )
    assert "dato-interno" not in resultado["output"]
    assert "error" not in resultado

def test_ejecucion_segura_detecta_limite_iteraciones() -> None:
    """Detecta una ejecución detenida por límite de iteraciones."""
    from langchain_core.runnables import RunnableLambda

    def simular_limite(entrada: dict) -> dict:
        return {
            "output": "Agent stopped due to max iterations.",
            "intermediate_steps": [],
        }

    agente_simulado = RunnableLambda(simular_limite)

    resultado = ejecutar_agente_seguro(
        agente=agente_simulado,
        entrada="Analiza los indicadores municipales.",
    )

    assert resultado["error"] == "limite_iteraciones"
    assert resultado["output"] == (
        "No fue posible completar la consulta "
        "dentro del límite de ejecución."
    )
    assert resultado["intermediate_steps"] == []

def test_agente_consulta_solicitud_municipal() -> None:
    """Verifica la integración de la herramienta municipal."""
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

    agente = construir_agente_municipal(
        modelo=modelo_simulado
    )

    resultado = ejecutar_agente_seguro(
        agente=agente,
        entrada=(
            "Consulta el estado y el historial "
            "de la solicitud SOL-12345."
        ),
    )

    assert "SOL-12345" in resultado["output"]
    assert len(resultado["intermediate_steps"]) == 1

    accion, observacion = resultado["intermediate_steps"][0]

    assert accion.tool == "consultar_estado_solicitud"
    assert "Solicitud recibida." in observacion
    assert "Documentación validada." in observacion
    assert "error" not in resultado

def test_agente_sin_supervisor_expone_cuatro_herramientas() -> None:
    """Mantiene deshabilitada la cancelación sin supervisor."""
    modelo_simulado = FakeToolCallingModel(
        responses=[AIMessage(content="Consulta disponible.")]
    )

    agente = construir_agente_municipal(
        modelo=modelo_simulado,
    )

    nombres = {herramienta.name for herramienta in agente.tools}

    assert nombres == {
        "calcular_metricas",
        "consultar_documentacion",
        "analizar_datos",
        "consultar_estado_solicitud",
    }


def test_agente_con_supervisor_expone_cinco_herramientas() -> None:
    """Habilita la cancelación solo con supervisor configurado."""
    modelo_simulado = FakeToolCallingModel(
        responses=[AIMessage(content="Supervisor configurado.")]
    )

    agente = construir_agente_municipal(
        modelo=modelo_simulado,
        solicitar_aprobacion_cancelacion=lambda: False,
    )

    nombres = {herramienta.name for herramienta in agente.tools}

    assert nombres == {
        "calcular_metricas",
        "consultar_documentacion",
        "analizar_datos",
        "consultar_estado_solicitud",
        "cancelar_solicitud_simulada",
    }

    herramienta_cancelacion = next(
        herramienta
        for herramienta in agente.tools
        if herramienta.name == "cancelar_solicitud_simulada"
    )

    assert set(herramienta_cancelacion.args) == {
        "numero_solicitud",
    }

def test_agente_no_cancela_sin_aprobacion_humana() -> None:
    """Bloquea una cancelación solicitada por el modelo sin aprobación."""
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

    agente = construir_agente_municipal(
        modelo=modelo_simulado,
        solicitar_aprobacion_cancelacion=lambda: False,
    )

    resultado = agente.invoke({
        "entrada": "Cancela la solicitud SOL-12345.",
    })

    pasos = resultado["intermediate_steps"]

    assert len(pasos) == 1
    assert pasos[0][0].tool == "cancelar_solicitud_simulada"
    assert pasos[0][1]["estado"] == "bloqueada"
    assert "bloqueada" in resultado["output"]

def test_agente_cancela_simulacion_con_aprobacion_humana() -> None:
    """Permite una cancelación ficticia con aprobación externa."""
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

    decisiones = []

    def aprobar_cancelacion() -> bool:
        """Simula una aprobación externa al agente."""
        decisiones.append(True)
        return True

    agente = construir_agente_municipal(
        modelo=modelo_simulado,
        solicitar_aprobacion_cancelacion=aprobar_cancelacion,
    )

    resultado = agente.invoke({
        "entrada": "Simula cancelar la solicitud SOL-12345.",
    })

    pasos = resultado["intermediate_steps"]

    assert len(decisiones) == 1
    assert len(pasos) == 1
    assert pasos[0][0].tool == "cancelar_solicitud_simulada"
    assert pasos[0][1]["estado"] == "simulada"
    assert pasos[0][1]["numero_solicitud"] == "SOL-12345"
    assert "autorizada" in resultado["output"]