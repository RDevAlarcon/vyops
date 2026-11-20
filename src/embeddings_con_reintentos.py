"""Adaptador de embeddings con reintentos controlados para Gemini."""

import time

from google.genai.errors import APIError
from langchain_core.embeddings import Embeddings
from langchain_google_genai._common import GoogleGenerativeAIError


CODIGOS_REINTENTABLES = {429, 500, 502, 503}


class EmbeddingsConReintentos(Embeddings):
    """Reintenta errores temporales antes de escribir en ChromaDB."""

    def __init__(
        self,
        embeddings: Embeddings,
        max_intentos: int = 3,
        espera_inicial: float = 2.0,
    ):
        if max_intentos < 1:
            raise ValueError("max_intentos debe ser al menos 1.")

        if espera_inicial < 0:
            raise ValueError("espera_inicial no puede ser negativa.")

        self.embeddings = embeddings
        self.max_intentos = max_intentos
        self.espera_inicial = espera_inicial

    @staticmethod
    def _codigo_http(error: Exception) -> int | None:
        """Busca el código HTTP en la cadena de excepciones."""

        actual = error
        visitados = set()

        while actual is not None and id(actual) not in visitados:
            visitados.add(id(actual))

            if isinstance(actual, APIError):
                return actual.code

            actual = actual.__cause__

        return None

    def _ejecutar(self, operacion, *args):
        """Ejecuta una operación y reintenta solo errores recuperables."""

        for intento in range(1, self.max_intentos + 1):
            try:
                return operacion(*args)

            except GoogleGenerativeAIError as error:
                codigo = self._codigo_http(error)

                if (
                    codigo not in CODIGOS_REINTENTABLES
                    or intento == self.max_intentos
                ):
                    raise

                espera = self.espera_inicial * (2 ** (intento - 1))
                time.sleep(espera)

        raise RuntimeError("Estado de reintentos inesperado.")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Genera embeddings de documentos con reintentos limitados."""

        return self._ejecutar(self.embeddings.embed_documents, texts)

    def embed_query(self, text: str) -> list[float]:
        """Genera el embedding de una consulta con reintentos limitados."""

        return self._ejecutar(self.embeddings.embed_query, text)
