from statistics import mean
from typing import Literal

from langchain_core.tools import tool

from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnableWithFallbacks
from langchain_core.language_models import BaseChatModel
import logging
from src.herramienta_solicitudes import consultar_estado_solicitud

@tool
def calcular_metricas(
    valores: list[float],
    operacion: Literal["suma", "promedio", "maximo", "minimo"],
) -> str:
    """Calcula una métrica estadística sobre una lista de valores numéricos."""
    if not valores:
        return "Error: la lista de valores no puede estar vacía."

    operaciones = {
        "suma": sum,
        "promedio": mean,
        "maximo": max,
        "minimo": min,
    }

    try:
        resultado = operaciones[operacion](valores)
    except KeyError:
        return f"Error: operación no admitida: {operacion}."

    return f"El resultado de {operacion} es {resultado}."

@tool
def consultar_documentacion(tema: str) -> str:
    """Consulta información interna de VyOps sobre un tema específico."""
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

    tema_normalizado = tema.strip().lower()

    try:
        return documentacion[tema_normalizado]
    except KeyError:
        return f"No se encontró documentación para el tema: {tema}."

@tool
def analizar_datos(valor_inicial: float, valor_final: float) -> dict:
    """Analiza la variación absoluta y porcentual entre dos valores."""
    variacion_absoluta = valor_final - valor_inicial

    if valor_inicial == 0:
        variacion_porcentual = None
    else:
        variacion_porcentual = (
            variacion_absoluta / abs(valor_inicial)
        ) * 100

    if variacion_absoluta > 0:
        tendencia = "aumento"
    elif variacion_absoluta < 0:
        tendencia = "disminucion"
    else:
        tendencia = "sin cambios"

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

def construir_modelo_agente(
    modelo_principal: str = "gemini-3.5-flash-lite",
    modelo_respaldo: str = "gemini-2.5-flash",
) -> RunnableWithFallbacks:
    """Construye el modelo del agente municipal con respaldo automático."""
    principal = ChatGoogleGenerativeAI(
        model=modelo_principal,
    )

    respaldo = ChatGoogleGenerativeAI(
        model=modelo_respaldo,
    )

    return principal.with_fallbacks([respaldo])

def construir_agente_municipal(
    modelo: BaseChatModel | None = None,
) -> AgentExecutor:
    """Construye el agente municipal con herramientas y trazabilidad."""
    herramientas = [
        calcular_metricas,
        consultar_documentacion,
        analizar_datos,
        consultar_estado_solicitud,
    ]

    if modelo is None:
        modelo = construir_modelo_agente()

    agente = create_tool_calling_agent(
        llm=modelo,
        tools=herramientas,
        prompt=prompt_agente,
    )

    return AgentExecutor(
        agent=agente,
        tools=herramientas,
        verbose=True,
        return_intermediate_steps=True,
        max_iterations=5,
        max_execution_time=60,
        handle_parsing_errors=True,
    )

logger = logging.getLogger(__name__)

def ejecutar_agente_seguro(
    agente: AgentExecutor,
    entrada: str,
) -> dict:
    """Ejecuta el agente y registra los errores de forma segura."""
    try:
        resultado = agente.invoke({"entrada": entrada})

        resultado["output"] = normalizar_respuesta_agente(
            resultado["output"]
        )

        if resultado["output"] == "Agent stopped due to max iterations.":
            logger.warning(
                "El agente alcanzó el límite de iteraciones."
            )
            return {
                **resultado,
                "output": (
                    "No fue posible completar la consulta "
                    "dentro del límite de ejecución."
                ),
                "error": "limite_iteraciones",
            }

        return resultado

    except TimeoutError:
        logger.error("La ejecución del agente excedió el tiempo permitido.")
        return {
            "output": "La consulta excedió el tiempo de espera.",
            "intermediate_steps": [],
            "error": "timeout",
        }

    except ConnectionError:
        logger.error("Error de conexión durante la ejecución del agente.")
        return {
            "output": "No fue posible conectar con el servicio de IA.",
            "intermediate_steps": [],
            "error": "conexion",
        }

    except Exception:
        logger.exception("Error inesperado durante la ejecución del agente.")
        return {
            "output": "No fue posible procesar la solicitud.",
            "intermediate_steps": [],
            "error": "inesperado",
        }

def normalizar_respuesta_agente(contenido: str | list) -> str:
    """Extrae el texto visible de una respuesta del agente."""
    if isinstance(contenido, str):
        return contenido

    textos = []

    for bloque in contenido:
        if isinstance(bloque, dict):
            if bloque.get("type") == "text":
                texto = bloque.get("text")
                if isinstance(texto, str):
                    textos.append(texto)

    return "\n".join(textos)