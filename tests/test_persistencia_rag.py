
import json
import tempfile
import unittest
from pathlib import Path

from persistencia_rag import guardar_registro_jsonl


class TestPersistenciaRAG(unittest.TestCase):

    def test_guardar_y_acumular_registros(self):
        resultado = {
            "trace_id": "traza-prueba-001",
            "modelo_generacion": "gemini-3.5-flash-lite",
            "modelo_embedding": "gemini-embedding-001",
            "pregunta": "¿Cómo consultar una solicitud?",
            "fuentes": ["solicitudes_consulta.md"],
            "tiempos": {
                "recuperacion": 0.5,
                "generacion": 1.2,
                "total_rag": 1.8,
                "total_completo": 2.0,
            },
            "tokens_entrada": 100,
            "tokens_salida": 50,
            "tokens_totales": 150,
            "tokens_razonamiento": None,
            "tokens_cache": 0,
            "tokens_embedding": 8,
            "uso_original": {
                "input_tokens": 100,
                "output_tokens": 50,
                "total_tokens": 150,
            },
            "costo_generacion_usd": 0.000155,
            "costo_embedding_usd": 0.0000012,
            "costo_total_usd": 0.0001562,
            "validacion_citas": {
                "citas_encontradas": 1,
                "citas_invalidas": [],
                "numeracion_valida": True,
            },
        }

        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "prueba_rag.jsonl"

            guardar_registro_jsonl(resultado, ruta)
            guardar_registro_jsonl(resultado, ruta)

            lineas = ruta.read_text(
                encoding="utf-8"
            ).splitlines()

            self.assertEqual(len(lineas), 2)

            registros = [
                json.loads(linea) for linea in lineas
            ]

            self.assertEqual(
                registros[0]["tokens_totales"], 150
            )
            self.assertIsNone(
                registros[0]["tokens_razonamiento"]
            )
            self.assertEqual(
                registros[1]["modelo_generacion"],
                "gemini-3.5-flash-lite",
            )
            self.assertIn("timestamp", registros[0])
            self.assertEqual(
                registros[0]["trace_id"],
                "traza-prueba-001",
            )
            self.assertEqual(
                registros[1]["trace_id"],
                "traza-prueba-001",
            )

    def test_no_guardar_pregunta_completa(self):
        pregunta = "Mi RUT es 12345678-9"

        resultado = {
            "modelo_generacion": "modelo-prueba",
            "modelo_embedding": "embedding-prueba",
            "pregunta": pregunta,
            "fuentes": [],
            "tiempos": {
                "total_rag": 0.5,
                "total_completo": 0.6,
            },
            "tokens_entrada": 10,
            "tokens_salida": 5,
            "tokens_totales": 15,
            "tokens_razonamiento": None,
            "tokens_cache": None,
            "tokens_embedding": 3,
            "uso_original": {},
            "costo_generacion_usd": 0.0,
            "costo_embedding_usd": 0.0,
            "costo_total_usd": 0.0,
            "validacion_citas": {},
        }

        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "privacidad.jsonl"

            guardar_registro_jsonl(resultado, ruta)

            contenido = ruta.read_text(encoding="utf-8")
            registro = json.loads(contenido)

            self.assertNotIn(pregunta, contenido)
            self.assertNotIn("pregunta", registro)
            self.assertEqual(
                registro["pregunta_longitud"],
                len(pregunta),
            )

if __name__ == "__main__":
    unittest.main()
