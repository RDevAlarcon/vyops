
"""Gestiona la indexación inicial e incremental del corpus en ChromaDB.

El módulo compara los fragmentos preparados con los registros existentes
y genera embeddings únicamente para los fragmentos pendientes.

Incluye controles para:
- Proteger el índice original del entorno de desarrollo.
- Evitar indexaciones concurrentes sobre el mismo directorio.
- Validar la integridad mínima del corpus.
- Insertar fragmentos en lotes con pausas configurables.
- Informar el progreso después de cada inserción completada.
- Autorizar explícitamente la eliminación de registros obsoletos.

La función sincronizar() admite embeddings inyectados para facilitar
las pruebas aisladas. La función main() configura Gemini para la
ejecución real desde la línea de comandos.
"""

import argparse
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from src.embeddings_con_reintentos import EmbeddingsConReintentos
from indexar_corpus import preparar_documentos
from recuperacion import (
    BASE_DIR,
    NOMBRE_COLECCION,
    obtener_directorio_vectorial,
)
from src.bloqueo_indexacion import bloqueo_indexacion
from src.sincronizacion_vectorial import (
    calcular_plan,
    autorizar_limpieza,
)


def sincronizar(
    directorio: Path,
    embeddings,
    aplicar_eliminaciones: bool = False,
) -> dict:
    """Sincroniza el corpus con una colección persistente de ChromaDB.

    Compara los identificadores existentes con los identificadores
    deseados y conserva los registros que no necesitan cambios.

    Los nuevos fragmentos se insertan en lotes de hasta diez unidades.
    Las eliminaciones solo se ejecutan cuando se solicitan
    explícitamente y superan los controles de autorización.

    Args:
        directorio: Ruta donde se almacena el índice vectorial.
        embeddings: Implementación de embeddings utilizada por ChromaDB.
            Puede ser Gemini o una implementación simulada para pruebas.
        aplicar_eliminaciones: Permite solicitar la eliminación
            controlada de registros que ya no pertenecen al corpus.

    Returns:
        dict: Resumen con fragmentos preparados, registros insertados,
        conservados, obsoletos, eliminados y registros finales.

    Raises:
        RuntimeError: Si se intenta modificar el índice original,
            el corpus es inválido o una limpieza no está autorizada.
        ValueError: Si la pausa configurada está fuera del rango válido.
    """
    # Normaliza la ruta para comparar directorios de forma consistente.
    directorio = Path(directorio).expanduser().resolve()

    # El índice original se considera protegido: las operaciones
    # de sincronización deben utilizar un directorio alternativo.
    directorio_original = (BASE_DIR / "vectorstore").resolve()

    if directorio == directorio_original:
        raise RuntimeError(
            "Protección activa: no se permite modificar el índice original."
        )

    # Mantiene un bloqueo durante toda la sincronización para evitar
    # operaciones concurrentes sobre el mismo índice.
    with bloqueo_indexacion(directorio):
        fragmentos, identificadores = preparar_documentos()

        # Rechaza corpus vacíos o con identificadores repetidos.
        if not fragmentos or len(identificadores) != len(set(identificadores)):
            raise RuntimeError("Corpus vacío o IDs duplicados.")

        # Comprueba que el corpus preparado contenga el mínimo
        # de documentos exigido para el caso demostrativo.
        documentos_cargados = len({
            fragmento.metadata["id"]
            for fragmento in fragmentos
        })

        if documentos_cargados < 30:
            raise RuntimeError("Corpus incompleto: menos de 30 documentos.")

        # Abre o crea la colección persistente en el directorio elegido.
        # La implementación de embeddings se recibe como dependencia.
        db = Chroma(
            collection_name=NOMBRE_COLECCION,
            persist_directory=str(directorio),
            embedding_function=embeddings,
        )

        # Obtiene únicamente los IDs para calcular las diferencias
        # sin recuperar el contenido completo de los documentos.
        existentes = set(db.get(include=[])["ids"])
        deseados = set(identificadores)

        # El plan clasifica los registros en insertar, conservar
        # y eliminar, sin modificar todavía la colección.
        plan = calcular_plan(existentes, deseados)

        # Respeta el orden de los fragmentos preparados y selecciona
        # exclusivamente los que necesitan incorporarse al índice.
        nuevos = [
            (fragmento, identificador)
            for fragmento, identificador in zip(
                fragmentos, identificadores
            )
            if identificador in plan.insertar
        ]

        # Permite configurar la pausa entre lotes mediante .env
        # o variables de entorno. El valor predeterminado es 10 s.
        pausa_segundos = float(
            os.environ.get("VYOPS_EMBEDDING_PAUSA_SEGUNDOS", "10")
        )

        if not 0 <= pausa_segundos <= 300:
            raise ValueError(
                "VYOPS_EMBEDDING_PAUSA_SEGUNDOS debe estar entre 0 y 300."
            )

        # Limita cada operación de inserción a diez fragmentos.
        tamano_lote = 10
        total_pendientes = len(nuevos)

        # Calcula cuántos lotes se necesitan, incluido el último
        # lote parcial cuando la cantidad no es múltiplo de diez.
        total_lotes = (
            (total_pendientes + tamano_lote - 1) // tamano_lote
        )

        procesados = 0

        # monotonic() permite medir duración sin depender
        # de cambios en la hora del sistema operativo.
        inicio_proceso = time.monotonic()

        print(
            f"[INICIO] Fragmentos del corpus: {len(fragmentos)}",
            flush=True,
        )
        print(
            f"[ESTADO] Conservados: {len(plan.conservar)} | "
            f"Pendientes: {total_pendientes}",
            flush=True,
        )

        # Una sincronización sin cambios termina sin generar
        # nuevos embeddings ni introducir pausas innecesarias.
        if total_pendientes == 0:
            print(
                "[PASS] No hay fragmentos nuevos para indexar.",
                flush=True,
            )

        for numero_lote, inicio in enumerate(
            range(0, total_pendientes, tamano_lote),
            start=1,
        ):
            lote = nuevos[inicio:inicio + tamano_lote]

            print(
                f"[INDEXACION] Lote {numero_lote}/{total_lotes} "
                f"| Fragmentos: {len(lote)}",
                flush=True,
            )

            # ChromaDB utiliza el proveedor de embeddings configurado.
            # El contador de progreso solo avanza si esta llamada
            # termina correctamente.
            db.add_documents(
                documents=[documento for documento, _ in lote],
                ids=[identificador for _, identificador in lote],
            )

            procesados += len(lote)

            # El porcentaje corresponde a los fragmentos nuevos,
            # no al tamaño total de la colección.
            porcentaje = procesados / total_pendientes * 100
            transcurrido = time.monotonic() - inicio_proceso

            print(
                f"[PROGRESO] {procesados}/{total_pendientes} "
                f"nuevos fragmentos persistidos "
                f"| {porcentaje:.1f}% "
                f"| Tiempo: {transcurrido:.1f}s",
                flush=True,
            )

            # Aplica una pausa preventiva únicamente entre lotes.
            # No espera después del último lote.
            if numero_lote < total_lotes and pausa_segundos > 0:
                print(
                    f"[ESPERA] Pausa preventiva: "
                    f"{pausa_segundos:g} segundos",
                    flush=True,
                )
                time.sleep(pausa_segundos)

        print(
            f"[FINALIZADO] Nuevos fragmentos: {procesados} "
            f"| Conservados: {len(plan.conservar)}",
            flush=True,
        )

        eliminados = 0

        # Los registros obsoletos no se eliminan automáticamente.
        # Incluso con autorización solicitada, deben superar
        # las comprobaciones de seguridad de autorizar_limpieza().
        if aplicar_eliminaciones and plan.eliminar:
            ids_actuales = set(db.get(include=[])["ids"])

            autorizado, motivo = autorizar_limpieza(
                ids_almacenados=ids_actuales,
                ids_deseados=deseados,
                documentos_cargados=documentos_cargados,
            )

            if not autorizado:
                raise RuntimeError(
                    f"Limpieza bloqueada: {motivo}"
                )

            db.delete(ids=list(plan.eliminar))
            eliminados = len(plan.eliminar)

        # Devuelve métricas de sincronización para auditoría
        # y para su comprobación mediante pruebas automatizadas.
        return {
            "fragmentos": len(fragmentos),
            "insertados": len(plan.insertar),
            "conservados": len(plan.conservar),
            "obsoletos": len(plan.eliminar),
            "eliminados": eliminados,
            "registros_finales": db._collection.count(),
        }


