
"""Implementación del agente municipal de VyOps con LangChain.

Este módulo proporciona las herramientas y funciones necesarias
para construir y ejecutar un agente de inteligencia artificial
orientado al apoyo de la gestión municipal en Chile.

Responsabilidades principales:

    1. Calcular métricas estadísticas sobre datos numéricos.
    2. Consultar documentación local disponible en VyOps.
    3. Analizar variaciones absolutas y porcentuales.
    4. Integrar consultas de solicitudes municipales simuladas.
    5. Construir un agente LangChain con herramientas.
    6. Configurar modelos Gemini con respaldo automático.
    7. Incorporar supervisión humana para cancelaciones simuladas.
    8. Limitar las iteraciones y el tiempo de ejecución.
    9. Gestionar errores mediante respuestas públicas controladas.
    10. Normalizar respuestas textuales sin exponer metadatos.

El agente utiliza un prompt de sistema que establece
restricciones para evitar afirmaciones sobre acceso
a información municipal no disponible.

La herramienta de cancelación simulada solamente
se incorpora cuando existe una función de aprobación
humana configurada.

Las operaciones municipales incluidas corresponden
a herramientas de demostración y simulación.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Función estadística para calcular promedios.
from statistics import mean

# Restringe los nombres de operaciones estadísticas admitidas.
from typing import Literal

# Decorador para registrar funciones como herramientas LangChain.
from langchain_core.tools import tool

# Componentes para construir y ejecutar agentes con herramientas.
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent

# Plantillas de mensajes y espacios para historial y acciones.
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Integración de modelos Gemini mediante LangChain.
from langchain_google_genai import ChatGoogleGenerativeAI

# Tipo de Runnable con mecanismos de respaldo.
from langchain_core.runnables import RunnableWithFallbacks

# Interfaz base para modelos de chat.
from langchain_core.language_models import BaseChatModel

# Registro de eventos, advertencias y errores del agente.
import logging

# Herramienta para consultar solicitudes municipales simuladas.
from src.herramienta_solicitudes import consultar_estado_solicitud

# Tipo para representar una función de aprobación humana.
from collections.abc import Callable

# Constructor de la herramienta de cancelación supervisada.
from src.herramienta_cancelacion import construir_herramienta_cancelacion


# ============================================================
# 2. HERRAMIENTA DE CÁLCULO DE MÉTRICAS
# ============================================================

@tool
def calcular_metricas(
    valores: list[float],
    operacion: Literal["suma", "promedio", "maximo", "minimo"],
) -> str:
    """Calcula una métrica estadística sobre una lista de valores numéricos.

    Permite ejecutar cuatro operaciones:

        - suma: suma de los valores proporcionados.
        - promedio: media aritmética de los valores.
        - maximo: mayor valor de la lista.
        - minimo: menor valor de la lista.

    Args:
        valores:
            Lista de números sobre los que se realiza el cálculo.
        operacion:
            Nombre de la operación estadística solicitada.

    Returns:
        str:
            Mensaje que contiene el resultado del cálculo.

            Si la lista está vacía, devuelve un mensaje de error.
            Si la operación no está disponible, informa
            que no se encuentra admitida.

    La herramienta no modifica los valores originales.
    """

    # Evita realizar cálculos sobre una lista sin elementos.
    if not valores:
        return "Error: la lista de valores no puede estar vacía."

    # Relaciona cada operación admitida con su función.
    operaciones = {
        "suma": sum,
        "promedio": mean,
        "maximo": max,
        "minimo": min,
    }

    # Selecciona y ejecuta la operación solicitada.
    try:
        resultado = operaciones[operacion](valores)

    # Informa cuando la operación no está registrada.
    except KeyError:
        return f"Error: operación no admitida: {operacion}."

    # Devuelve el resultado en un formato textual.
    return f"El resultado de {operacion} es {resultado}."


# ============================================================
# 3. HERRAMIENTA DE CONSULTA DOCUMENTAL
# ============================================================

@tool
def consultar_documentacion(tema: str) -> str:
    """Consulta información interna de VyOps sobre un tema específico.

    Utiliza un diccionario local con documentación
    demostrativa sobre VyOps, LangChain y agentes.

    Args:
        tema:
            Nombre del tema que se desea consultar.

    Returns:
        str:
            Contenido documental asociado al tema.

            Si el tema no existe, devuelve un mensaje
            que informa la ausencia de documentación.

    La búsqueda ignora espacios al inicio y al final
    y no distingue entre mayúsculas y minúsculas.

    Esta implementación no consulta fuentes externas
    ni representa una búsqueda RAG sobre documentos municipales.
    """

    # Repositorio documental local utilizado por la herramienta.
    documentacion = {
        "vyops": (
            "VyOps es un proyecto de aprendizaje y desarrollo "
            "de soluciones de inteligencia artificial."
        ),
        "langchain": (
            "LangChain permite construir aplicaciones con modelos "
            "de lenguaje, cadenas, herramientas y agentes."
        ),
        "agentes": (
            "Un agente puede seleccionar herramientas durante "
            "la ejecución según la solicitud del usuario."
        ),
    }

    # Normaliza el tema para facilitar la coincidencia.
    tema_normalizado = tema.strip().lower()

    # Busca el contenido correspondiente.
    try:
        return documentacion[tema_normalizado]

    # Informa cuando no existe documentación para el tema.
    except KeyError:
        return f"No se encontró documentación para el tema: {tema}."


# ============================================================
# 4. HERRAMIENTA DE ANÁLISIS DE DATOS
# ============================================================

@tool
def analizar_datos(valor_inicial: float, valor_final: float) -> dict:
    """Analiza la variación absoluta y porcentual entre dos valores.

    Calcula el cambio de un indicador entre dos períodos
    y clasifica su tendencia.

    Args:
        valor_inicial:
            Valor del indicador en el período inicial.
        valor_final:
            Valor del indicador en el período final.

    Returns:
        dict:
            Diccionario que contiene:

            - valor_inicial: valor recibido inicialmente.
            - valor_final: valor recibido al finalizar.
            - variacion_absoluta: diferencia entre valores.
            - variacion_porcentual: cambio porcentual.
            - tendencia: aumento, disminucion o sin cambios.

    La variación porcentual utiliza el valor absoluto
    del denominador inicial.

    Si valor_inicial es cero, la variación porcentual
    se representa mediante None para evitar
    una división por cero.

    Los resultados numéricos calculados se redondean
    a dos posiciones decimales.
    """

    # Calcula la diferencia entre el valor final y el inicial.
    variacion_absoluta = valor_final - valor_inicial

    # Evita dividir por cero cuando no existe una base inicial.
    if valor_inicial == 0:
        variacion_porcentual = None
    else:
        # Calcula el cambio porcentual respecto de la base.
        variacion_porcentual = (
            variacion_absoluta / abs(valor_inicial)
        ) * 100

    # Clasifica la dirección del cambio observado.
    if variacion_absoluta > 0:
        tendencia = "aumento"
    elif variacion_absoluta < 0:
        tendencia = "disminucion"
    else:
        tendencia = "sin cambios"

    # Devuelve los valores y el análisis calculado.
    return {
        "valor_inicial": valor_inicial,
        "valor_final": valor_final,
        "variacion_absoluta": round(variacion_absoluta, 2),
        "variacion_porcentual": (
            round(variacion_porcentual, 2)
            if variacion_porcentual is not None
            else None
        ),
        "tendencia": tendencia,
    }


# ============================================================
# 5. PROMPT DEL AGENTE MUNICIPAL
# ============================================================

# Define las instrucciones del sistema y la estructura
# de los mensajes que recibirá el agente.
#
# El prompt establece el contexto municipal chileno,
# las herramientas disponibles y las restricciones
# relacionadas con la veracidad de la información.
#
# chat_history permite incorporar conversaciones anteriores.
# agent_scratchpad almacena los mensajes intermedios
# utilizados por el agente durante sus acciones.
prompt_agente = ChatPromptTemplate.from_messages(
    [
    (
        "system",
        (
            "Eres VyOps, un asistente inteligente de apoyo "
            "a la gestión municipal en Chile. "
            "Tu objetivo es ayudar a funcionarios municipales "
            "a consultar información, analizar datos, "
            "interpretar indicadores y apoyar la gestión operativa. "
            "Responde siempre en español de Chile. "
            "Utiliza calcular_metricas para operaciones estadísticas. "
            "Utiliza analizar_datos para comparar indicadores "
            "entre períodos. "
            "Utiliza consultar_documentacion para consultar "
            "la documentación local disponible en VyOps. "
            "No afirmes tener acceso a sistemas municipales, "
            "expedientes, bases de datos o normativa actualizada "
            "si no están disponibles mediante herramientas. "
            "No inventes datos, documentos ni resultados. "
            "No presentes recomendaciones como decisiones "
            "administrativas oficiales. "
            "Cuando una solicitud requiera herramientas "
            "que todavía no existen, informa esa limitación. "
            "Para preguntas generales, responde directamente."
            "Utiliza consultar_estado_solicitud para consultar "
            "el estado y el historial de solicitudes municipales simuladas. "
        ),
    ),
        MessagesPlaceholder(
            variable_name="chat_history",
            optional=True,
        ),
        ("human", "{entrada}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)


# ============================================================
# 6. CONSTRUCCIÓN DEL MODELO CON RESPALDO
# ============================================================

def construir_modelo_agente(
    modelo_principal: str = "gemini-3.5-flash-lite",
    modelo_respaldo: str = "gemini-2.5-flash",
) -> RunnableWithFallbacks:
    """Construye el modelo del agente municipal con respaldo automático.

    Configura dos instancias de ChatGoogleGenerativeAI:

        - Modelo principal: primera alternativa de ejecución.
        - Modelo de respaldo: alternativa ante fallos del principal.

    Args:
        modelo_principal:
            Identificador del modelo Gemini principal.
        modelo_respaldo:
            Identificador del modelo Gemini alternativo.

    Returns:
        RunnableWithFallbacks:
            Modelo principal configurado con respaldo.

    La función utiliza with_fallbacks() para definir
    la alternativa de ejecución.

    La disponibilidad efectiva de cada modelo depende
    de la configuración y del proveedor correspondiente.
    """

    # Configura el modelo principal.
    principal = ChatGoogleGenerativeAI(
        model=modelo_principal,
    )

    # Configura el modelo de respaldo.
    respaldo = ChatGoogleGenerativeAI(
        model=modelo_respaldo,
    )

    # Devuelve el modelo principal con una alternativa.
    return principal.with_fallbacks([respaldo])


# ============================================================
# 7. CONSTRUCCIÓN DEL AGENTE MUNICIPAL
# ============================================================

def construir_agente_municipal(
    modelo: BaseChatModel | None = None,
    solicitar_aprobacion_cancelacion: Callable[[], bool] | None = None,
) -> AgentExecutor:
    """Construye el agente municipal con herramientas y trazabilidad.

    Registra las herramientas de consulta y análisis
    disponibles para el agente.

    La herramienta de cancelación simulada se incorpora
    exclusivamente cuando se proporciona una función
    de aprobación humana.

    Args:
        modelo:
            Modelo de chat utilizado por el agente.

            Si no se proporciona, se construye uno
            mediante construir_modelo_agente().

        solicitar_aprobacion_cancelacion:
            Función externa que devuelve una decisión
            booleana de aprobación.

            Si es None, no se registra la herramienta
            de cancelación simulada.

    Returns:
        AgentExecutor:
            Ejecutor del agente con herramientas,
            trazabilidad y límites de ejecución.

    Configuración del ejecutor:
        - verbose=True: habilita mensajes de ejecución.
        - return_intermediate_steps=True: conserva las acciones.
        - max_iterations=5: limita las iteraciones.
        - max_execution_time=60: establece un límite temporal.
        - handle_parsing_errors=True: gestiona errores de análisis.

    La aprobación humana se configura fuera del modelo,
    evitando que una decisión generada por el agente
    sustituya directamente la autorización externa.
    """

    # Herramientas disponibles sin supervisión de cancelaciones.
    herramientas = [
        calcular_metricas,
        consultar_documentacion,
        analizar_datos,
        consultar_estado_solicitud,
    ]

    # La cancelación simulada solo se expone
    # cuando existe una función externa de aprobación.
    if solicitar_aprobacion_cancelacion is not None:
        herramientas.append(
            construir_herramienta_cancelacion(
                solicitar_decision=solicitar_aprobacion_cancelacion,
            )
        )

    # Construye el modelo predeterminado cuando
    # no se proporciona una instancia externa.
    if modelo is None:
        modelo = construir_modelo_agente()

    # Crea el agente capaz de seleccionar herramientas.
    agente = create_tool_calling_agent(
        llm=modelo,
        tools=herramientas,
        prompt=prompt_agente,
    )

    # Configura el ejecutor con trazabilidad
    # y límites de ejecución.
    return AgentExecutor(
        agent=agente,
        tools=herramientas,
        verbose=True,
        return_intermediate_steps=True,
        max_iterations=5,
        max_execution_time=60,
        handle_parsing_errors=True,
    )


# ============================================================
# 8. REGISTRO DE EVENTOS DEL AGENTE
# ============================================================

# Utiliza el nombre del módulo como identificador del logger.
# Permite registrar advertencias y errores para diagnóstico
# sin incorporarlos necesariamente a las respuestas públicas.
logger = logging.getLogger(__name__)


# ============================================================
# 9. EJECUCIÓN SEGURA DEL AGENTE
# ============================================================

def ejecutar_agente_seguro(
    agente: AgentExecutor,
    entrada: str,
) -> dict:
    """Ejecuta el agente y registra los errores de forma segura.

    Centraliza la ejecución del agente y transforma
    determinados errores en respuestas controladas.

    Args:
        agente:
            Ejecutor del agente que procesará la consulta.
        entrada:
            Consulta textual proporcionada al agente.

    Returns:
        dict:
            Resultado de la ejecución.

            En caso de éxito, conserva el resultado
            del agente y normaliza el campo output.

            Ante errores controlados, devuelve:
                - output: mensaje público.
                - intermediate_steps: lista vacía.
                - error: clasificación del problema.

    Clasificaciones utilizadas:
        - limite_iteraciones.
        - timeout.
        - conexion.
        - inesperado.

    Los detalles técnicos de las excepciones
    no se incorporan directamente a los mensajes
    públicos de error.

    Los eventos se registran mediante logging
    para facilitar su diagnóstico.
    """

    try:
        # Ejecuta el agente con la consulta recibida.
        resultado = agente.invoke({"entrada": entrada})

        # Convierte el contenido de salida en texto visible.
        resultado["output"] = normalizar_respuesta_agente(
            resultado["output"]
        )

        # Detecta la detención por máximo de iteraciones.
        if resultado["output"] == "Agent stopped due to max iterations.":
            logger.warning(
                "El agente alcanzó el límite de iteraciones."
            )

            # Sustituye el mensaje interno por uno público.
            return {
                **resultado,
                "output": (
                    "No fue posible completar la consulta "
                    "dentro del límite de ejecución."
                ),
                "error": "limite_iteraciones",
            }

        # Devuelve el resultado normalizado cuando no hay errores.
        return resultado

    # Gestiona los tiempos de espera agotados.
    except TimeoutError:
        logger.error("La ejecución del agente excedió el tiempo permitido.")
        return {
            "output": "La consulta excedió el tiempo de espera.",
            "intermediate_steps": [],
            "error": "timeout",
        }

    # Gestiona los errores de conexión.
    except ConnectionError:
        logger.error("Error de conexión durante la ejecución del agente.")
        return {
            "output": "No fue posible conectar con el servicio de IA.",
            "intermediate_steps": [],
            "error": "conexion",
        }

    # Captura errores no contemplados en las categorías anteriores.
    except Exception:
        logger.exception("Error inesperado durante la ejecución del agente.")
        return {
            "output": "No fue posible procesar la solicitud.",
            "intermediate_steps": [],
            "error": "inesperado",
        }


# ============================================================
# 10. NORMALIZACIÓN DE RESPUESTAS DEL AGENTE
# ============================================================

def normalizar_respuesta_agente(contenido: str | list) -> str:
    """Extrae el texto visible de una respuesta del agente.

    Acepta respuestas que contienen una cadena de texto
    o una lista de bloques estructurados.

    Args:
        contenido:
            Texto o lista de bloques devueltos por el agente.

    Returns:
        str:
            Si el contenido ya es una cadena,
            devuelve esa misma cadena.

            Si contiene una lista, concatena los valores
            textuales de los bloques cuyo tipo sea "text".

            Si no existen bloques textuales válidos,
            devuelve una cadena vacía.

    Los campos adicionales de los bloques, como
    metadatos o firmas, no se incluyen en la salida.

    Los textos recuperados se separan mediante
    saltos de línea.
    """

    # Conserva las respuestas que ya son texto.
    if isinstance(contenido, str):
        return contenido

    # Almacena únicamente los textos visibles.
    textos = []

    # Recorre los bloques estructurados de la respuesta.
    for bloque in contenido:
        if isinstance(bloque, dict):

            # Solo procesa bloques identificados como texto.
            if bloque.get("type") == "text":
                texto = bloque.get("text")

                # Descarta valores que no sean cadenas.
                if isinstance(texto, str):
                    textos.append(texto)

    # Une los fragmentos textuales mediante saltos de línea.
    return "\n".join(textos)
