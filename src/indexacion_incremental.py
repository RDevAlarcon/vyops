
"""Indexación inicial e incremental de documentos en ChromaDB."""

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
    """Sincroniza fragmentos manteniendo los registros sin cambios."""

    directorio = Path(directorio).expanduser().resolve()
    directorio_original = (BASE_DIR / "vectorstore").resolve()

    if directorio == directorio_original:
        raise RuntimeError(
            "Protección activa: no se permite modificar el índice original."
        )

    with bloqueo_indexacion(directorio):
        fragmentos, identificadores = preparar_documentos()

        if not fragmentos or len(identificadores) != len(set(identificadores)):
            raise RuntimeError("Corpus vacío o IDs duplicados.")

        documentos_cargados = len({
            fragmento.metadata["id"]
            for fragmento in fragmentos
        })

        if documentos_cargados < 30:
            raise RuntimeError("Corpus incompleto: menos de 30 documentos.")

        db = Chroma(
            collection_name=NOMBRE_COLECCION,
            persist_directory=str(directorio),
            embedding_function=embeddings,
        )

        existentes = set(db.get(include=[])["ids"])
        deseados = set(identificadores)

        plan = calcular_plan(existentes, deseados)

        nuevos = [
            (fragmento, identificador)
            for fragmento, identificador in zip(
                fragmentos, identificadores
            )
            if identificador in plan.insertar
        ]

        pausa_segundos = float(
            os.environ.get("VYOPS_EMBEDDING_PAUSA_SEGUNDOS", "10")
        )

        if not 0 <= pausa_segundos <= 300:
            raise ValueError(
                "VYOPS_EMBEDDING_PAUSA_SEGUNDOS debe estar entre 0 y 300."
            )

        tamano_lote = 10
        total_pendientes = len(nuevos)
        total_lotes = (
            (total_pendientes + tamano_lote - 1) // tamano_lote
        )

        procesados = 0
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

            db.add_documents(
                documents=[documento for documento, _ in lote],
                ids=[identificador for _, identificador in lote],
            )

            procesados += len(lote)
            porcentaje = procesados / total_pendientes * 100
            transcurrido = time.monotonic() - inicio_proceso

            print(
                f"[PROGRESO] {procesados}/{total_pendientes} "
                f"nuevos fragmentos persistidos "
                f"| {porcentaje:.1f}% "
                f"| Tiempo: {transcurrido:.1f}s",
                flush=True,
            )

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

        return {
            "fragmentos": len(fragmentos),
            "insertados": len(plan.insertar),
            "conservados": len(plan.conservar),
            "obsoletos": len(plan.eliminar),
            "eliminados": eliminados,
            "registros_finales": db._collection.count(),
        }


def main() -> None:
    """Ejecuta la indexación usando embeddings de Gemini."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--directorio", type=Path)
    parser.add_argument(
        "--aplicar-eliminaciones",
        action="store_true",
    )
    args = parser.parse_args()

    directorio = (
        args.directorio
        if args.directorio is not None
        else obtener_directorio_vectorial()
    )

    load_dotenv(BASE_DIR / ".env")

    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("Falta GEMINI_API_KEY.")

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=api_key,
    )

    embeddings_controlados = EmbeddingsConReintentos(embeddings)

    resultado = sincronizar(
        directorio=directorio,
        embeddings=embeddings_controlados,
        aplicar_eliminaciones=args.aplicar_eliminaciones,
    )

    for clave, valor in resultado.items():
        print(f"{clave}: {valor}")

    print("PASS: sincronización completada.")


if __name__ == "__main__":
    main()
