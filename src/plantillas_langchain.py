"""Plantillas de prompts para el Bloque 18 de SkillNest."""

from langchain_core.prompts import PromptTemplate


def crear_prompt_explicativo(tema: str, area: str) -> str:
    """Genera un prompt educativo utilizando una plantilla."""

    plantilla = PromptTemplate.from_template(
        "Explica el concepto de {tema} en un párrafo, "
        "para alguien que recién comienza en {area}."
    )

    prompt = plantilla.invoke({
        "tema": tema,
        "area": area,
    })

    return prompt.text

def crear_plantilla_extraccion() -> PromptTemplate:
    """Crea una plantilla para extraer tres hallazgos de un texto."""

    return PromptTemplate.from_template(
        "Analiza el siguiente informe:\n\n"
        "{texto}\n\n"
        "Extrae exactamente tres hallazgos principales. "
        "No inventes información ni agregues conclusiones "
        "que no estén respaldadas por el texto."
    )

def crear_plantilla_simplificacion() -> PromptTemplate:
    """Crea una plantilla para simplificar hallazgos técnicos."""

    return PromptTemplate.from_template(
        "Recibirás los siguientes hallazgos de un informe:\n\n"
        "{puntos}\n\n"
        "Reescribe cada hallazgo utilizando un lenguaje claro "
        "y sencillo para una persona sin conocimientos técnicos. "
        "Conserva los datos, cantidades y hechos originales. "
        "No agregues información nueva."
    )

def crear_plantilla_formato() -> PromptTemplate:
    """Crea una plantilla para presentar tres hallazgos en Markdown."""

    return PromptTemplate.from_template(
        "Recibirás los siguientes hallazgos explicados "
        "en lenguaje sencillo:\n\n"
        "{texto_simple}\n\n"
        "Organiza la información en exactamente tres viñetas "
        "Markdown, utilizando el símbolo '-'. "
        "Cada viñeta debe expresar un hallazgo. "
        "No agregues títulos, introducciones ni información nueva."
    )