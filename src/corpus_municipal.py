"""Carga y validacion del corpus municipal ficticio de VyOps."""

from pathlib import Path
import re

import yaml
from langchain_core.documents import Document


BASE_DIR = Path(__file__).resolve().parent.parent
CORPUS_DIR = BASE_DIR / "corpus"

CAMPOS_OBLIGATORIOS = (
    "id",
    "titulo",
    "institucion",
    "categoria",
    "version",
    "fecha",
    "estado",
    "clasificacion",
)


def obtener_corpus_municipal() -> list[Document]:
    """Carga los documentos Markdown y conserva sus metadatos YAML."""
    if not CORPUS_DIR.is_dir():
        raise FileNotFoundError(
            f"No existe el directorio del corpus: {CORPUS_DIR}"
        )

    archivos = sorted(CORPUS_DIR.rglob("*.md"))

    if not archivos:
        raise ValueError("El corpus no contiene documentos Markdown.")

    documentos = []
    identificadores = set()

    for archivo in archivos:
        texto = archivo.read_text(encoding="utf-8-sig")

        coincidencia = re.match(
            r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)",
            texto,
            flags=re.DOTALL,
        )

        if coincidencia is None:
            raise ValueError(
                f"Encabezado YAML invalido: {archivo}"
            )

        metadatos = yaml.safe_load(coincidencia.group(1))

        if not isinstance(metadatos, dict):
            raise ValueError(
                f"Metadatos YAML invalidos: {archivo}"
            )

        faltantes = [
            campo
            for campo in CAMPOS_OBLIGATORIOS
            if campo not in metadatos
            or metadatos[campo] is None
            or str(metadatos[campo]).strip() == ""
        ]

        if faltantes:
            raise ValueError(
                f"Metadatos faltantes en {archivo}: {faltantes}"
            )

        identificador = str(metadatos["id"])

        if identificador in identificadores:
            raise ValueError(
                f"Identificador duplicado: {identificador}"
            )

        identificadores.add(identificador)

        contenido = texto[coincidencia.end():].strip()

        if not contenido:
            raise ValueError(
                f"Documento sin contenido: {archivo}"
            )

        ruta_relativa = archivo.relative_to(CORPUS_DIR).as_posix()

        metadata = {
            clave: str(valor)
            for clave, valor in metadatos.items()
        }

        metadata["source"] = ruta_relativa
        metadata["fuente"] = ruta_relativa
        metadata["documento_id"] = identificador

        documentos.append(
            Document(
                page_content=contenido,
                metadata=metadata,
            )
        )

    return documentos
