
"""Calcula los costos estimados del pipeline RAG de VyOps.

Este módulo proporciona funciones para estimar el consumo económico
de las operaciones de generación de texto y embeddings.

Permite calcular:
    - Costos de tokens de entrada y salida.
    - Costos de tokens recuperados desde caché.
    - Costos de generación de embeddings.
    - Costo total estimado de una consulta RAG.

Las tarifas se expresan en dólares estadounidenses (USD)
por cada millón de tokens.

Las funciones no realizan llamadas a Gemini ni consultan
servicios externos. Los resultados son estimaciones basadas
en las tarifas configuradas y los tokens proporcionados.

Las tarifas declaradas como constantes se mantienen por
compatibilidad con los cálculos que utilizan valores
predeterminados.
"""

from configuracion_modelos import (
    obtener_tarifas_generacion,
    obtener_tarifa_embedding,
)


# Tarifas de referencia Gemini API, modalidad Standard de pago.
# Los valores se expresan en USD por un millón de tokens.
# La vigencia de estas tarifas debe verificarse por separado.

PRECIO_ENTRADA_FLASH_LITE = 0.30
PRECIO_SALIDA_FLASH_LITE = 2.50
PRECIO_EMBEDDING = 0.15


def calcular_costo(
    tokens_entrada,
    tokens_salida,
    precio_entrada_millon=PRECIO_ENTRADA_FLASH_LITE,
    precio_salida_millon=PRECIO_SALIDA_FLASH_LITE,
):
    """Calcula el costo estimado de generación sin caché diferenciada.

    Multiplica los tokens de entrada y salida por sus tarifas
    respectivas, expresadas en USD por millón de tokens.

    Args:
        tokens_entrada (int): Cantidad de tokens de entrada.
        tokens_salida (int): Cantidad de tokens de salida.
        precio_entrada_millon (float): Tarifa de entrada en USD
            por un millón de tokens.
        precio_salida_millon (float): Tarifa de salida en USD
            por un millón de tokens.

    Returns:
        dict: Desglose del costo estimado:
            - entrada_usd: Costo de los tokens de entrada.
            - salida_usd: Costo de los tokens de salida.
            - total_usd: Suma de ambos costos.

    Raises:
        ValueError: Si algún valor es None o negativo.

    Notes:
        No aplica tarifas diferenciadas de caché.

        El resultado es una estimación matemática y no
        representa necesariamente el importe facturado
        por el proveedor.
    """

    valores = (
        tokens_entrada,
        tokens_salida,
        precio_entrada_millon,
        precio_salida_millon,
    )

    # Evita calcular costos con información incompleta.
    if any(valor is None for valor in valores):
        raise ValueError("Faltan datos para calcular el costo.")

    # Los consumos y las tarifas deben ser no negativos.
    if any(valor < 0 for valor in valores):
        raise ValueError("Los valores no pueden ser negativos.")

    # Convierte las tarifas por millón a costos del consumo real.
    costo_entrada = tokens_entrada * precio_entrada_millon / 1_000_000
    costo_salida = tokens_salida * precio_salida_millon / 1_000_000

    return {
        "entrada_usd": costo_entrada,
        "salida_usd": costo_salida,
        "total_usd": costo_entrada + costo_salida,
    }


def calcular_costo_embedding(
    tokens_embedding,
    precio_millon=PRECIO_EMBEDDING,
):
    """Estima el costo de los tokens utilizados para embeddings.

    Args:
        tokens_embedding (int): Cantidad de tokens considerados
            para la generación de embeddings.
        precio_millon (float): Tarifa en USD por millón
            de tokens de embeddings.

    Returns:
        float: Costo estimado de embeddings en USD.

    Raises:
        ValueError: Si la cantidad de tokens es None
            o negativa.

    Notes:
        La función únicamente realiza el cálculo económico.
        No genera embeddings ni realiza solicitudes al proveedor.

        Se valida la cantidad de tokens, pero no se aplica
        una validación independiente a precio_millon.
    """

    if tokens_embedding is None or tokens_embedding < 0:
        raise ValueError("Cantidad de tokens inválida.")

    return tokens_embedding * precio_millon / 1_000_000


