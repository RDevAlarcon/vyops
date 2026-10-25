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

from src.registro_costos import RegistroCostosSesion


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


    @patch("src.cliente_api.calcular_costo")
    @patch("src.cliente_api.extraer_texto")
    @patch("src.cliente_api.enviar_peticion")
    @patch("src.cliente_api.armar_peticion")
    def test_consultar_modelo_con_costos(
        self,
        armar,
        enviar,
        extraer,
        calcular,
    ):
        """Comprueba que una consulta registre su costo una sola vez."""

        # Creamos un registro independiente para esta sesión.
        registro = RegistroCostosSesion()

        # Simulamos la construcción de la solicitud.
        armar.return_value = (
            "https://ejemplo.invalid",
            {"x-goog-api-key": "clave_simulada"},
            {"contents": []},
        )

        # Simulamos una respuesta exitosa de Gemini.
        datos = {
            "usageMetadata": {
                "promptTokenCount": 100,
                "candidatesTokenCount": 50,
                "thoughtsTokenCount": 0,
            }
        }
        enviar.return_value = datos
        extraer.return_value = "Respuesta de prueba"
        calcular.return_value = 0.000155

        # Ejecutamos la consulta con registro de costos.
        from src.cliente_api import consultar_modelo_con_costos

        resultado = consultar_modelo_con_costos(
            "Consulta de prueba",
            registro,
        )

        # Comprobamos el resultado y el registro de la operación.
        self.assertEqual(resultado, "Respuesta de prueba")
        self.assertEqual(registro.obtener_operaciones(), [0.000155])
        self.assertAlmostEqual(registro.obtener_total(), 0.000155)

        # Verificamos que el costo se calcule una sola vez.
        calcular.assert_called_once()
        enviar.assert_called_once()


    @patch("src.cliente_api.enviar_peticion")
    @patch("src.cliente_api.armar_peticion")
    def test_consulta_fallida_no_registra_costo(self, armar, enviar):
        """Comprueba que una consulta fallida no genere cargos."""
        from src.cliente_api import consultar_modelo_con_costos

        registro = RegistroCostosSesion()

        armar.return_value = (
            "https://ejemplo.invalid",
            {"x-goog-api-key": "clave_simulada"},
            {"contents": []},
        )

        enviar.side_effect = RuntimeError("Error HTTP 503")

        with self.assertRaises(RuntimeError):
            consultar_modelo_con_costos(
                "Consulta de prueba",
                registro,
            )

        self.assertEqual(registro.obtener_operaciones(), [])
        self.assertEqual(registro.obtener_total(), 0.0)
        enviar.assert_called_once()


    @patch("src.cliente_api.calcular_costo")
    @patch("src.cliente_api.extraer_texto")
    @patch("src.cliente_api.enviar_peticion")
    @patch("src.cliente_api.armar_peticion")
    def test_acumula_costos_de_dos_consultas(
        self, armar, enviar, extraer, calcular,
    ):
        """Comprueba el costo acumulado de dos consultas exitosas."""
        from src.cliente_api import consultar_modelo_con_costos

        registro = RegistroCostosSesion()

        armar.return_value = (
            "https://ejemplo.invalid",
            {"x-goog-api-key": "clave_simulada"},
            {"contents": []},
        )
        enviar.return_value = {"usageMetadata": {}}
        extraer.side_effect = ["Primera respuesta", "Segunda respuesta"]
        calcular.side_effect = [0.00015, 0.00025]

        primera = consultar_modelo_con_costos("Primera consulta", registro)
        segunda = consultar_modelo_con_costos("Segunda consulta", registro)

        self.assertEqual(primera, "Primera respuesta")
        self.assertEqual(segunda, "Segunda respuesta")
        self.assertEqual(
            registro.obtener_operaciones(),
            [0.00015, 0.00025],
        )
        self.assertAlmostEqual(registro.obtener_total(), 0.00040)
        self.assertEqual(enviar.call_count, 2)
        self.assertEqual(calcular.call_count, 2)


    @patch("src.cliente_api.calcular_costo")
    @patch("src.cliente_api.extraer_texto")
    @patch("src.cliente_api.enviar_peticion")
    @patch("src.cliente_api.armar_peticion")
    def test_error_extraccion_no_registra_costo(
        self, armar, enviar, extraer, calcular,
    ):
        """Comprueba que una respuesta inválida no registre costos."""
        from src.cliente_api import consultar_modelo_con_costos

        registro = RegistroCostosSesion()

        armar.return_value = (
            "https://ejemplo.invalid",
            {"x-goog-api-key": "clave_simulada"},
            {"contents": []},
        )
        enviar.return_value = {"candidates": []}
        extraer.side_effect = ValueError("Respuesta sin texto")

        with self.assertRaises(ValueError):
            consultar_modelo_con_costos(
                "Consulta de prueba",
                registro,
            )

        self.assertEqual(registro.obtener_operaciones(), [])
        self.assertEqual(registro.obtener_total(), 0.0)
        calcular.assert_not_called()
        enviar.assert_called_once()


    @patch("src.cliente_api.calcular_costo")
    @patch("src.cliente_api.extraer_texto")
    @patch("src.cliente_api.enviar_peticion")
    @patch("src.cliente_api.armar_peticion")
    def test_error_calculo_no_registra_costo(
        self, armar, enviar, extraer, calcular,
    ):
        """Comprueba que un error de cálculo no altere el registro."""
        from src.cliente_api import consultar_modelo_con_costos

        registro = RegistroCostosSesion()

        armar.return_value = (
            "https://ejemplo.invalid",
            {"x-goog-api-key": "clave_simulada"},
            {"contents": []},
        )
        enviar.return_value = {"usageMetadata": {}}
        extraer.return_value = "Respuesta de prueba"
        calcular.side_effect = ValueError("Uso de tokens inválido")

        with self.assertRaises(ValueError):
            consultar_modelo_con_costos(
                "Consulta de prueba",
                registro,
            )

        self.assertEqual(registro.obtener_operaciones(), [])
        self.assertEqual(registro.obtener_total(), 0.0)
        calcular.assert_called_once()
        enviar.assert_called_once()


if __name__ == "__main__":
    unittest.main()
