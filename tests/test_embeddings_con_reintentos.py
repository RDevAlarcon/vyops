import unittest
from unittest.mock import Mock, patch

from google.genai.errors import ClientError, ServerError
from langchain_google_genai._common import GoogleGenerativeAIError

from src.embeddings_con_reintentos import EmbeddingsConReintentos


def error_gemini(codigo):
    """Construye un error de LangChain con su causa HTTP original."""
    clase = ClientError if codigo < 500 else ServerError
    causa = clase(
        code=codigo,
        response_json={"error": {"message": "Error simulado"}},
    )
    error = GoogleGenerativeAIError("Error simulado")
    error.__cause__ = causa
    return error


class TestEmbeddingsConReintentos(unittest.TestCase):

    @patch("src.embeddings_con_reintentos.time.sleep")
    def test_exito_inmediato(self, dormir):
        proveedor = Mock()
        proveedor.embed_documents.return_value = [[0.1, 0.2]]

        adaptador = EmbeddingsConReintentos(proveedor)

        self.assertEqual(
            adaptador.embed_documents(["documento"]),
            [[0.1, 0.2]],
        )
        self.assertEqual(proveedor.embed_documents.call_count, 1)
        dormir.assert_not_called()

    @patch("src.embeddings_con_reintentos.time.sleep")
    def test_429_recuperable(self, dormir):
        proveedor = Mock()
        proveedor.embed_documents.side_effect = [
            error_gemini(429),
            [[0.1, 0.2]],
        ]

        adaptador = EmbeddingsConReintentos(proveedor)

        self.assertEqual(
            adaptador.embed_documents(["documento"]),
            [[0.1, 0.2]],
        )
        self.assertEqual(proveedor.embed_documents.call_count, 2)
        dormir.assert_called_once_with(2.0)

    @patch("src.embeddings_con_reintentos.time.sleep")
    def test_503_agota_intentos(self, dormir):
        proveedor = Mock()
        proveedor.embed_documents.side_effect = error_gemini(503)

        adaptador = EmbeddingsConReintentos(proveedor)

        with self.assertRaises(GoogleGenerativeAIError):
            adaptador.embed_documents(["documento"])

        self.assertEqual(proveedor.embed_documents.call_count, 3)
        self.assertEqual(
            [llamada.args[0] for llamada in dormir.call_args_list],
            [2.0, 4.0],
        )

    @patch("src.embeddings_con_reintentos.time.sleep")
    def test_401_no_reintenta(self, dormir):
        proveedor = Mock()
        proveedor.embed_documents.side_effect = error_gemini(401)

        adaptador = EmbeddingsConReintentos(proveedor)

        with self.assertRaises(GoogleGenerativeAIError):
            adaptador.embed_documents(["documento"])

        self.assertEqual(proveedor.embed_documents.call_count, 1)
        dormir.assert_not_called()


if __name__ == "__main__":
    unittest.main()
