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