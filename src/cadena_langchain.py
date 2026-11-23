
"""Orquestación de tres etapas con LangChain para VyOps.

Este módulo construye una cadena de procesamiento
secuencial utilizando LangChain Expression Language (LCEL).

La cadena transforma un texto mediante tres etapas:

    1. Extracción:
       Identifica los puntos relevantes del texto original.

    2. Simplificación:
       Transforma los puntos extraídos en un texto
       más sencillo de comprender.

    3. Formato:
       Organiza el texto simplificado en una
       respuesta final estructurada.

Cada etapa utiliza:

    - Una plantilla de prompt específica.
    - Un modelo compatible con Runnable.
    - StrOutputParser para obtener texto.

Los resultados intermedios se adaptan mediante
funciones lambda para proporcionar las variables
esperadas por la siguiente plantilla.

La función construir_cadena() únicamente construye
y devuelve la composición de componentes.

La ejecución efectiva ocurre cuando el consumidor
invoca la cadena mediante los métodos de Runnable.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Convierte las respuestas del modelo en cadenas de texto.
from langchain_core.output_parsers import StrOutputParser

# Interfaz utilizada para representar componentes ejecutables
# y cadenas compuestas de LangChain.
from langchain_core.runnables import Runnable

# Plantillas de prompt correspondientes a cada etapa
# del procesamiento de texto.
from src.plantillas_langchain import (
    crear_plantilla_extraccion,
    crear_plantilla_simplificacion,
    crear_plantilla_formato,
)


# ============================================================
# 2. CONSTRUCCIÓN DE LA CADENA DE TRES ETAPAS
# ============================================================

def construir_cadena(modelo: Runnable) -> Runnable:
    """Conecta extracción, simplificación y formato en una cadena.

    Construye un flujo secuencial de tres etapas
    utilizando el operador de composición | de LangChain.

    Cada etapa recibe información procesada por la anterior.

    Args:
        modelo:
            Componente Runnable que procesa los prompts.

            Se utiliza en las tres etapas de la cadena
            y puede corresponder a un modelo real
            o a un modelo simulado para pruebas.

    Returns:
        Runnable:
            Cadena compuesta que ejecuta las etapas
            de extracción, simplificación y formato.

            Su resultado final es una cadena de texto
            producida por StrOutputParser.

    Flujo de procesamiento:

        Entrada original
            |
            v
        Plantilla de extracción
            |
            v
        Modelo
            |
            v
        StrOutputParser
            |
            v
        {"puntos": puntos}
            |
            v
        Plantilla de simplificación
            |
            v
        Modelo
            |
            v
        StrOutputParser
            |
            v
        {"texto_simple": texto_simple}
            |
            v
        Plantilla de formato
            |
            v
        Modelo
            |
            v
        StrOutputParser
            |
            v
        Respuesta final

    Las funciones lambda adaptan el resultado textual
    de una etapa al diccionario requerido por la siguiente.

    El módulo no modifica las plantillas originales
    ni implementa lógica adicional de análisis textual.
    """

    # --------------------------------------------------------
    # 2.1. COMPOSICIÓN SECUENCIAL
    # --------------------------------------------------------

    # El operador | conecta los componentes Runnable.
    #
    # Cada componente procesa el resultado del anterior
    # y entrega su salida al siguiente componente.
    cadena = (

        # ----------------------------------------------------
        # ETAPA 1: EXTRACCIÓN
        # ----------------------------------------------------

        # Construye el prompt de extracción a partir
        # de la entrada recibida por la cadena.
        crear_plantilla_extraccion()

        # Ejecuta el modelo para identificar
        # los puntos relevantes del texto.
        | modelo

        # Convierte la respuesta del modelo en texto.
        | StrOutputParser()

        # Adapta los puntos extraídos a la variable
        # requerida por la plantilla de simplificación.
        | (lambda puntos: {"puntos": puntos})

        # ----------------------------------------------------
        # ETAPA 2: SIMPLIFICACIÓN
        # ----------------------------------------------------

        # Construye el prompt utilizando los puntos
        # identificados durante la primera etapa.
        | crear_plantilla_simplificacion()

        # Ejecuta el modelo para simplificar el contenido.
        | modelo

        # Obtiene el resultado como una cadena de texto.
        | StrOutputParser()

        # Adapta el texto simplificado a la variable
        # requerida por la plantilla de formato.
        | (lambda texto_simple: {"texto_simple": texto_simple})

        # ----------------------------------------------------
        # ETAPA 3: FORMATO FINAL
        # ----------------------------------------------------

        # Construye el prompt que organiza
        # el contenido simplificado.
        | crear_plantilla_formato()

        # Ejecuta el modelo para generar
        # la presentación final del contenido.
        | modelo

        # Convierte la última respuesta en texto.
        | StrOutputParser()
    )

    # --------------------------------------------------------
    # 2.2. DEVOLUCIÓN DE LA CADENA
    # --------------------------------------------------------

    # Devuelve la composición lista para ejecutarse.
    #
    # La construcción no invoca el modelo:
    # las llamadas ocurren al ejecutar la cadena.
    return cadena
