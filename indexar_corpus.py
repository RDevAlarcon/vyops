
"""Prepara y valida el corpus documental municipal de VyOps.

Este módulo constituye la etapa de preparación del pipeline RAG:

1. Carga los documentos municipales y sus metadatos.
2. Divide el contenido en fragmentos de tamaño controlado.
3. Genera identificadores deterministas mediante SHA-256.
4. Comprueba que no existan identificadores duplicados.
5. Verifica que todos los documentos estén representados.

IMPORTANTE:
Esta operación es completamente local. No genera embeddings,
no realiza llamadas a Gemini y no modifica ChromaDB.
"""

from collections import Counter
from hashlib import sha256

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.corpus_municipal import obtener_corpus_municipal


# Tamaño máximo objetivo de cada fragmento, medido en caracteres.
# Permite recuperar partes específicas sin procesar documentos completos.
CHUNK_SIZE = 800

# Cantidad de caracteres compartidos entre fragmentos consecutivos.
# Ayuda a conservar contexto cuando el texto se divide.
CHUNK_OVERLAP = 120

# Prioridad de separación: párrafos, líneas, oraciones, palabras
# y, como último recurso, caracteres individuales.
SEPARADORES = ["\n\n", "\n", ". ", " ", ""]


def preparar_documentos() -> tuple[list[Document], list[str]]:
    """Fragmenta el corpus y genera identificadores reproducibles.

    Cada fragmento conserva los metadatos de su documento original
    e incorpora información adicional para su identificación.

    El identificador combina:
        - ID del documento municipal.
        - Posición del fragmento dentro del documento.
        - Huella SHA-256 del contenido del fragmento.

    Esta estructura permite reconocer fragmentos sin depender
    de identificadores aleatorios.

    Returns:
        tuple[list[Document], list[str]]:
            Una tupla con los fragmentos preparados y sus
            identificadores, en el mismo orden.

    Raises:
        FileNotFoundError: Si no existe el directorio del corpus.
        ValueError: Si los documentos originales no superan
            las validaciones del módulo de carga.
    """
    # Recupera los documentos originales previamente validados.
    documentos = obtener_corpus_municipal()

    # Configura la estrategia de fragmentación del corpus.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=SEPARADORES,
    )

    fragmentos = []
    identificadores = []

    for documento in documentos:
        # Divide cada documento de forma independiente para evitar
        # mezclar contenido y metadatos de diferentes fuentes.
        partes = splitter.split_documents([documento])

        for posicion, fragmento in enumerate(partes, start=1):
            # Calcula una huella del contenido para detectar cambios.
            # Un contenido diferente produce una huella diferente,
            # salvo la posibilidad teórica de colisiones hash.
            huella = sha256(
                fragmento.page_content.encode("utf-8")
            ).hexdigest()

            # Combina documento, posición y contenido para obtener
            # un identificador estable entre ejecuciones equivalentes.
            identificador = (
                f"{documento.metadata['id']}"
                f":{posicion:04d}"
                f":{huella}"
            )

            # Añade metadatos que facilitan la trazabilidad y
            # sincronización posterior con el índice vectorial.
            fragmento.metadata["chunk_id"] = identificador
            fragmento.metadata["chunk_index"] = posicion
            fragmento.metadata["content_sha256"] = huella

            fragmentos.append(fragmento)
            identificadores.append(identificador)

    return fragmentos, identificadores


def main() -> None:
    """Ejecuta la preparación y comprueba la integridad del corpus.

    Verifica que:
        - No existan identificadores de fragmentos duplicados.
        - Todos los documentos tengan al menos un fragmento.
        - Se haya generado al menos un fragmento.

    Raises:
        FileNotFoundError: Si falta el directorio del corpus.
        ValueError: Si existen documentos originales inválidos.
        RuntimeError: Si la preparación produce duplicados,
            omite documentos o no genera fragmentos.
    """
    documentos = obtener_corpus_municipal()
    fragmentos, identificadores = preparar_documentos()

    # Counter permite identificar IDs que aparecen más de una vez,
    # incluso cuando los fragmentos proceden de archivos distintos.
    duplicados = [
        identificador
        for identificador, cantidad in Counter(
            identificadores
        ).items()
        if cantidad > 1
    ]

    # Comprueba cuántos documentos originales están representados
    # en el conjunto de fragmentos preparados.
    documentos_representados = {
        fragmento.metadata["id"]
        for fragmento in fragmentos
    }

    # Muestra indicadores para comprobar la preparación documental.
    print("Documentos originales:", len(documentos))
    print("Chunks preparados:", len(fragmentos))
    print("IDs unicos:", len(set(identificadores)))
    print("Documentos representados:", len(documentos_representados))
    print("Duplicados:", len(duplicados))

    # Evita continuar con identificadores ambiguos.
    if duplicados:
        raise RuntimeError(
            "Se detectaron identificadores duplicados."
        )

    # Impide considerar válida una preparación incompleta.
    if len(documentos_representados) != len(documentos):
        raise RuntimeError(
            "No todos los documentos estan representados."
        )

    # Evita aprobar un corpus que no produjo contenido recuperable.
    if not fragmentos:
        raise RuntimeError(
            "No se generaron fragmentos."
        )

    print("PASS: Preparacion documental completada.")
    print("ChromaDB: sin modificaciones.")
    print("Gemini: sin llamadas.")


if __name__ == "__main__":
    # Solo ejecuta la validación cuando se invoca directamente
    # este archivo; importar sus funciones no inicia el proceso.
    main()
