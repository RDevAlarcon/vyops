"""Bloqueo cooperativo para la indexación de VyOps en Windows."""

from contextlib import contextmanager
from pathlib import Path
import msvcrt

from recuperacion import obtener_directorio_vectorial


class IndexacionEnCursoError(RuntimeError):
    """Indica que otro proceso mantiene el bloqueo de indexación."""


@contextmanager
def bloqueo_indexacion(directorio: Path | None = None):
    """Protege operaciones de indexación mediante un bloqueo exclusivo.

    Crea el directorio de almacenamiento si todavía no existe.
    El bloqueo solo coordina procesos que utilizan este mecanismo.
    """
    ruta_vectorial = (
        Path(directorio).expanduser().resolve()
        if directorio is not None
        else obtener_directorio_vectorial()
    )

    ruta_vectorial.mkdir(parents=True, exist_ok=True)
    ruta_bloqueo = ruta_vectorial / ".vyops_indexacion.lock"

    with ruta_bloqueo.open("a+b") as archivo:
        archivo.seek(0)
        archivo.write(b"0")
        archivo.flush()
        archivo.seek(0)

        try:
            msvcrt.locking(
                archivo.fileno(),
                msvcrt.LK_NBLCK,
                1,
            )
        except OSError as exc:
            raise IndexacionEnCursoError(
                "Otra indexación de VyOps mantiene el bloqueo."
            ) from exc

        try:
            yield
        finally:
            archivo.seek(0)
            msvcrt.locking(
                archivo.fileno(),
                msvcrt.LK_UNLCK,
                1,
            )