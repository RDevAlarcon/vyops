
"""Enrutamiento condicional de mensajes con LangChain.

Bloque 19 de SkillNest.

Este módulo implementa un flujo de clasificación y
enrutamiento de mensajes utilizando LangChain Expression
Language (LCEL).

El objetivo es seleccionar una estrategia de respuesta
según la intención identificada en el mensaje del usuario.

Categorías reconocidas:

    pregunta:
        Consultas técnicas, procedimientos y orientación
        sobre trámites o procesos administrativos.

    queja:
        Reportes de problemas, fallas, demoras
        o inconvenientes administrativos.

    sugerencia:
        Propuestas de mejora, nuevas funcionalidades
        u optimización de procesos.

    defecto:
        Ruta utilizada cuando la clasificación
        no coincide con las categorías anteriores.

Componentes principales:

    1. Plantilla de clasificación de mensajes.
    2. Cadena de clasificación y normalización.
    3. Plantillas especializadas de respuesta.
    4. Construcción de las cuatro rutas.
    5. Enrutador condicional mediante RunnableBranch.
    6. Cadena completa mediante RunnablePassthrough.

El módulo permite inyectar un modelo compatible
con Runnable para realizar la clasificación
y generar las respuestas.

La cadena conserva el mensaje original y agrega
los campos categoria y respuesta al resultado.

No realiza trámites ni consultas externas por sí mismo.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Permite construir prompts con variables de entrada.
from langchain_core.prompts import PromptTemplate

# Convierte las respuestas del modelo en texto.
from langchain_core.output_parsers import StrOutputParser

# Interfaz base de los componentes ejecutables de LangChain.
from langchain_core.runnables import Runnable

# Permite seleccionar una cadena según condiciones.
from langchain_core.runnables import RunnableBranch

# Conserva los datos de entrada y permite agregar campos.
from langchain_core.runnables import RunnablePassthrough


# ============================================================
# 2. PLANTILLA DE CLASIFICACIÓN
# ============================================================

def crear_plantilla_clasificacion() -> PromptTemplate:
    """Crea una plantilla para clasificar mensajes de soporte.

    Returns:
        PromptTemplate:
            Plantilla que solicita clasificar un mensaje
            en una de tres categorías:

            - pregunta.
            - queja.
            - sugerencia.

    La plantilla utiliza la variable mensaje
    para incorporar el texto proporcionado.

    Solicita al modelo devolver únicamente
    el nombre de la categoría seleccionada.
    """

    # Define las instrucciones de clasificación.
    # La respuesta esperada contiene una sola categoría.
    return PromptTemplate.from_template(
        "Clasifica el siguiente mensaje de soporte en una sola "
        "palabra: pregunta, queja o sugerencia. "
        "Responde únicamente con una de esas tres categorías.\n\n"
        "{mensaje}"
    )


# ============================================================
# 3. CADENA DE CLASIFICACIÓN Y NORMALIZACIÓN
# ============================================================

def construir_paso_clasificacion(modelo: Runnable) -> Runnable:
    """Clasifica un mensaje y normaliza la categoría obtenida.

    Args:
        modelo:
            Componente Runnable encargado de interpretar
            el mensaje y generar su clasificación.

    Returns:
        Runnable:
            Cadena que produce una categoría textual
            normalizada.

    Flujo:
        1. Construye el prompt de clasificación.
        2. Ejecuta el modelo.
        3. Convierte la respuesta en texto.
        4. Elimina espacios exteriores.
        5. Convierte el texto a minúsculas.

    La normalización facilita la comparación posterior
    con las condiciones del enrutador.
    """

    # Compone el prompt, el modelo y la normalización.
    return (
        crear_plantilla_clasificacion()
        | modelo
        | StrOutputParser()

        # Elimina espacios y normaliza mayúsculas.
        | (lambda texto: texto.strip().lower())
    )


# ============================================================
# 4. PLANTILLA PARA PREGUNTAS
# ============================================================

def crear_plantilla_pregunta() -> PromptTemplate:
    """Crea una plantilla para consultas técnicas y procedimientos.

    Returns:
        PromptTemplate:
            Plantilla especializada en responder preguntas
            sobre tecnología y procedimientos administrativos.

    La plantilla orienta al modelo a:

        - Explicar conceptos técnicos.
        - Describir procedimientos paso a paso.
        - Identificar requisitos cuando exista información.
        - Considerar la jurisdicción correspondiente.
        - Evitar inventar normas, costos o plazos.
        - Reconocer cuándo se requiere verificar
          información en fuentes oficiales.

    El mensaje original se incorpora mediante
    la variable mensaje.
    """

    # Define las instrucciones para consultas informativas.
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


# ============================================================
# 5. PLANTILLA PARA QUEJAS
# ============================================================

def crear_plantilla_queja() -> PromptTemplate:
    """Crea una plantilla para gestionar quejas y problemas reportados.

    Returns:
        PromptTemplate:
            Plantilla especializada en interpretar
            problemas y orientar posibles soluciones.

    La plantilla solicita al modelo:

        - Reconocer el inconveniente.
        - Identificar el problema principal.
        - Proponer pasos concretos cuando sea posible.
        - Considerar canales de consulta o reclamación.
        - Evitar prometer resultados no garantizados.
        - Solicitar antecedentes cuando sean necesarios.
        - Diferenciar hechos confirmados de hipótesis.

    No implica la apertura automática de reclamos
    ni la ejecución de acciones administrativas.
    """

    # Define el comportamiento de la ruta de quejas.
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


# ============================================================
# 6. PLANTILLA PARA SUGERENCIAS
# ============================================================

def crear_plantilla_sugerencia() -> PromptTemplate:
    """Crea una plantilla para analizar sugerencias y mejoras.

    Returns:
        PromptTemplate:
            Plantilla orientada a interpretar propuestas
            y describir sus posibles beneficios.

    La plantilla considera sugerencias relacionadas
    con tecnología, automatización, procedimientos
    y nuevas funcionalidades.

    Solicita al modelo identificar la propuesta,
    explicar su posible utilidad y mencionar aspectos
    que deberían evaluarse antes de implementarla.

    No autoriza ni ejecuta cambios sobre sistemas.
    """

    # Define las instrucciones de análisis de propuestas.
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


# ============================================================
# 7. PLANTILLA PARA MENSAJES NO CLASIFICADOS
# ============================================================

def crear_plantilla_defecto() -> PromptTemplate:
    """Crea una plantilla para mensajes sin categoría reconocida.

    Returns:
        PromptTemplate:
            Plantilla de orientación general utilizada
            cuando la categoría no coincide con ninguna
            de las tres rutas especializadas.

    Esta ruta permite responder de manera neutral
    y solicitar aclaraciones cuando la intención
    del usuario no está suficientemente definida.

    También establece restricciones para evitar
    afirmaciones sobre acciones o consultas externas
    que no hayan ocurrido.
    """

    # Define la respuesta para categorías no reconocidas.
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


# ============================================================
# 8. CONSTRUCCIÓN DE LAS RUTAS DE RESPUESTA
# ============================================================

def construir_rutas_respuesta(modelo: Runnable) -> dict[str, Runnable]:
    """Construye las cuatro rutas de respuesta utilizando un modelo.

    Args:
        modelo:
            Componente Runnable que genera las respuestas
            para cada plantilla especializada.

    Returns:
        dict[str, Runnable]:
            Diccionario que relaciona las categorías
            con sus cadenas de procesamiento:

            - pregunta.
            - queja.
            - sugerencia.
            - defecto.

    Cada ruta utiliza la misma estructura:

        Plantilla especializada
            |
            Modelo
            |
            StrOutputParser

    El modelo se reutiliza en las cuatro rutas,
    pero cada una proporciona instrucciones diferentes.

    Esta función construye las cadenas sin ejecutarlas.
    """

    # Registra una cadena especializada por categoría.
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


# ============================================================
# 9. CONSTRUCCIÓN DEL ENRUTADOR CONDICIONAL
# ============================================================

def construir_enrutador(modelo: Runnable) -> Runnable:
    """Selecciona una ruta de respuesta según la categoría.

    Args:
        modelo:
            Componente Runnable utilizado para generar
            las respuestas de las rutas especializadas.

    Returns:
        Runnable:
            Enrutador condicional que selecciona
            una cadena según el campo categoria.

    El enrutador evalúa las condiciones en orden:

        1. categoria == "pregunta".
        2. categoria == "queja".
        3. categoria == "sugerencia".
        4. Cualquier otro valor utiliza la ruta defecto.

    RunnableBranch ejecuta la primera ruta
    cuya condición se cumple.

    La ruta defecto actúa como alternativa
    cuando ninguna condición anterior coincide.
    """

    # Construye las cuatro cadenas de respuesta.
    rutas = construir_rutas_respuesta(modelo)

    # Define las condiciones de selección de rutas.
    return RunnableBranch(
        (
            # Selecciona la ruta de preguntas.
            lambda datos: datos["categoria"] == "pregunta",
            rutas["pregunta"],
        ),
        (
            # Selecciona la ruta de quejas.
            lambda datos: datos["categoria"] == "queja",
            rutas["queja"],
        ),
        (
            # Selecciona la ruta de sugerencias.
            lambda datos: datos["categoria"] == "sugerencia",
            rutas["sugerencia"],
        ),

        # Ruta utilizada cuando no existe coincidencia.
        rutas["defecto"],
    )


# ============================================================
# 10. CADENA COMPLETA DE ENRUTAMIENTO
# ============================================================

def construir_cadena_enrutamiento(modelo: Runnable) -> Runnable:
    """Clasifica un mensaje y ejecuta la ruta correspondiente.

    Args:
        modelo:
            Componente Runnable utilizado tanto para
            clasificar el mensaje como para generar
            la respuesta especializada.

    Returns:
        Runnable:
            Cadena compuesta que conserva los datos
            de entrada e incorpora dos campos:

            - categoria: clasificación normalizada.
            - respuesta: texto generado por la ruta.

    Flujo de ejecución:

        1. Recibir los datos originales.
        2. Clasificar el mensaje.
        3. Agregar el campo categoria.
        4. Evaluar las condiciones del enrutador.
        5. Ejecutar la ruta seleccionada.
        6. Agregar el campo respuesta.
        7. Devolver el resultado completo.

    RunnablePassthrough.assign() permite agregar
    información sin descartar los campos anteriores.

    El modelo se utiliza primero para clasificar
    y después para generar la respuesta.

    La cadena no realiza acciones administrativas
    ni modifica sistemas externos.
    """

    # Construye el clasificador de mensajes.
    clasificador = construir_paso_clasificacion(modelo)

    # Construye el enrutador de respuestas.
    enrutador = construir_enrutador(modelo)

    # Compone el flujo de clasificación y respuesta.
    return (

        # Conserva la entrada original y agrega
        # la categoría generada por el clasificador.
        RunnablePassthrough.assign(categoria=clasificador)

        # Utiliza la categoría para seleccionar una ruta
        # y agrega la respuesta al resultado.
        | RunnablePassthrough.assign(
            respuesta=enrutador
        )
    )
