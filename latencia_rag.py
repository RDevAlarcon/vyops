
import time
from contextlib import contextmanager


@contextmanager
def medir(tiempos, etapa):
    """Registra la duración de una etapa en segundos."""
    inicio = time.perf_counter()

    try:
        yield
    finally:
        tiempos[etapa] = time.perf_counter() - inicio