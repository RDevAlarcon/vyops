
"""Centraliza la configuración de modelos y tarifas de VyOps.

Este módulo define los modelos utilizados por el pipeline RAG
municipal y las tarifas de referencia para estimar su consumo.

Contiene:
    - El identificador del modelo de generación.
    - El identificador del modelo de embeddings.
    - Las tarifas de generación por millón de tokens.
    - La tarifa de embeddings por millón de tokens.
    - Funciones para consultar las tarifas configuradas.

Las tarifas se expresan en dólares estadounidenses (USD)
por cada millón de tokens.

Esta configuración corresponde a los valores utilizados
durante el Bloque 28 del proyecto SkillNest. No implica
que las tarifas continúen vigentes en el proveedor.

El módulo no realiza llamadas a Gemini ni modifica
la configuración de los modelos durante su ejecución.
"""


# Modelo encargado de generar las respuestas del RAG.
MODELO_GENERACION = "gemini-3.5-flash-lite"

# Modelo utilizado para representar textos mediante embeddings.
MODELO_EMBEDDING = "gemini-embedding-001"


# Tarifas de referencia de Gemini API, modalidad Standard de pago.
# Valores expresados en USD por un millón de tokens.
#
# Cada modelo de generación define:
#   entrada: costo de los tokens de entrada.
#   salida: costo de los tokens de salida.
#   cache: costo de lectura desde caché, cuando está configurado.
#
# El valor None indica que no existe una tarifa de caché
# configurada para el modelo dentro de VyOps.

TARIFAS_GENERACION = {
    "gemini-3.5-flash-lite": {
        "entrada": 0.30,
        "salida": 2.50,
        "cache": None,
    },
}


# Tarifa de referencia para el cálculo de embeddings.
# Cada entrada relaciona un identificador de modelo
# con su costo en USD por millón de tokens.

TARIFAS_EMBEDDING = {
    "gemini-embedding-001": 0.15,
}


def obtener_tarifas_generacion(modelo):
    """Obtiene las tarifas configuradas de un modelo de generación.

    Consulta el catálogo local de tarifas y devuelve
    los precios asociados al identificador solicitado.

    Args:
        modelo (str): Identificador del modelo de generación
            cuya configuración de tarifas se desea consultar.

    Returns:
        dict: Diccionario con las tarifas configuradas:
            - entrada: Precio de tokens de entrada.
            - salida: Precio de tokens de salida.
            - cache: Precio de lectura desde caché o None.

        Todos los precios configurados se expresan en USD
        por un millón de tokens.

    Raises:
        ValueError: Si el modelo solicitado no existe
            en TARIFAS_GENERACION.

    Notes:
        La función devuelve directamente el diccionario
        almacenado en TARIFAS_GENERACION, no una copia.

        No consulta tarifas en tiempo real ni realiza
        solicitudes al proveedor.
    """

    # Se rechazan modelos sin tarifas conocidas para evitar
    # estimaciones económicas basadas en precios incorrectos.
    if modelo not in TARIFAS_GENERACION:
        raise ValueError(
            f"No existen tarifas configuradas para: {modelo}"
        )

    return TARIFAS_GENERACION[modelo]


def obtener_tarifa_embedding(modelo):
    """Obtiene la tarifa configurada de un modelo de embeddings.

    Consulta el catálogo local de tarifas correspondiente
    a los modelos de representación vectorial.

    Args:
        modelo (str): Identificador del modelo de embeddings
            cuya tarifa se desea consultar.

    Returns:
        float: Precio configurado en USD por un millón
            de tokens de embeddings.

    Raises:
        ValueError: Si el modelo solicitado no existe
            en TARIFAS_EMBEDDING.

    Notes:
        La tarifa se obtiene desde la configuración local.
        No se consulta la API del proveedor.

        Esta función no calcula costos ni genera embeddings.
    """

    # Evita utilizar una tarifa genérica para un modelo
    # que no haya sido incorporado explícitamente al catálogo.
    if modelo not in TARIFAS_EMBEDDING:
        raise ValueError(
            f"No existe tarifa configurada para: {modelo}"
        )

    return TARIFAS_EMBEDDING[modelo]
