
"""Demuestra el cálculo de huellas digitales de documentos con SHA-256.

Este módulo utiliza textos de ejemplo para mostrar cómo una función
hash permite comparar el contenido de distintos documentos.

La demostración comprueba que:
- Dos textos idénticos producen la misma huella.
- Textos diferentes pueden producir huellas diferentes.
- La huella depende del contenido y no del nombre del documento.

Se utiliza una representación abreviada de 12 caracteres
hexadecimales del hash SHA-256.

Este archivo es una práctica independiente: no genera embeddings,
no modifica ChromaDB ni realiza llamadas a Gemini.
"""

import hashlib


def huella(texto):
    """Calcula una huella SHA-256 abreviada de un texto.

    Convierte el texto a bytes UTF-8, calcula su hash SHA-256
    y devuelve los primeros 12 caracteres hexadecimales.

    Args:
        texto (str): Contenido textual que se desea identificar.

    Returns:
        str: Huella hexadecimal abreviada de 12 caracteres.

    Notes:
        La versión abreviada es útil para demostraciones y
        comparaciones sencillas, pero presenta mayor riesgo de
        colisiones que el hash SHA-256 completo.
    """
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:12]


# Documentos de ejemplo para comparar sus huellas.
# doc1 y doc2 tienen exactamente el mismo contenido.
doc1 = "Politica de devoluciones: 30 dias desde la compra."
doc2 = "Politica de devoluciones: 30 dias desde la compra."

# doc3 contiene una política diferente.
doc3 = "Politica de envios: 5 dias habiles a todo el pais."


# Muestra las huellas y longitudes de los textos.
print("doc1 huella:", huella(doc1), "longitud:", len(doc1))
print("doc2 huella:", huella(doc2), "longitud:", len(doc2))
print("doc3 huella:", huella(doc3), "longitud:", len(doc3))

# Comprueba que dos documentos idénticos generan la misma huella.
print("doc1 == doc2 (mismo contenido):", huella(doc1) == huella(doc2))
