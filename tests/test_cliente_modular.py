
"""Pruebas unitarias del cliente modular de Gemini para VyOps.

Bloque 12 — SkillNest.

Verifica que la interfaz pública consultar_modelo() coordine
correctamente las funciones de construcción, envío y extracción
de respuestas.

Utiliza mocks para simular las operaciones del cliente sin
realizar solicitudes reales a la API de Gemini.
"""

import unittest
from unittest.mock import patch

from src.cliente_api import consultar_modelo


class TestClienteModular(unittest.TestCase):
    """Valida la integración y propagación de errores del cliente."""

    @patch("src.cliente_api.extraer_texto")
    @patch("src.cliente_api.enviar_peticion")
    @patch("src.cliente_api.armar_peticion")
    def test_consultar_modelo(
        self,
        armar,
        enviar,
        extraer,
    ):
        """Comprueba la ejecución ordenada de las tres etapas.

        Verifica que consultar_modelo() construya la solicitud,
        entregue sus datos a la función de envío y devuelva
        el texto extraído de la respuesta simulada.
        """

        # Simulamos los datos necesarios para construir la solicitud.
        armar.return_value = (
            "https://ejemplo.invalid",
            {"x-goog-api-key": "clave_simulada"},
            {"contents": []},
        )

        # Simulamos la respuesta de Gemini y el texto extraído.
        enviar.return_value = {"candidates": []}
        extraer.return_value = "Santiago"

        resultado = consultar_modelo(
            "¿Cuál es la capital de Chile?"
        )

        # Verificamos el resultado y los argumentos de cada etapa.
        self.assertEqual(resultado, "Santiago")

        armar.assert_called_once_with(
            "¿Cuál es la capital de Chile?",
            None,
        )

        enviar.assert_called_once_with(
            "https://ejemplo.invalid",
            {"x-goog-api-key": "clave_simulada"},
            {"contents": []},
        )

        extraer.assert_called_once_with(
            {"candidates": []}
        )

    @patch("src.cliente_api.extraer_texto")
    @patch("src.cliente_api.enviar_peticion")
    @patch("src.cliente_api.armar_peticion")
    def test_consultar_modelo_propaga_error_del_cliente(
        self,
        armar,
        enviar,
        extraer,
    ):
        """Comprueba la propagación de errores del envío.

        Simula un RuntimeError durante la comunicación con Gemini.

        Verifica que consultar_modelo() conserve la excepción
        y no intente extraer texto cuando falla el envío.
        """

        # Preparamos una solicitud simulada.
        armar.return_value = (
            "https://ejemplo.invalid",
            {"x-goog-api-key": "clave_simulada"},
            {"contents": []},
        )

        # Simulamos un fallo definitivo de comunicación.
        enviar.side_effect = RuntimeError(
            "El servicio tardó demasiado en responder."
        )

        # Comprobamos que el error llegue al módulo que consulta.
        with self.assertRaisesRegex(
            RuntimeError,
            "El servicio tardó demasiado en responder",
        ):
            consultar_modelo("Consulta de prueba")

        # El envío ocurre una vez y no se procesa una respuesta.
        enviar.assert_called_once()
        extraer.assert_not_called()


if __name__ == "__main__":
    unittest.main()
