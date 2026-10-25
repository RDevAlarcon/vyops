import unittest

from src.consumir_gemini import calcular_costo


class TestCalculoCostos(unittest.TestCase):

    def test_calcula_costo_exacto_con_razonamiento(self):
        """Verifica el costo de entrada, salida y razonamiento."""

        respuesta = {
            "usageMetadata": {
                "promptTokenCount": 1000,
                "candidatesTokenCount": 200,
                "thoughtsTokenCount": 100,
                "totalTokenCount": 1300,
            }
        }

        costo = calcular_costo(
            respuesta,
            precio_entrada=0.30,
            precio_salida=2.50,
        )

        # Entrada: 1000 * 0.30 / 1_000_000 = 0.00030
        # Salida: (200 + 100) * 2.50 / 1_000_000 = 0.00075
        # Total esperado: 0.00105 USD
        self.assertAlmostEqual(costo, 0.00105, places=10)