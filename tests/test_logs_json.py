import json
import logging
import unittest

from logs_json import JsonFormatter
from traza_contexto import trace_id_var


class TestLogsJson(unittest.TestCase):

    def test_trace_id_automatico_desde_contextvars(self):
        token = trace_id_var.set("trace-prueba-001")

        try:
            registro = logging.LogRecord(
                name="rag_pipeline",
                level=logging.INFO,
                pathname=__file__,
                lineno=1,
                msg="consulta_iniciada",
                args=(),
                exc_info=None,
            )

            resultado = JsonFormatter().format(registro)
            datos = json.loads(resultado)

            self.assertEqual(
                datos["trace_id"],
                "trace-prueba-001",
            )
            self.assertEqual(
                datos["msg"],
                "consulta_iniciada",
            )
            self.assertEqual(
                datos["level"],
                "INFO",
            )

        finally:
            trace_id_var.reset(token)

    def test_consultas_independientes_tienen_trazas_distintas(self):
        formatter = JsonFormatter()
        identificadores = []

        for indice in range(2):
            token = trace_id_var.set(f"trace-consulta-{indice}")

            try:
                registro = logging.LogRecord(
                    name="rag_pipeline",
                    level=logging.INFO,
                    pathname=__file__,
                    lineno=1,
                    msg="consulta_iniciada",
                    args=(),
                    exc_info=None,
                )

                datos = json.loads(formatter.format(registro))
                identificadores.append(datos["trace_id"])

            finally:
                trace_id_var.reset(token)

        self.assertEqual(
            identificadores,
            ["trace-consulta-0", "trace-consulta-1"],
        )
        self.assertIsNone(trace_id_var.get())
    def test_no_expone_datos_sensibles(self):
        registro = logging.LogRecord(
            name="rag_pipeline",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="consulta_iniciada",
            args=(),
            exc_info=None,
        )

        registro.extra_data = {
            "pregunta": "Mi RUT es 12345678-9",
            "respuesta": "Información privada",
            "pregunta_len": 20,
            "k": 3,
        }

        resultado = JsonFormatter().format(registro)
        datos = json.loads(resultado)

        self.assertNotIn("pregunta", datos)
        self.assertNotIn("respuesta", datos)
        self.assertNotIn("12345678-9", resultado)
        self.assertNotIn("Información privada", resultado)

        self.assertEqual(datos["pregunta_len"], 20)
        self.assertEqual(datos["k"], 3)

    def test_no_expone_mensaje_sensible(self):
        registro = logging.LogRecord(
            name="rag_pipeline",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="Consulta del usuario: Mi RUT es 12345678-9",
            args=(),
            exc_info=None,
        )

        resultado = JsonFormatter().format(registro)
        datos = json.loads(resultado)

        self.assertNotIn("12345678-9", resultado)
        self.assertNotIn("Consulta del usuario", resultado)
        self.assertEqual(
            datos["msg"],
            "evento_no_autorizado",
        )

    def test_modelo_autorizado_y_modelo_sensible(self):
        from configuracion_modelos import MODELO_GENERACION

        registro = logging.LogRecord(
            name="rag_pipeline",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="generacion_iniciada",
            args=(),
            exc_info=None,
        )

        registro.extra_data = {
            "modelo": MODELO_GENERACION,
            "n_documentos": 3,
        }

        datos = json.loads(JsonFormatter().format(registro))

        self.assertEqual(datos["modelo"], MODELO_GENERACION)
        self.assertEqual(datos["n_documentos"], 3)

        registro.extra_data = {
            "modelo": "Mi RUT es 12345678-9",
            "n_documentos": 3,
        }

        resultado = JsonFormatter().format(registro)
        datos = json.loads(resultado)

        self.assertNotIn("modelo", datos)
        self.assertNotIn("12345678-9", resultado)
        self.assertEqual(datos["n_documentos"], 3)

    def test_descarta_numeros_no_finitos(self):
        registro = logging.LogRecord(
            name="rag_pipeline",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="documentos_recuperados",
            args=(),
            exc_info=None,
        )

        registro.extra_data = {
            "n_documentos": 3,
            "latencia_ms": float("nan"),
        }

        resultado = JsonFormatter().format(registro)
        datos = json.loads(resultado)

        self.assertEqual(datos["n_documentos"], 3)
        self.assertNotIn("latencia_ms", datos)
        self.assertNotIn("NaN", resultado)
