from configuracion_modelos import (
    obtener_tarifas_generacion,
    obtener_tarifa_embedding,
)

# Tarifas oficiales Gemini API, modalidad Standard de pago.
# USD por 1 millón de tokens.

PRECIO_ENTRADA_FLASH_LITE = 0.30
PRECIO_SALIDA_FLASH_LITE = 2.50
PRECIO_EMBEDDING = 0.15


def calcular_costo(
    tokens_entrada,
    tokens_salida,
    precio_entrada_millon=PRECIO_ENTRADA_FLASH_LITE,
    precio_salida_millon=PRECIO_SALIDA_FLASH_LITE,
):
    """Calcula el costo estimado de generación en USD."""

    valores = (
        tokens_entrada,
        tokens_salida,
        precio_entrada_millon,
        precio_salida_millon,
    )

    if any(valor is None for valor in valores):
        raise ValueError("Faltan datos para calcular el costo.")

    if any(valor < 0 for valor in valores):
        raise ValueError("Los valores no pueden ser negativos.")

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
    """Calcula el costo estimado de embeddings en USD."""

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
    """Calcula costos con una tarifa específica de caché.

    Supone que tokens_cache está incluido en tokens_entrada.
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

    if tokens_cache > tokens_entrada:
        raise ValueError(
            "Los tokens en caché no pueden superar la entrada."
        )

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
    """Calcula el costo RAG según las tarifas del modelo."""

    tarifas = obtener_tarifas_generacion(modelo_generacion)
    tarifa_embedding = obtener_tarifa_embedding(modelo_embedding)

    if tokens_cache is None:
        raise ValueError(
            "El proveedor no informó el consumo de caché."
        )

    if tokens_cache > 0:
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

    costo_embedding = calcular_costo_embedding(
        tokens_embedding=tokens_embedding,
        precio_millon=tarifa_embedding,
    )

    return {
        "generacion_usd": generacion["total_usd"],
        "embedding_usd": costo_embedding,
        "total_usd": generacion["total_usd"] + costo_embedding,
    }