def calcular_costo_con_cache(
    tokens_entrada,
    tokens_salida,
    tokens_cache,
    precio_entrada_millon,
    precio_salida_millon,
    precio_cache_millon,
):
    """Calcula el costo de generación con tarifa de caché diferenciada.

    Se considera que los tokens recuperados desde caché
    forman parte de los tokens de entrada reportados.

    Para evitar contabilizarlos dos veces, se descuentan
    de la entrada normal antes de calcular los costos.

    Args:
        tokens_entrada (int): Total de tokens de entrada,
            incluidos los tokens recuperados desde caché.
        tokens_salida (int): Tokens de salida generados.
        tokens_cache (int): Tokens de entrada leídos desde caché.
        precio_entrada_millon (float): Tarifa de entrada normal
            en USD por millón de tokens.
        precio_salida_millon (float): Tarifa de salida
            en USD por millón de tokens.
        precio_cache_millon (float): Tarifa de lectura desde
            caché en USD por millón de tokens.

    Returns:
        dict: Desglose del costo estimado:
            - entrada_usd: Costo de entrada sin caché.
            - cache_usd: Costo de tokens leídos desde caché.
            - salida_usd: Costo de tokens de salida.
            - total_usd: Suma de los tres componentes.

    Raises:
        ValueError: Si algún valor es None o negativo,
            o si los tokens de caché superan los de entrada.

    Notes:
        El cálculo supone que tokens_cache está incluido
        en tokens_entrada.

        No contempla costos adicionales por almacenamiento
        o creación de caché.
    """

    valores = (
        tokens_entrada,
        tokens_salida,
        tokens_cache,
        precio_entrada_millon,
        precio_salida_millon,
        precio_cache_millon,
    )

    if any(valor is None for valor in valores):
        raise ValueError("Faltan datos para calcular el costo.")

    if any(valor < 0 for valor in valores):
        raise ValueError("Los valores no pueden ser negativos.")

    # La lectura desde caché es un subconjunto de la entrada.
    if tokens_cache > tokens_entrada:
        raise ValueError(
            "Los tokens en caché no pueden superar la entrada."
        )

    # Separa los tokens normales de los leídos desde caché
    # para aplicar a cada grupo su tarifa correspondiente.
    tokens_entrada_normal = tokens_entrada - tokens_cache

    costo_entrada = (
        tokens_entrada_normal * precio_entrada_millon
        / 1_000_000
    )

    costo_cache = (
        tokens_cache * precio_cache_millon
        / 1_000_000
    )

    costo_salida = (
        tokens_salida * precio_salida_millon
        / 1_000_000
    )

    return {
        "entrada_usd": costo_entrada,
        "cache_usd": costo_cache,
        "salida_usd": costo_salida,
        "total_usd": costo_entrada + costo_cache + costo_salida,
    }


def calcular_costo_rag(
    modelo_generacion,
    modelo_embedding,
    tokens_entrada,
    tokens_salida,
    tokens_embedding,
    tokens_cache=0,
):
    """Calcula el costo total estimado de una consulta RAG.

    Obtiene las tarifas correspondientes a los modelos
    configurados y calcula por separado los costos
    de generación de texto y embeddings.

    Selecciona el cálculo de generación con o sin
    caché diferenciada según el consumo informado.

    Args:
        modelo_generacion (str): Identificador del modelo
            utilizado para generar la respuesta.
        modelo_embedding (str): Identificador del modelo
            utilizado para embeddings.
        tokens_entrada (int): Tokens de entrada del modelo.
        tokens_salida (int): Tokens de salida del modelo.
        tokens_embedding (int): Tokens considerados
            para calcular el costo de embeddings.
        tokens_cache (int): Tokens recuperados desde caché.
            Su valor predeterminado es cero.

    Returns:
        dict: Desglose del costo estimado:
            - generacion_usd: Costo total de generación.
            - embedding_usd: Costo de embeddings.
            - total_usd: Suma de ambos componentes.

    Raises:
        ValueError: Si el consumo de caché es None,
            si existe consumo de caché sin una tarifa
            configurada o si los cálculos internos
            detectan valores inválidos.

    Notes:
        Las tarifas se obtienen desde configuracion_modelos.py.

        Si tokens_cache es mayor que cero, se utiliza
        calcular_costo_con_cache().

        En caso contrario, se utiliza calcular_costo().

        El cálculo no consulta directamente la API de Gemini.
        Su precisión depende de las tarifas configuradas
        y de los datos de consumo proporcionados.
    """

    # Obtiene las tarifas asociadas a los modelos declarados.
    tarifas = obtener_tarifas_generacion(modelo_generacion)
    tarifa_embedding = obtener_tarifa_embedding(modelo_embedding)

    # Se diferencia el consumo de caché desconocido (None)
    # de un consumo explícitamente informado como cero.
    if tokens_cache is None:
        raise ValueError(
            "El proveedor no informó el consumo de caché."
        )

    if tokens_cache > 0:
        # No se estima un costo de caché si el modelo
        # carece de una tarifa específica configurada.
        if tarifas["cache"] is None:
            raise ValueError(
                "No existe tarifa de caché configurada "
                f"para {modelo_generacion}."
            )

        generacion = calcular_costo_con_cache(
            tokens_entrada=tokens_entrada,
            tokens_salida=tokens_salida,
            tokens_cache=tokens_cache,
            precio_entrada_millon=tarifas["entrada"],
            precio_salida_millon=tarifas["salida"],
            precio_cache_millon=tarifas["cache"],
        )
    else:
        generacion = calcular_costo(
            tokens_entrada=tokens_entrada,
            tokens_salida=tokens_salida,
            precio_entrada_millon=tarifas["entrada"],
            precio_salida_millon=tarifas["salida"],
        )

    # El costo de embeddings se calcula por separado
    # y se incorpora al total de la consulta RAG.
    costo_embedding = calcular_costo_embedding(
        tokens_embedding=tokens_embedding,
        precio_millon=tarifa_embedding,
    )

    return {
        "generacion_usd": generacion["total_usd"],
        "embedding_usd": costo_embedding,
        "total_usd": generacion["total_usd"] + costo_embedding,
    }
