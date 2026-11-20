"""Pruebas aisladas de las pausas durante la indexación."""

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from langchain_core.documents import Document

from src.indexacion_incremental import sincronizar


class TestPausasIndexacion(unittest.TestCase):
    """Comprueba los lotes y las pausas sin utilizar Gemini."""

    def ejecutar_sincronizacion(self, cantidad, pausa="10", existentes=False):
        """Simula una sincronización con 30 documentos representados."""

        documentos = [
            Document(
                page_content=f"Contenido {i}",
                metadata={"id": f"doc-{i % 30}"},
            )
            for i in range(cantidad)
        ]
        identificadores = [f"fragmento-{i}" for i in range(cantidad)]

        db = MagicMock()
        db.get.return_value = {
            "ids": identificadores if existentes else []
        }
        db._collection.count.return_value = cantidad

        with TemporaryDirectory() as temporal:
            with (
                patch(
                    "src.indexacion_incremental.preparar_documentos",
                    return_value=(documentos, identificadores),
                ),
                patch("src.indexacion_incremental.Chroma", return_value=db),
                patch("src.indexacion_incremental.bloqueo_indexacion"),
                patch("src.indexacion_incremental.time.sleep") as dormir,
                patch.dict(
                    os.environ,
                    {"VYOPS_EMBEDDING_PAUSA_SEGUNDOS": pausa},
                ),
            ):
                resultado = sincronizar(Path(temporal), MagicMock())

        return dormir.call_args_list, db.add_documents.call_args_list, resultado

    def test_treinta_fragmentos_generan_dos_pausas(self):
        pausas, lotes, _ = self.ejecutar_sincronizacion(30)
        self.assertEqual(len(lotes), 3)
        self.assertEqual(len(pausas), 2)

    def test_cincuenta_fragmentos_generan_cuatro_pausas(self):
        pausas, lotes, _ = self.ejecutar_sincronizacion(50)
        self.assertEqual(len(lotes), 5)
        self.assertEqual(len(pausas), 4)

    def test_setenta_y_cinco_fragmentos_generan_siete_pausas(self):
        pausas, lotes, _ = self.ejecutar_sincronizacion(75)
        self.assertEqual(len(lotes), 8)
        self.assertEqual(len(pausas), 7)
        self.assertEqual(len(lotes[-1].kwargs["documents"]), 5)

    def test_pausa_configurable(self):
        pausas, _, _ = self.ejecutar_sincronizacion(30, pausa="20")
        self.assertTrue(all(p.args[0] == 20 for p in pausas))

    def test_sin_cambios_no_genera_pausas(self):
        pausas, lotes, resultado = self.ejecutar_sincronizacion(
            30, existentes=True
        )
        self.assertEqual(len(lotes), 0)
        self.assertEqual(len(pausas), 0)
        self.assertEqual(resultado["insertados"], 0)

    def test_pausa_invalida_se_rechaza(self):
        with self.assertRaises(ValueError):
            self.ejecutar_sincronizacion(30, pausa="-1")

    def test_lotes_no_superan_diez_fragmentos(self):
        _, lotes, _ = self.ejecutar_sincronizacion(75)
        self.assertTrue(
            all(len(llamada.kwargs["documents"]) <= 10 for llamada in lotes)
        )


if __name__ == "__main__":
    unittest.main()
