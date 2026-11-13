
"""Configuración de modelos y tarifas de VyOps."""

MODELO_GENERACION = "gemini-3.5-flash-lite"
MODELO_EMBEDDING = "gemini-embedding-001"

# USD por millón de tokens.
# Tarifas Standard de pago utilizadas en el Bloque 28.
TARIFAS_GENERACION = {
    "gemini-3.5-flash-lite": {
        "entrada": 0.30,
        "salida": 2.50,
        "cache": None,
    },
}

TARIFAS_EMBEDDING = {
    "gemini-embedding-001": 0.15,
}


def obtener_tarifas_generacion(modelo):
    """Devuelve las tarifas configuradas para un modelo."""

    if modelo not in TARIFAS_GENERACION:
        raise ValueError(
            f"No existen tarifas configuradas para: {modelo}"
        )

    return TARIFAS_GENERACION[modelo]


def obtener_tarifa_embedding(modelo):
    """Devuelve la tarifa del modelo de embeddings."""

    if modelo not in TARIFAS_EMBEDDING:
        raise ValueError(
            f"No existe tarifa configurada para: {modelo}"
        )

    return TARIFAS_EMBEDDING[modelo]
