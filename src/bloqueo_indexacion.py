
"""Coordina operaciones de indexación mediante un bloqueo en Windows.

Este módulo implementa un bloqueo exclusivo cooperativo utilizando
msvcrt.locking(), disponible en sistemas Windows.

Su objetivo es evitar que dos procesos de VyOps que respeten este
mecanismo ejecuten simultáneamente operaciones sobre el mismo
directorio de almacenamiento vectorial.

El bloqueo se mantiene durante la ejecución del bloque protegido
y se libera al finalizar, incluso cuando ocurre una excepción.

Limitaciones:
- El mecanismo depende de Windows.
- Solo coordina procesos que utilizan el mismo archivo de bloqueo.
- No impide que aplicaciones externas modifiquen ChromaDB.
"""

from contextlib import contextmanager
from pathlib import Path
import msvcrt

from recuperacion import obtener_directorio_vectorial


class IndexacionEnCursoError(RuntimeError):
    """Indica que no fue posible adquirir el bloqueo exclusivo.

    Se utiliza cuando otro proceso mantiene bloqueado el archivo
    de coordinación o Windows rechaza la adquisición del bloqueo.
    """


@contextmanager
def bloqueo_indexacion(directorio: Path | None = None):
    """Protege una operación mediante un bloqueo exclusivo de archivo.

    Determina el directorio vectorial, crea un archivo de coordinación
    y solicita a Windows un bloqueo exclusivo no bloqueante sobre
    su primer byte.

    El bloqueo permanece activo mientras se ejecuta el código
    incluido dentro de la instrucción ``with``.

    Args:
        directorio: Directorio vectorial que se desea proteger.
            Si es None, utiliza la ruta configurada en VyOps.

    Yields:
        None: Cede el control al bloque protegido una vez
        adquirido el bloqueo.

    Raises:
        IndexacionEnCursoError: Si no puede adquirirse el bloqueo
            exclusivo porque Windows rechaza la operación.

    Notes:
        El directorio y el archivo de bloqueo pueden crearse si
        todavía no existen. Por lo tanto, este mecanismo no es
        estrictamente de solo lectura.

        El bloqueo es cooperativo y está asociado al directorio
        seleccionado. Dos procesos que utilicen directorios
        diferentes no comparten el mismo bloqueo.
    """
    # Normaliza el directorio indicado o utiliza la configuración
    # centralizada cuando no se proporciona una ruta explícita.
    ruta_vectorial = (
        Path(directorio).expanduser().resolve()
        if directorio is not None
        else obtener_directorio_vectorial()
    )

    # Garantiza que exista el directorio donde se almacenará
    # el archivo utilizado para coordinar las ejecuciones.
    ruta_vectorial.mkdir(parents=True, exist_ok=True)

    ruta_bloqueo = ruta_vectorial / ".vyops_indexacion.lock"

    # Mantiene abierto el archivo durante toda la operación.
    # El modo a+b permite crearlo sin truncarlo.
    with ruta_bloqueo.open("a+b") as archivo:
        # Prepara el primer byte sobre el que Windows aplicará
        # el bloqueo exclusivo.
        archivo.seek(0)
        archivo.write(b"0")
        archivo.flush()
        archivo.seek(0)

        try:
            # LK_NBLCK solicita un bloqueo exclusivo sin esperar.
            # Si no puede adquirirse, Windows informa un error.
            msvcrt.locking(
                archivo.fileno(),
                msvcrt.LK_NBLCK,
                1,
            )
        except OSError as exc:
            # Convierte el error del sistema en una excepción
            # específica y comprensible para el proyecto.
            raise IndexacionEnCursoError(
                "Otra indexación de VyOps mantiene el bloqueo."
            ) from exc

        try:
            # Ejecuta la operación protegida mientras el proceso
            # conserva el bloqueo exclusivo.
            yield
        finally:
            # Libera el mismo byte bloqueado, incluso cuando
            # el código protegido termina mediante una excepción.
            archivo.seek(0)
            msvcrt.locking(
                archivo.fileno(),
                msvcrt.LK_UNLCK,
                1,
            )
