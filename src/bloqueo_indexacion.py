
"""Coordina operaciones de indexación mediante un bloqueo multiplataforma.

Implementa un bloqueo exclusivo cooperativo compatible con Windows
y sistemas POSIX, incluido Linux.

Su objetivo es evitar que dos procesos de VyOps ejecuten
simultáneamente operaciones sobre el mismo directorio vectorial.

El bloqueo se libera al finalizar la operación protegida,
incluso cuando ocurre una excepción.

Limitaciones:
- Solo coordina procesos que respetan el mecanismo de bloqueo.
- No impide modificaciones realizadas por aplicaciones externas.
- Requiere un sistema de archivos compatible con estos bloqueos.
"""

import errno
import os
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO, Iterator

from recuperacion import obtener_directorio_vectorial


# Selecciona el mecanismo nativo de bloqueo según la plataforma.
if os.name == "nt":
    import msvcrt
elif os.name == "posix":
    import fcntl
else:
    raise RuntimeError(
        "Sistema operativo no compatible con el bloqueo de VyOps."
    )


class IndexacionEnCursoError(RuntimeError):
    """Indica que otra operación mantiene el bloqueo exclusivo."""


def _adquirir_bloqueo(archivo: BinaryIO) -> None:
    """Solicita un bloqueo exclusivo sin esperar su disponibilidad."""

    try:
        if os.name == "nt":
            # Windows permite bloquear una región más allá
            # del final del archivo, incluso si está vacío.
            archivo.seek(0)

            msvcrt.locking(
                archivo.fileno(),
                msvcrt.LK_NBLCK,
                1,
            )
        else:
            # Linux utiliza un bloqueo exclusivo sobre el archivo.
            fcntl.flock(
                archivo.fileno(),
                fcntl.LOCK_EX | fcntl.LOCK_NB,
            )

    except OSError as exc:
        # Distingue la contención de otros errores del sistema,
        # evitando informar una indexación en curso incorrectamente.
        if exc.errno in {
            errno.EACCES,
            errno.EAGAIN,
            errno.EWOULDBLOCK,
        }:
            raise IndexacionEnCursoError(
                "Otra indexación de VyOps mantiene el bloqueo."
            ) from exc

        raise


def _liberar_bloqueo(archivo: BinaryIO) -> None:
    """Libera el bloqueo utilizando el mecanismo de la plataforma."""

    if os.name == "nt":
        archivo.seek(0)

        msvcrt.locking(
            archivo.fileno(),
            msvcrt.LK_UNLCK,
            1,
        )
    else:
        fcntl.flock(
            archivo.fileno(),
            fcntl.LOCK_UN,
        )


@contextmanager
def bloqueo_indexacion(
    directorio: Path | None = None,
) -> Iterator[None]:
    """Protege una operación mediante un bloqueo exclusivo de archivo.

    Args:
        directorio: Directorio vectorial que se desea proteger.
            Si es None, utiliza la ruta configurada en VyOps.

    Yields:
        None: Cede el control una vez adquirido el bloqueo.

    Raises:
        IndexacionEnCursoError: Si otra operación mantiene el bloqueo.
        OSError: Si ocurre otro error del sistema de archivos.

    Notes:
        El directorio y el archivo de coordinación pueden crearse
        si todavía no existen.

        El archivo de bloqueo permanece en el directorio después
        de liberar el bloqueo para conservar su identidad.
    """

    ruta_vectorial = (
        Path(directorio).expanduser().resolve()
        if directorio is not None
        else obtener_directorio_vectorial()
    )

    ruta_vectorial.mkdir(parents=True, exist_ok=True)

    ruta_bloqueo = ruta_vectorial / ".vyops_indexacion.lock"

    # Abre o crea el archivo sin truncarlo ni agregar contenido.
    with ruta_bloqueo.open("a+b") as archivo:
        _adquirir_bloqueo(archivo)

        try:
            yield
        finally:
            _liberar_bloqueo(archivo)
