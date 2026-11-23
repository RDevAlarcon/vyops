
"""Plantillas de prompts para el Bloque 18 de SkillNest.

Este módulo centraliza la construcción de prompts
utilizados en ejercicios de generación y transformación
de texto dentro del proyecto VyOps.

Utiliza PromptTemplate de LangChain para separar
las instrucciones del modelo de los valores dinámicos
que se incorporan durante la ejecución.

Responsabilidades principales:

    1. Generar prompts educativos personalizados.
    2. Construir plantillas para extraer hallazgos.
    3. Preparar instrucciones de simplificación textual.
    4. Definir un formato estructurado de salida en Markdown.

Funciones disponibles:

    crear_prompt_explicativo():
        Genera un prompt completo a partir de
        un tema y un área de conocimiento.

    crear_plantilla_extraccion():
        Construye una plantilla para identificar
        exactamente tres hallazgos de un informe.

    crear_plantilla_simplificacion():
        Construye una plantilla para expresar
        hallazgos técnicos en lenguaje sencillo.

    crear_plantilla_formato():
        Construye una plantilla para organizar
        tres hallazgos mediante viñetas Markdown.

Flujo conceptual de procesamiento de informes:

    Informe original
        |
        v
    Extracción de hallazgos
        |
        v
    Simplificación del lenguaje
        |
        v
    Presentación en Markdown

Las tres últimas funciones devuelven plantillas
que pueden integrarse posteriormente en cadenas
de procesamiento de LangChain.

IMPORTANTE:
    Este módulo no ejecuta consultas a Gemini
    ni a otros modelos de inteligencia artificial.

    Su responsabilidad se limita a construir
    o completar plantillas de prompts.

    Las instrucciones de no inventar información
    forman parte del contenido de los prompts,
    pero no constituyen una validación automática
    de las respuestas generadas por un modelo.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# PromptTemplate permite definir instrucciones
# con variables que se completan dinámicamente.
#
# Las plantillas pueden utilizarse individualmente
# o integrarse en cadenas de LangChain.
from langchain_core.prompts import PromptTemplate


# ============================================================
# 2. GENERACIÓN DE PROMPTS EDUCATIVOS
# ============================================================

def crear_prompt_explicativo(tema: str, area: str) -> str:
    """Genera un prompt educativo utilizando una plantilla.

    Construye una instrucción para explicar un concepto
    a una persona que está comenzando a estudiar
    un área de conocimiento.

    Args:
        tema:
            Concepto que se desea explicar.

        area:
            Área de conocimiento que proporciona
            el contexto educativo de la explicación.

    Returns:
        str:
            Prompt completo con las variables
            tema y area sustituidas por sus valores.

    Flujo:
        1. Construir la plantilla educativa.
        2. Incorporar el tema y el área recibidos.
        3. Recuperar el texto del prompt generado.
        4. Devolver el prompt como cadena.

    La función no genera la explicación directamente.

    Devuelve una instrucción que puede enviarse
    posteriormente a un modelo de lenguaje.
    """

    # --------------------------------------------------------
    # 2.1. DEFINICIÓN DE LA PLANTILLA
    # --------------------------------------------------------

    # Construye una plantilla con dos variables:
    #
    # {tema}: concepto que se desea explicar.
    # {area}: contexto educativo de la explicación.
    #
    # La instrucción solicita un único párrafo
    # adaptado a una persona principiante.
    plantilla = PromptTemplate.from_template(
        "Explica el concepto de {tema} en un párrafo, "
        "para alguien que recién comienza en {area}."
    )

    # --------------------------------------------------------
    # 2.2. INCORPORACIÓN DE VARIABLES
    # --------------------------------------------------------

    # Completa la plantilla utilizando los valores
    # recibidos como argumentos.
    #
    # invoke() genera el valor del prompt;
    # no realiza una consulta a un modelo.
    prompt = plantilla.invoke({
        "tema": tema,
        "area": area,
    })

    # --------------------------------------------------------
    # 2.3. DEVOLUCIÓN DEL PROMPT
    # --------------------------------------------------------

    # Devuelve únicamente el texto del prompt
    # para permitir su utilización posterior.
    return prompt.text


# ============================================================
# 3. PLANTILLA DE EXTRACCIÓN DE HALLAZGOS
# ============================================================

def crear_plantilla_extraccion() -> PromptTemplate:
    """Crea una plantilla para extraer tres hallazgos de un texto.

    Returns:
        PromptTemplate:
            Plantilla de LangChain que recibe
            el contenido de un informe.

    Variable requerida:
        texto:
            Informe que será analizado
            para identificar sus hallazgos.

    Instrucciones incluidas:
        - Analizar el informe proporcionado.
        - Extraer exactamente tres hallazgos principales.
        - No inventar información.
        - No agregar conclusiones sin respaldo textual.

    La función devuelve la plantilla sin completar.

    La extracción de hallazgos debe realizarse
    posteriormente mediante un modelo de lenguaje
    u otro componente de procesamiento.
    """

    # --------------------------------------------------------
    # 3.1. CONSTRUCCIÓN DE LA PLANTILLA
    # --------------------------------------------------------

    # Define el marcador {texto} para incorporar
    # posteriormente el contenido del informe.
    #
    # Las instrucciones delimitan la cantidad
    # de hallazgos y solicitan respaldo en el texto.
    return PromptTemplate.from_template(
        "Analiza el siguiente informe:\n\n"
        "{texto}\n\n"
        "Extrae exactamente tres hallazgos principales. "
        "No inventes información ni agregues conclusiones "
        "que no estén respaldadas por el texto."
    )


# ============================================================
# 4. PLANTILLA DE SIMPLIFICACIÓN DE HALLAZGOS
# ============================================================

def crear_plantilla_simplificacion() -> PromptTemplate:
    """Crea una plantilla para simplificar hallazgos técnicos.

    Returns:
        PromptTemplate:
            Plantilla que solicita transformar
            hallazgos técnicos en explicaciones sencillas.

    Variable requerida:
        puntos:
            Hallazgos extraídos previamente
            de un informe.

    Instrucciones incluidas:
        - Utilizar lenguaje claro y sencillo.
        - Adaptar el contenido a personas
          sin conocimientos técnicos.
        - Conservar datos, cantidades y hechos.
        - No incorporar información nueva.

    Esta plantilla corresponde a una etapa
    de transformación del lenguaje.

    No realiza extracción adicional
    ni comprueba automáticamente que los datos
    originales se hayan conservado.
    """

    # --------------------------------------------------------
    # 4.1. CONSTRUCCIÓN DE LA PLANTILLA
    # --------------------------------------------------------

    # Define el marcador {puntos} para recibir
    # los hallazgos que se desean simplificar.
    #
    # El prompt solicita preservar el contenido factual
    # mientras modifica su forma de expresión.
    return PromptTemplate.from_template(
        "Recibirás los siguientes hallazgos de un informe:\n\n"
        "{puntos}\n\n"
        "Reescribe cada hallazgo utilizando un lenguaje claro "
        "y sencillo para una persona sin conocimientos técnicos. "
        "Conserva los datos, cantidades y hechos originales. "
        "No agregues información nueva."
    )


# ============================================================
# 5. PLANTILLA DE PRESENTACIÓN EN MARKDOWN
# ============================================================

def crear_plantilla_formato() -> PromptTemplate:
    """Crea una plantilla para presentar tres hallazgos en Markdown.

    Returns:
        PromptTemplate:
            Plantilla que solicita organizar
            los hallazgos en exactamente tres viñetas.

    Variable requerida:
        texto_simple:
            Hallazgos previamente expresados
            mediante lenguaje sencillo.

    Instrucciones incluidas:
        - Generar exactamente tres viñetas Markdown.
        - Utilizar el símbolo '-' para cada viñeta.
        - Expresar un hallazgo por viñeta.
        - No agregar títulos.
        - No incorporar introducciones.
        - No añadir información nueva.

    Esta plantilla se orienta a la presentación
    estructurada de información.

    No verifica automáticamente que el resultado
    cumpla con la cantidad o el formato solicitado.

    La comprobación del resultado corresponde
    a una etapa posterior de evaluación.
    """

    # --------------------------------------------------------
    # 5.1. CONSTRUCCIÓN DE LA PLANTILLA
    # --------------------------------------------------------

    # Define el marcador {texto_simple} para recibir
    # los hallazgos después de su simplificación.
    #
    # La instrucción establece un formato Markdown
    # de tres viñetas, sin elementos adicionales.
    return PromptTemplate.from_template(
        "Recibirás los siguientes hallazgos explicados "
        "en lenguaje sencillo:\n\n"
        "{texto_simple}\n\n"
        "Organiza la información en exactamente tres viñetas "
        "Markdown, utilizando el símbolo '-'. "
        "Cada viñeta debe expresar un hallazgo. "
        "No agregues títulos, introducciones ni información nueva."
    )