def main() -> None:
    """Configura Gemini y ejecuta la sincronización desde la consola.

    Permite seleccionar el directorio vectorial y solicitar
    explícitamente la eliminación controlada de registros obsoletos.

    Raises:
        RuntimeError: Si falta la clave API o falla una validación
            de seguridad durante la sincronización.
    """
    # Define los argumentos disponibles para la ejecución manual.
    parser = argparse.ArgumentParser()
    parser.add_argument("--directorio", type=Path)
    parser.add_argument(
        "--aplicar-eliminaciones",
        action="store_true",
    )
    args = parser.parse_args()

    # Prioriza la ruta indicada por el usuario. Si no existe
    # ese argumento, utiliza la configuración centralizada.
    directorio = (
        args.directorio
        if args.directorio is not None
        else obtener_directorio_vectorial()
    )

    # Carga la configuración local sin incluir credenciales
    # directamente en el código fuente.
    load_dotenv(BASE_DIR / ".env")

    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("Falta GEMINI_API_KEY.")

    # Configura el modelo de embeddings utilizado en el Gate 2.
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=api_key,
    )

    # Incorpora el mecanismo de reintentos ante errores recuperables
    # del proveedor, como límites temporales de cuota.
    embeddings_controlados = EmbeddingsConReintentos(embeddings)

    resultado = sincronizar(
        directorio=directorio,
        embeddings=embeddings_controlados,
        aplicar_eliminaciones=args.aplicar_eliminaciones,
    )

    # Presenta el resultado de la sincronización en la consola.
    for clave, valor in resultado.items():
        print(f"{clave}: {valor}")

    print("PASS: sincronización completada.")


if __name__ == "__main__":
    # Evita iniciar la indexación real al importar este módulo
    # desde otras partes del proyecto o desde las pruebas.
    main()
