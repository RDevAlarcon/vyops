
"""Pruebas unitarias del cálculo de costos de Gemini para VyOps.

Este módulo verifica la función calcular_costo(),
definida en src.consumir_gemini.

La prueba comprueba el cálculo del costo monetario
de una respuesta del modelo utilizando los metadatos
de consumo de tokens.

Se consideran tres categorías:

    - Tokens de entrada (promptTokenCount):
      Tokens utilizados para enviar la consulta al modelo.

    - Tokens de salida (candidatesTokenCount):
      Tokens correspondientes a la respuesta generada.

    - Tokens de razonamiento (thoughtsTokenCount):
      Tokens utilizados por el modelo durante
      su procesamiento interno.

Los precios proporcionados se expresan en USD
por cada millón de tokens.

La prueba verifica que los tokens de razonamiento
se incluyan en el cálculo del costo de salida,
según la fórmula utilizada en este escenario.

No se realizan solicitudes reales a Gemini.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Framework estándar de pruebas unitarias de Python.
import unittest

# Función encargada de calcular el costo monetario
# a partir de los metadatos de consumo de tokens.
from src.consumir_gemini import calcular_costo


# ============================================================
# 2. PRUEBAS DEL CÁLCULO DE COSTOS
# ============================================================

class TestCalculoCostos(unittest.TestCase):
    """Valida el cálculo de costos de consumo de tokens.

    Comprueba que calcular_costo() utilice correctamente
    las cantidades de tokens y las tarifas proporcionadas.

    Las verificaciones utilizan assertAlmostEqual()
    para controlar la precisión de los resultados decimales.
    """

    # --------------------------------------------------------
    # 2.1. COSTO DE ENTRADA, SALIDA Y RAZONAMIENTO
    # --------------------------------------------------------

    def test_calcula_costo_exacto_con_razonamiento(self):
        """Verifica el costo de entrada, salida y razonamiento.

        Escenario:
            - 1.000 tokens de entrada.
            - 200 tokens de salida.
            - 100 tokens de razonamiento.
            - 1.300 tokens totales informados.
            - Precio de entrada: 0,30 USD por millón.
            - Precio de salida: 2,50 USD por millón.

        Cálculo esperado:
            Costo de entrada:
                1000 * 0.30 / 1_000_000 = 0.00030 USD

            Costo de salida y razonamiento:
                (200 + 100) * 2.50 / 1_000_000
                = 0.00075 USD

            Costo total:
                0.00030 + 0.00075 = 0.00105 USD

        Verificación:
            El costo calculado debe coincidir con
            0.00105 USD, utilizando una precisión
            de diez posiciones decimales.
        """

        # Simula los metadatos de uso entregados
        # por una respuesta de Gemini.
        respuesta = {
            "usageMetadata": {
                "promptTokenCount": 1000,
                "candidatesTokenCount": 200,
                "thoughtsTokenCount": 100,
                "totalTokenCount": 1300,
            }
        }

        # Calcula el costo utilizando las tarifas
        # definidas para entrada y salida.
        costo = calcular_costo(
            respuesta,
            precio_entrada=0.30,
            precio_salida=2.50,
        )

        # Entrada: 1000 * 0.30 / 1_000_000 = 0.00030
        # Salida: (200 + 100) * 2.50 / 1_000_000 = 0.00075
        # Total esperado: 0.00105 USD
        self.assertAlmostEqual(costo, 0.00105, places=10)
