"""Pruebas de verificacion del indice del servicio RAG."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import servicio_vyops_rag


class TestServicioRAGIndice(unittest.TestCase):
    """Valida el indice sin consultar Gemini ni modificar ChromaDB."""

    def test_reconoce_directorio_configurado(self):
        """Acepta un directorio existente con identificadores."""
        with tempfile.TemporaryDirectory() as temporal:
            directorio = Path(temporal)

            with (
                patch.object(
                    servicio_vyops_rag,
                    "obtener_directorio_vectorial",
                    return_value=directorio,
                ),
                patch.object(
                    servicio_vyops_rag,
                    "obtener_ids_existentes",
                    return_value={"doc-1", "doc-2"},
                ),
            ):
                resultado = servicio_vyops_rag.verificar_indice()

            self.assertEqual(resultado["fragmentos_persistidos"], 2)
            self.assertTrue(resultado["ids_unicos"])

    def test_rechaza_directorio_inexistente(self):
        """Rechaza una ruta inexistente sin crearla."""
        with tempfile.TemporaryDirectory() as temporal:
            directorio = Path(temporal) / "indice_inexistente"

            with (
                patch.object(
                    servicio_vyops_rag,
                    "obtener_directorio_vectorial",
                    return_value=directorio,
                ),
                patch.object(
                    servicio_vyops_rag,
                    "obtener_ids_existentes",
                ) as consultar_ids,
            ):
                with self.assertRaises(RuntimeError):
                    servicio_vyops_rag.verificar_indice()

            self.assertFalse(directorio.exists())
            consultar_ids.assert_not_called()

    def test_rechaza_coleccion_vacia(self):
        """Rechaza un indice existente sin identificadores."""
        with tempfile.TemporaryDirectory() as temporal:
            directorio = Path(temporal)

            with (
                patch.object(
                    servicio_vyops_rag,
                    "obtener_directorio_vectorial",
                    return_value=directorio,
                ),
                patch.object(
                    servicio_vyops_rag,
                    "obtener_ids_existentes",
                    return_value=set(),
                ),
            ):
                with self.assertRaisesRegex(RuntimeError, "vac"):
                    servicio_vyops_rag.verificar_indice()


if __name__ == "__main__":
    unittest.main()