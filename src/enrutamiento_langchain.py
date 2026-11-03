"""Enrutamiento condicional de mensajes con LangChain.

Bloque 19 de SkillNest.
"""

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable
from langchain_core.runnables import RunnableBranch
from langchain_core.runnables import RunnablePassthrough

def crear_plantilla_clasificacion() -> PromptTemplate:
    """Crea una plantilla para clasificar mensajes de soporte."""
    return PromptTemplate.from_template(
        "Clasifica el siguiente mensaje de soporte en una sola "
        "palabra: pregunta, queja o sugerencia. "
        "Responde únicamente con una de esas tres categorías.\n\n"
        "{mensaje}"
    )

def construir_paso_clasificacion(modelo: Runnable) -> Runnable:
    """Clasifica un mensaje y normaliza la categoría obtenida."""
    return (
        crear_plantilla_clasificacion()
        | modelo
        | StrOutputParser()
        | (lambda texto: texto.strip().lower())
    )

def crear_plantilla_pregunta() -> PromptTemplate:
    """Crea una plantilla para consultas técnicas y procedimientos."""
    return PromptTemplate.from_template(
        "Eres un asistente especializado en orientación técnica, "
        "procesos y procedimientos administrativos.\n\n"

        "Responde consultas relacionadas con:\n"
        "- Tecnología, software y funcionamiento de sistemas.\n"
        "- Funcionamiento de procesos técnicos y administrativos.\n"
        "- Trámites, permisos, autorizaciones y certificaciones.\n"
        "- Documentos y requisitos necesarios para realizar gestiones.\n"
        "- Etapas, responsables y organismos involucrados "
        "en distintos procedimientos.\n\n"

        "Instrucciones:\n"
        "1. Responde de forma clara, precisa y ordenada.\n"
        "2. Si la consulta trata sobre un procedimiento, "
        "explica sus etapas paso a paso.\n"
        "3. Identifica los documentos, requisitos y permisos "
        "necesarios cuando dispongas de información confiable.\n"
        "4. Indica qué organismo o institución interviene "
        "cuando corresponda.\n"
        "5. Considera el país o jurisdicción indicada "
        "por el usuario. Si falta y es importante, "
        "solicita esa información.\n"
        "6. No inventes requisitos, plazos, costos ni normativas.\n"
        "7. Si la información puede haber cambiado, "
        "advierte que debe verificarse en fuentes oficiales.\n"
        "8. No afirmes haber consultado fuentes oficiales "
        "si no se han proporcionado herramientas para hacerlo.\n\n"

        "Consulta del usuario:\n"
        "{mensaje}"
    )


def crear_plantilla_queja() -> PromptTemplate:
    """Crea una plantilla para gestionar quejas y problemas reportados."""
    return PromptTemplate.from_template(
        "Eres un asistente especializado en atención y "
        "orientación para la resolución de problemas.\n\n"

        "Puedes recibir quejas relacionadas con:\n"
        "- Fallas de software o servicios tecnológicos.\n"
        "- Problemas durante trámites o procedimientos.\n"
        "- Dificultades para obtener documentos o permisos.\n"
        "- Errores, demoras o inconvenientes administrativos.\n\n"

        "Instrucciones:\n"
        "1. Reconoce el problema con empatía y respeto.\n"
        "2. Identifica el inconveniente principal.\n"
        "3. Propón pasos concretos para investigar o resolver "
        "el problema cuando sea posible.\n"
        "4. Si corresponde a un trámite, identifica posibles "
        "canales de consulta o reclamación, sin inventarlos.\n"
        "5. No prometas resultados, plazos ni soluciones "
        "que no puedas garantizar.\n"
        "6. Si faltan antecedentes importantes, "
        "solicita la información necesaria.\n"
        "7. Distingue entre hechos confirmados "
        "y posibles explicaciones.\n\n"

        "Mensaje del usuario:\n"
        "{mensaje}"
    )


