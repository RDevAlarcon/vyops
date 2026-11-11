
"""Compara estrategias de división de texto para RAG."""

from langchain_text_splitters import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
)


def obtener_texto_prueba() -> str:
    """Devuelve el texto de ejemplo utilizado en SkillNest."""
    return (
        "El cliente reintenta hasta 3 veces ante un TimeoutError, con espera creciente "
        "entre intento e intento.\n\n"
        "Los errores de autenticación nunca se reintentan: fallan de inmediato con un "
        "ValueError, sin ninguna espera.\n\n"
        "El costo de cada llamada se acumula en una variable de sesión mientras el "
        "programa sigue corriendo."
    )


def dividir_recursivamente(texto: str) -> list[str]:
    """Divide el texto respetando límites naturales cuando sea posible."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=100,
        chunk_overlap=20,
    )

    return splitter.split_text(texto)


def main() -> None:
    """Prepara el texto para comparar ambas estrategias."""
    texto = obtener_texto_prueba()

    print("Comparación de estrategias de chunking")
    print(f"Caracteres del texto original: {len(texto)}")

    fragmentos = dividir_por_caracteres(texto)

    print("\n--- Chunking por caracteres ---")
    print(f"Cantidad de chunks: {len(fragmentos)}")

    for indice, fragmento in enumerate(fragmentos, start=1):
        print(f"\nChunk {indice} ({len(fragmento)} caracteres):")
        print(repr(fragmento))

    fragmentos_recursivos = dividir_recursivamente(texto)

    print("\n--- Chunking recursivo ---")
    print(f"Cantidad de chunks: {len(fragmentos_recursivos)}")

    for indice, fragmento in enumerate(fragmentos_recursivos, start=1):
        print(f"\nChunk {indice} ({len(fragmento)} caracteres):")
        print(repr(fragmento))


def dividir_por_caracteres(texto: str) -> list[str]:
    """Divide el texto en fragmentos de tamaño fijo."""
    splitter = CharacterTextSplitter(
        separator="",
        chunk_size=100,
        chunk_overlap=20,
    )

    return splitter.split_text(texto)

if __name__ == "__main__":
    main()
