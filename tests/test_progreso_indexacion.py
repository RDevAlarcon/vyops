
"""Pruebas del progreso de indexacion sin consumir Gemini."""

import io
import os
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from langchain_core.documents import Document

from src.indexacion_incremental import sincronizar


class TestProgresoIndexacion(unittest.TestCase):
    """Valida los mensajes y evita reportar inserciones fallidas."""

    def ejecutar(self, cantidad=30, existentes=(), fallar=False):
        """Ejecuta la sincronizacion con dependencias simuladas."""
        documentos = [
            Document(
                page_content=f"Contenido {i}",
                metadata={"id": f"doc-{i % 30}"},
            )
            for i in range(cantidad)
        ]
        identificadores = [
            f"fragmento-{i}" for i in range(cantidad)
        ]

        db = MagicMock()
        db.get.return_value = {"ids": list(existentes)}
        db._collection.count.return_value = cantidad

        if fallar:
            db.add_documents.side_effect = RuntimeError(
                "Fallo simulado de persistencia"
            )

        salida = io.StringIO()
        error = None
        resultado = None

        with TemporaryDirectory() as temporal:
            with (
                patch(
                    "src.indexacion_incremental.preparar_documentos",
                    return_value=(documentos, identificadores),
                ),
                patch(
                    "src.indexacion_incremental.Chroma",
                    return_value=db,
                ),
                patch("src.indexacion_incremental.bloqueo_indexacion"),
                patch("src.indexacion_incremental.time.sleep") as dormir,
                patch.dict(
                    os.environ,
                    {"VYOPS_EMBEDDING_PAUSA_SEGUNDOS": "10"},
                ),
                redirect_stdout(salida),
            ):
                try:
                    resultado = sincronizar(
                        Path(temporal),
                        MagicMock(),
                    )
                except RuntimeError as excepcion:
                    error = excepcion

        return salida.getvalue(), resultado, error, db, dormir

    def test_progreso_llega_a_cien_por_ciento(self):
        salida, resultado, error, db, _ = self.ejecutar(30)

        self.assertIsNone(error)
        self.assertIn("[INDEXACION] Lote 1/3", salida)
        self.assertIn("[INDEXACION] Lote 3/3", salida)
        self.assertIn("30/30 nuevos fragmentos persistidos", salida)
        self.assertIn("100.0%", salida)
        self.assertEqual(resultado["insertados"], 30)
        self.assertEqual(db.add_documents.call_count, 3)

    def test_distingue_conservados_y_pendientes(self):
        existentes = [f"fragmento-{i}" for i in range(10)]

        salida, resultado, error, db, _ = self.ejecutar(
            30,
            existentes=existentes,
        )

        self.assertIsNone(error)
        self.assertIn("Conservados: 10 | Pendientes: 20", salida)
        self.assertIn("20/20 nuevos fragmentos persistidos", salida)
        self.assertIn("100.0%", salida)
        self.assertEqual(resultado["conservados"], 10)
        self.assertEqual(resultado["insertados"], 20)
        self.assertEqual(db.add_documents.call_count, 2)

    def test_sin_cambios_no_indexa_ni_espera(self):
        existentes = [f"fragmento-{i}" for i in range(30)]

        salida, resultado, error, db, dormir = self.ejecutar(
            30,
            existentes=existentes,
        )

        self.assertIsNone(error)
        self.assertIn("Pendientes: 0", salida)
        self.assertIn(
            "[PASS] No hay fragmentos nuevos para indexar.",
            salida,
        )
        self.assertEqual(resultado["insertados"], 0)
        db.add_documents.assert_not_called()
        dormir.assert_not_called()

    def test_lote_fallido_no_se_anuncia_persistido(self):
        salida, resultado, error, db, dormir = self.ejecutar(
            30,
            fallar=True,
        )

        self.assertIsNone(resultado)
        self.assertIsInstance(error, RuntimeError)
        self.assertIn("[INDEXACION] Lote 1/3", salida)
        self.assertNotIn("[PROGRESO]", salida)
        self.assertNotIn("[FINALIZADO]", salida)
        self.assertEqual(db.add_documents.call_count, 1)
        dormir.assert_not_called()


if __name__ == "__main__":
    unittest.main()
