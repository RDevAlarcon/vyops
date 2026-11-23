
"""Herramientas para medir la latencia de las etapas RAG de VyOps.

Este módulo proporciona un administrador de contexto que permite
registrar el tiempo de ejecución de diferentes operaciones.

Se utiliza para medir etapas como:
- Recuperación documental.
- Filtrado de seguridad.
- Construcción del prompt.
- Generación de respuestas.
- Conteo de tokens.
- Validación de citas.

Las duraciones se almacenan en segundos dentro de un diccionario,
utilizando el nombre de cada etapa como identificador.

El módulo funciona localmente y no requiere Gemini ni ChromaDB.
"""

import time
from contextlib import contextmanager


@contextmanager
def medir(tiempos, etapa):
    """Mide y registra la duración de una etapa de procesamiento.

    Utiliza time.perf_counter() para obtener una medición
    de tiempo adecuada para calcular intervalos de ejecución.

    El bloque protegido se ejecuta normalmente y, al finalizar,
    su duración se guarda en el diccionario proporcionado.

    Args:
        tiempos (dict): Diccionario donde se registran las
            duraciones de las distintas etapas del pipeline.
        etapa (str): Nombre de la etapa que se desea medir.

    Yields:
        None: Permite ejecutar el bloque de código cuya
        duración se quiere registrar.

    Notes:
        El bloque finally garantiza que la duración se registre
        incluso cuando ocurre una excepción durante la etapa.

        Si una etapa se mide varias veces utilizando el mismo
        nombre, su valor anterior se reemplaza.

        Esta función no captura ni suprime las excepciones
        producidas dentro del bloque.
    """
    # Captura el instante inicial mediante un reloj monotónico
    # de alta resolución, apropiado para medir duraciones.
    inicio = time.perf_counter()

    try:
        # Cede el control al bloque que se desea medir.
        yield
    finally:
        # Registra el tiempo transcurrido incluso si el bloque
        # termina mediante una excepción.
        tiempos[etapa] = time.perf_counter() - inicio
