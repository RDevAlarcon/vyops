
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

        for inicio in range(0, len(nuevos), tamano_lote):
            lote = nuevos[inicio:inicio + tamano_lote]

            db.add_documents(
                documents=[documento for documento, _ in lote],
                ids=[identificador for _, identificador in lote],
            )

            if inicio + tamano_lote < len(nuevos):
                time.sleep(pausa_segundos)

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
