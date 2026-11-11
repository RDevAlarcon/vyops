
"""Indexación del corpus municipal ficticio de VyOps."""

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.corpus_municipal import obtener_corpus_municipal


def preparar_documentos() -> list[Document]:
    """Divide el corpus en fragmentos para su indexación."""
    documentos = obtener_corpus_municipal()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=30,
    )

    return splitter.split_documents(documentos)



def main() -> None:
    """Genera embeddings y persiste el corpus en ChromaDB."""
    load_dotenv()

    fragmentos = preparar_documentos()

    print(f"Documentos originales: {len(obtener_corpus_municipal())}")
    print(f"Chunks preparados: {len(fragmentos)}")

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
    )

    print("Generando embeddings con Gemini...")

    base_vectorial = Chroma.from_documents(
        documents=fragmentos,
        embedding=embeddings,
        persist_directory="vectorstore/",
    )

    total = base_vectorial._collection.count()

    print(f"Registros almacenados en ChromaDB: {total}")

    if total != len(fragmentos):
        raise RuntimeError(
            "La cantidad de registros no coincide con los chunks."
        )

    print("Indexación completada correctamente.")



if __name__ == "__main__":
    main()