def crear_plantilla_sugerencia() -> PromptTemplate:
    """Crea una plantilla para analizar sugerencias y mejoras."""
    return PromptTemplate.from_template(
        "Eres un asistente especializado en analizar propuestas "
        "de mejora y recomendaciones.\n\n"

        "Puedes recibir sugerencias relacionadas con:\n"
        "- Aplicaciones, software y servicios tecnológicos.\n"
        "- Optimización y automatización de procesos.\n"
        "- Simplificación de trámites administrativos.\n"
        "- Mejoras en documentación, permisos y procedimientos.\n"
        "- Nuevas funcionalidades o servicios.\n\n"

        "Instrucciones:\n"
        "1. Agradece la sugerencia de manera profesional.\n"
        "2. Identifica claramente la mejora propuesta.\n"
        "3. Explica brevemente qué beneficio podría aportar.\n"
        "4. Si corresponde, menciona aspectos que deberían "
        "evaluarse antes de implementarla.\n"
        "5. No prometas que la propuesta será implementada.\n"
        "6. No inventes beneficios, resultados ni capacidades.\n"
        "7. Si la sugerencia no es suficientemente clara, "
        "solicita una aclaración.\n\n"

        "Sugerencia del usuario:\n"
        "{mensaje}"
    )

def crear_plantilla_defecto() -> PromptTemplate:
    """Crea una plantilla para mensajes sin categoría reconocida."""
    return PromptTemplate.from_template(
        "Eres un asistente de orientación general especializado "
        "en tecnología, procesos y procedimientos.\n\n"

        "El siguiente mensaje no pudo clasificarse claramente "
        "como pregunta, queja o sugerencia.\n\n"

        "Instrucciones:\n"
        "1. Responde de manera profesional, clara y neutral.\n"
        "2. Identifica qué información intenta comunicar el usuario.\n"
        "3. Si su intención no está clara, solicita una aclaración "
        "breve y específica.\n"
        "4. No asumas que el usuario está realizando una queja "
        "o solicitando un trámite.\n"
        "5. No inventes información, requisitos ni procedimientos.\n"
        "6. No afirmes haber realizado acciones o consultado "
        "fuentes externas.\n"
        "7. Evita solicitar datos personales innecesarios.\n\n"

        "Mensaje del usuario:\n"
        "{mensaje}"
    )

def construir_rutas_respuesta(modelo: Runnable) -> dict[str, Runnable]:
    """Construye las cuatro rutas de respuesta utilizando un modelo."""
    return {
        "pregunta": (
            crear_plantilla_pregunta()
            | modelo
            | StrOutputParser()
        ),
        "queja": (
            crear_plantilla_queja()
            | modelo
            | StrOutputParser()
        ),
        "sugerencia": (
            crear_plantilla_sugerencia()
            | modelo
            | StrOutputParser()
        ),
        "defecto": (
            crear_plantilla_defecto()
            | modelo
            | StrOutputParser()
        ),
    }

def construir_enrutador(modelo: Runnable) -> Runnable:
    """Selecciona una ruta de respuesta según la categoría."""
    rutas = construir_rutas_respuesta(modelo)

    return RunnableBranch(
        (
            lambda datos: datos["categoria"] == "pregunta",
            rutas["pregunta"],
        ),
        (
            lambda datos: datos["categoria"] == "queja",
            rutas["queja"],
        ),
        (
            lambda datos: datos["categoria"] == "sugerencia",
            rutas["sugerencia"],
        ),
        rutas["defecto"],
    )

def construir_cadena_enrutamiento(modelo: Runnable) -> Runnable:
    """Clasifica un mensaje y ejecuta la ruta correspondiente."""
    clasificador = construir_paso_clasificacion(modelo)
    enrutador = construir_enrutador(modelo)

    return (
        RunnablePassthrough.assign(categoria=clasificador)
        | RunnablePassthrough.assign(
            respuesta=enrutador
        )
    )