
"""Pruebas de la memoria conversacional temporal de VyOps.

Este módulo verifica el comportamiento de la memoria
implementada en src.memoria_agente.

La memoria permite mantener el contexto de una conversación
a través de múltiples invocaciones que utilizan
un mismo identificador de sesión.

Las pruebas cubren los siguientes escenarios:

    1. Independencia de historiales entre sesiones.
    2. Reutilización del historial de una misma sesión.
    3. Eliminación y reinicio de un historial.
    4. Rechazo de identificadores de sesión vacíos.
    5. Conservación de mensajes entre invocaciones.
    6. Aislamiento de conversaciones entre sesiones.
    7. Integración de memoria y herramientas municipales.

Se utilizan componentes de LangChain y un modelo
simulado para comprobar el comportamiento del agente
sin realizar llamadas a modelos generativos externos.

Los historiales creados durante las pruebas se eliminan
mediante bloques finally, evitando que las sesiones
de prueba permanezcan registradas después de ejecutarse.

Estas pruebas verifican el aislamiento lógico
por identificador de sesión. No comprueban persistencia
entre reinicios del proceso, autenticación de usuarios
ni aislamiento entre organizaciones.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Framework utilizado para verificar excepciones esperadas.
import pytest

# Funciones de administración de historiales conversacionales.
from src.memoria_agente import (
    eliminar_historial,
    obtener_historial,
)

# Permite utilizar una función Python como componente
# ejecutable dentro de una cadena de LangChain.
from langchain_core.runnables import RunnableLambda

# Construye un agente que conserva el historial
# asociado al identificador de sesión.
from src.memoria_agente import construir_agente_con_memoria

# Representa mensajes producidos por un modelo de IA.
from langchain_core.messages import AIMessage

# Decorador de LangChain para definir herramientas.
# Se conserva el import original del archivo.
from langchain_core.tools import tool

# Construye el agente municipal con herramientas.
from src.agente_con_herramientas import construir_agente_municipal

# Modelo simulado que devuelve respuestas y llamadas
# a herramientas previamente definidas.
from tests.test_agente_con_herramientas import FakeToolCallingModel


# ============================================================
# 2. AISLAMIENTO BÁSICO DE HISTORIALES
# ============================================================

def test_sesiones_tienen_historiales_independientes() -> None:
    """Verifica que dos sesiones no compartan historial.

    Obtiene dos historiales utilizando identificadores
    de sesión diferentes.

    Agrega un mensaje únicamente a la primera sesión
    y comprueba:

        - Los historiales son objetos distintos.
        - La primera sesión contiene un mensaje.
        - La segunda sesión permanece vacía.

    El bloque finally elimina ambos historiales
    independientemente del resultado de las aserciones.
    """

    # Obtiene un historial para cada identificador de sesión.
    primera = obtener_historial("prueba_usuario_001")
    segunda = obtener_historial("prueba_usuario_002")

    try:
        # Agrega un mensaje únicamente a la primera sesión.
        primera.add_user_message("Mi solicitud es SOL-12345.")

        # Verifica que las sesiones no compartan el mismo objeto.
        assert primera is not segunda

        # Comprueba que el mensaje se almacene solo
        # en el historial correspondiente.
        assert len(primera.messages) == 1
        assert len(segunda.messages) == 0

    finally:
        # Elimina los historiales utilizados en la prueba.
        eliminar_historial("prueba_usuario_001")
        eliminar_historial("prueba_usuario_002")


# ============================================================
# 3. REUTILIZACIÓN DE HISTORIALES
# ============================================================

def test_misma_sesion_reutiliza_historial() -> None:
    """Verifica que una sesión conserve sus mensajes.

    Obtiene un historial, agrega un mensaje y vuelve
    a solicitar el historial utilizando el mismo session_id.

    Comprueba que:

        - Se reutiliza el mismo objeto de historial.
        - El mensaje anterior continúa disponible.
        - El contenido almacenado no cambia.

    Este comportamiento permite mantener continuidad
    entre interacciones de una misma conversación.
    """

    # Identificador utilizado durante toda la prueba.
    session_id = "prueba_reutilizacion"

    try:
        # Obtiene el historial y agrega un mensaje.
        historial = obtener_historial(session_id)
        historial.add_user_message("Hola, soy un vecino.")

        # Solicita nuevamente el historial de la misma sesión.
        recuperado = obtener_historial(session_id)

        # Comprueba que se reutilice el objeto original.
        assert recuperado is historial

        # Verifica que el mensaje anterior permanezca disponible.
        assert len(recuperado.messages) == 1
        assert recuperado.messages[0].content == "Hola, soy un vecino."

    finally:
        # Elimina el historial creado durante la prueba.
        eliminar_historial(session_id)


# ============================================================
# 4. ELIMINACIÓN Y REINICIO DE SESIONES
# ============================================================

def test_eliminar_historial_reinicia_sesion() -> None:
    """Verifica que eliminar una sesión borre su historial.

    Crea un historial con un mensaje y posteriormente
    elimina la sesión mediante eliminar_historial().

    Al solicitar nuevamente el mismo identificador,
    comprueba que:

        - Se obtiene un objeto de historial diferente.
        - El nuevo historial no contiene mensajes.

    La prueba verifica el reinicio del estado conversacional
    asociado al identificador de sesión.
    """

    # Identificador del historial que será eliminado.
    session_id = "prueba_eliminacion"

    try:
        # Crea un historial con un mensaje temporal.
        historial = obtener_historial(session_id)
        historial.add_user_message("Mensaje temporal.")

        # Elimina el historial registrado.
        eliminar_historial(session_id)

        # Obtiene nuevamente el historial de la misma sesión.
        nuevo_historial = obtener_historial(session_id)

        # Comprueba que se haya creado un objeto diferente.
        assert nuevo_historial is not historial

        # Verifica que el nuevo historial esté vacío.
        assert len(nuevo_historial.messages) == 0

    finally:
        # Limpia cualquier historial que permanezca asociado
        # al identificador utilizado.
        eliminar_historial(session_id)


# ============================================================
# 5. VALIDACIÓN DE IDENTIFICADORES DE SESIÓN
# ============================================================

def test_rechaza_identificador_vacio() -> None:
    """Verifica que una sesión necesite un identificador válido.

    Intenta obtener un historial utilizando una cadena
    compuesta únicamente por espacios.

    Comprueba que obtener_historial() genere ValueError.

    Este escenario verifica el rechazo de identificadores
    sin contenido significativo.
    """

    # La función debe rechazar un identificador
    # compuesto solamente por espacios.
    with pytest.raises(ValueError):
        obtener_historial("   ")


# ============================================================
# 6. CONSERVACIÓN DE CONVERSACIONES ENTRE INVOCACIONES
# ============================================================

def test_memoria_conserva_conversacion() -> None:
    """Verifica que una sesión recuerde mensajes anteriores.

    Construye un agente simulado mediante RunnableLambda.

    El agente responde indicando la cantidad de mensajes
    recibidos en el campo chat_history.

    Se realizan dos invocaciones con el mismo session_id.

    Verificaciones:
        - La primera invocación recibe cero mensajes anteriores.
        - La segunda invocación recibe dos mensajes anteriores.
        - El historial final contiene cuatro mensajes.
        - El primer mensaje conserva su contenido original.

    Los cuatro mensajes corresponden a dos entradas
    del usuario y dos respuestas del agente.
    """

    # Identificador compartido por ambas invocaciones.
    session_id = "prueba_conversacion"

    def responder(datos: dict) -> dict:
        """Devuelve la cantidad de mensajes anteriores recibidos.

        Args:
            datos (dict):
                Entrada del agente simulado.
                Puede incluir el campo chat_history.

        Returns:
            dict:
                Diccionario con la clave output,
                cuyo valor informa la cantidad
                de mensajes anteriores.

        Esta función no llama a ningún modelo externo.
        """

        # Recupera el historial entregado al agente.
        # Si no existe, utiliza una lista vacía.
        historial = datos.get("chat_history", [])

        # Informa la cantidad de mensajes previos.
        return {
            "output": f"Mensajes anteriores: {len(historial)}"
        }

    # Convierte la función responder en un componente
    # ejecutable de LangChain.
    agente_simulado = RunnableLambda(responder)

    # Incorpora la gestión de memoria conversacional.
    agente_con_memoria = construir_agente_con_memoria(
        agente_simulado
    )

    # Configura el identificador de sesión
    # que utilizarán ambas invocaciones.
    configuracion = {
        "configurable": {
            "session_id": session_id,
        }
    }

    try:
        # Primera interacción: todavía no existen
        # mensajes anteriores en la sesión.
        primera = agente_con_memoria.invoke(
            {"entrada": "Hola, soy un vecino."},
            config=configuracion,
        )

        # Segunda interacción: el historial ya contiene
        # la primera pregunta y su respuesta.
        segunda = agente_con_memoria.invoke(
            {"entrada": "¿Recuerdas mi mensaje anterior?"},
            config=configuracion,
        )

        # Comprueba la cantidad de mensajes anteriores
        # recibidos en cada invocación.
        assert primera["output"] == "Mensajes anteriores: 0"
        assert segunda["output"] == "Mensajes anteriores: 2"

        # Obtiene el historial completo de la sesión.
        historial = obtener_historial(session_id)

        # Dos interacciones generan cuatro mensajes.
        assert len(historial.messages) == 4

        # Verifica que se conserve el primer mensaje.
        assert historial.messages[0].content == (
            "Hola, soy un vecino."
        )

    finally:
        # Elimina la sesión al terminar la prueba.
        eliminar_historial(session_id)


# ============================================================
# 7. AISLAMIENTO DE CONVERSACIONES ENTRE SESIONES
# ============================================================

def test_memoria_aisla_sesiones() -> None:
    """Verifica que las conversaciones no se mezclen entre sesiones.

    Construye un agente simulado que informa la cantidad
    de mensajes anteriores recibidos.

    Se utilizan dos identificadores independientes:

        - sesion_a: realiza dos interacciones.
        - sesion_b: realiza una interacción.

    Verificaciones:
        - La segunda interacción de A recibe dos mensajes previos.
        - La primera interacción de B recibe cero mensajes previos.
        - El historial de A contiene cuatro mensajes.
        - El historial de B contiene dos mensajes.
        - El identificador de solicitud de A no aparece
          en los mensajes almacenados para B.

    La prueba comprueba el aislamiento conversacional
    por session_id dentro del mecanismo de memoria.
    """

    def responder(datos: dict) -> dict:
        """Informa la cantidad de mensajes previos de la sesión.

        Args:
            datos (dict):
                Datos entregados al agente simulado,
                incluyendo opcionalmente chat_history.

        Returns:
            dict:
                Respuesta con el número de mensajes
                anteriores disponibles.
        """

        # Obtiene los mensajes anteriores de la sesión actual.
        historial = datos.get("chat_history", [])

        # Devuelve el conteo de mensajes.
        return {
            "output": f"Mensajes anteriores: {len(historial)}"
        }

    # Construye el agente simulado.
    agente_simulado = RunnableLambda(responder)

    # Agrega memoria conversacional al agente.
    agente_con_memoria = construir_agente_con_memoria(
        agente_simulado
    )

    # Define dos sesiones independientes.
    sesion_a = "prueba_aislamiento_a"
    sesion_b = "prueba_aislamiento_b"

    try:
        # Configuración correspondiente a la sesión A.
        configuracion_a = {
            "configurable": {"session_id": sesion_a}
        }

        # Configuración correspondiente a la sesión B.
        configuracion_b = {
            "configurable": {"session_id": sesion_b}
        }

        # Primera interacción de la sesión A.
        # Incluye un identificador de solicitud municipal.
        agente_con_memoria.invoke(
            {"entrada": "Mi solicitud es SOL-12345."},
            config=configuracion_a,
        )

        # Segunda interacción de la sesión A.
        # Debe recibir el historial de su interacción anterior.
        respuesta_a = agente_con_memoria.invoke(
            {"entrada": "¿Recuerdas mi solicitud?"},
            config=configuracion_a,
        )

        # Primera interacción de la sesión B.
        # No debe recibir mensajes de la sesión A.
        respuesta_b = agente_con_memoria.invoke(
            {"entrada": "¿Qué mensajes anteriores tengo?"},
            config=configuracion_b,
        )

        # Comprueba que cada sesión reciba
        # la cantidad correcta de mensajes previos.
        assert respuesta_a["output"] == "Mensajes anteriores: 2"
        assert respuesta_b["output"] == "Mensajes anteriores: 0"

        # Recupera ambos historiales para inspeccionarlos.
        historial_a = obtener_historial(sesion_a)
        historial_b = obtener_historial(sesion_b)

        # Comprueba el número de mensajes almacenados
        # en cada conversación.
        assert len(historial_a.messages) == 4
        assert len(historial_b.messages) == 2

        # El identificador de solicitud debe permanecer
        # en la sesión A y no aparecer en la sesión B.
        assert "SOL-12345" in historial_a.messages[0].content
        assert "SOL-12345" not in str(historial_b.messages)

    finally:
        # Elimina ambos historiales para evitar
        # que afecten a otras pruebas.
        eliminar_historial(sesion_a)
        eliminar_historial(sesion_b)


# ============================================================
# 8. INTEGRACIÓN DE MEMORIA Y HERRAMIENTAS MUNICIPALES
# ============================================================

def test_agente_municipal_con_memoria() -> None:
    """Verifica herramientas y memoria en una misma sesión.

    Construye un agente municipal utilizando
    FakeToolCallingModel, un modelo simulado
    con respuestas previamente definidas.

    El escenario representa dos interacciones:

        Primera interacción:
            - El usuario consulta una solicitud municipal.
            - El modelo solicita ejecutar una herramienta.
            - La herramienta devuelve una observación.
            - El agente genera una respuesta sobre la solicitud.

        Segunda interacción:
            - El usuario pregunta qué solicitud consultó.
            - El modelo devuelve una respuesta que menciona
              el mismo identificador de solicitud.

    Verificaciones:
        - Ambas respuestas contienen SOL-12345.
        - La primera interacción registra una acción intermedia.
        - La herramienta invocada es consultar_estado_solicitud.
        - La observación contiene "Solicitud recibida.".
        - El historial contiene cuatro mensajes.
        - Se conserva el orden de las interacciones.

    La prueba utiliza respuestas simuladas del modelo
    y no demuestra por sí sola que un modelo real
    pueda recordar o interpretar el contexto.
    """

    # Identificador de sesión utilizado
    # durante ambas interacciones municipales.
    session_id = "prueba_agente_municipal"

    # Configura un modelo simulado con tres respuestas:
    #
    # 1. Solicitud de ejecución de una herramienta.
    # 2. Respuesta posterior a la ejecución.
    # 3. Respuesta de la segunda interacción.
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

    # Construye el agente municipal utilizando
    # el modelo simulado en lugar de un servicio externo.
    agente = construir_agente_municipal(
        modelo=modelo_simulado
    )

    # Incorpora memoria conversacional al agente.
    agente_con_memoria = construir_agente_con_memoria(agente)

    # Configura el identificador compartido
    # por ambas invocaciones.
    configuracion = {
        "configurable": {
            "session_id": session_id,
        }
    }

    try:
        # Primera interacción:
        # solicita consultar el estado y el historial
        # de una solicitud municipal.
        primera = agente_con_memoria.invoke(
            {
                "entrada": (
                    "Consulta el estado y el historial "
                    "de la solicitud SOL-12345."
                )
            },
            config=configuracion,
        )

        # Segunda interacción:
        # pregunta por la solicitud consultada anteriormente.
        segunda = agente_con_memoria.invoke(
            {
                "entrada": (
                    "¿Recuerdas qué solicitud consulté?"
                )
            },
            config=configuracion,
        )

        # Comprueba que ambas respuestas mencionen
        # el identificador de la solicitud.
        assert "SOL-12345" in primera["output"]
        assert "SOL-12345" in segunda["output"]

        # La primera interacción debe registrar
        # una única acción intermedia.
        assert len(primera["intermediate_steps"]) == 1

        # Extrae la acción ejecutada y su observación.
        accion, observacion = primera["intermediate_steps"][0]

        # Comprueba el nombre de la herramienta utilizada.
        assert accion.tool == "consultar_estado_solicitud"

        # Verifica el contenido esperado de la observación.
        assert "Solicitud recibida." in observacion

        # Recupera el historial de la sesión municipal.
        historial = obtener_historial(session_id)

        # Dos interacciones deben generar cuatro mensajes
        # en el historial conversacional.
        assert len(historial.messages) == 4

        # Comprueba que el primer mensaje corresponda
        # a la consulta municipal inicial.
        assert historial.messages[0].content.startswith(
            "Consulta el estado"
        )

        # La primera respuesta debe conservar
        # el identificador de la solicitud.
        assert "SOL-12345" in historial.messages[1].content

        # El tercer mensaje debe corresponder
        # a la segunda pregunta del usuario.
        assert historial.messages[2].content == (
            "¿Recuerdas qué solicitud consulté?"
        )

    finally:
        # Elimina el historial de la sesión
        # para mantener aisladas las pruebas.
        eliminar_historial(session_id)
