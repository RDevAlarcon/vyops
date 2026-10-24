
"""Pruebas unitarias del cliente HTTP de Gemini para VyOps.

Bloque 12 — SkillNest.

Verifica el manejo de errores de autenticación, respuestas HTTP
temporales, tiempos de espera y políticas de reintentos.

Las solicitudes HTTP y las pausas se simulan mediante mocks.
No se realizan llamadas reales a Gemini ni se utilizan API keys.
"""

import unittest
from unittest.mock import Mock, patch

import requests

from src.consumir_gemini import enviar_peticion


class TestClienteGemini(unittest.TestCase):
    """Valida los errores HTTP y los reintentos del cliente."""

    @patch("src.consumir_gemini.requests.post")
    def test_error_400_no_reintenta(self, peticion):
        """Comprueba que HTTP 400 se informe sin reintentos.

        Simula una solicitud rechazada por Gemini, que puede
        deberse a una API key inválida o a parámetros incorrectos.

        Verifica que el cliente genere un RuntimeError con un
        mensaje orientativo y realice un único intento HTTP.
        """

        # Simulamos una respuesta HTTP 400 del proveedor.
        respuesta = Mock(spec=requests.Response)
        respuesta.status_code = 400
        respuesta.raise_for_status.side_effect = requests.HTTPError(
            "400 Bad Request",
            response=respuesta,
        )

        peticion.return_value = respuesta

        # Comprobamos que el error se comunique correctamente.
        with self.assertRaisesRegex(
            RuntimeError,
            "Gemini rechazó la solicitud \\(HTTP 400\\)",
        ):
            enviar_peticion(
                "https://ejemplo.invalid",
                {"x-goog-api-key": "clave_simulada"},
                {"contents": []},
            )

        # HTTP 400 no debe activar reintentos automáticos.
        peticion.assert_called_once()
    @patch("src.consumir_gemini.requests.post")
    def test_error_401_no_reintenta(self, peticion):
        """Comprueba que HTTP 401 detenga la solicitud sin reintentos.

        Simula un rechazo de autenticación y verifica que el cliente
        informe el error y realice un único intento de conexión.
        """

        # Simulamos una respuesta HTTP 401.
        respuesta = Mock(spec=requests.Response)
        respuesta.status_code = 401
        respuesta.raise_for_status.side_effect = requests.HTTPError(
            "401 Unauthorized",
            response=respuesta,
        )

        peticion.return_value = respuesta

        # El error debe propagarse como RuntimeError.
        with self.assertRaisesRegex(
            RuntimeError,
            "La API rechazó la autenticación o el acceso",
        ):
            enviar_peticion(
                "https://ejemplo.invalid",
                {"x-goog-api-key": "clave_simulada"},
                {"contents": []},
            )

        # Los errores de autenticación no deben reintentarse.
        peticion.assert_called_once()

    @patch("src.consumir_gemini.time.sleep")
    @patch("src.consumir_gemini.requests.post")
    def test_error_429_reintenta(self, peticion, espera):
        """Comprueba los reintentos exponenciales ante HTTP 429.

        Simula dos respuestas de límite de solicitudes y una
        respuesta exitosa. Verifica tres intentos y pausas
        de 2 y 4 segundos, sin realizar esperas reales.
        """

        respuestas = []

        # Dos errores HTTP 429 seguidos de una respuesta exitosa.
        for codigo in (429, 429, 200):
            respuesta = Mock(spec=requests.Response)
            respuesta.status_code = codigo
            respuesta.headers = {}

            if codigo == 429:
                respuesta.raise_for_status.side_effect = (
                    requests.HTTPError(
                        "429 Too Many Requests",
                        response=respuesta,
                    )
                )
            else:
                respuesta.raise_for_status.return_value = None
                respuesta.json.return_value = {"resultado": "OK"}

            respuestas.append(respuesta)

        peticion.side_effect = respuestas

        resultado = enviar_peticion(
            "https://ejemplo.invalid",
            {"x-goog-api-key": "clave_simulada"},
            {"contents": []},
        )

        # Verificamos la recuperación y el backoff exponencial.
        self.assertEqual(resultado, {"resultado": "OK"})
        self.assertEqual(peticion.call_count, 3)
        self.assertEqual(
            [llamada.args[0] for llamada in espera.call_args_list],
            [2, 4],
        )

    @patch("src.consumir_gemini.time.sleep")
    @patch("src.consumir_gemini.requests.post")
    def test_error_503_reintenta(self, peticion, espera):
        """Comprueba la recuperación tras un error HTTP 503.

        Simula una indisponibilidad temporal del servicio seguida
        de una respuesta exitosa. Verifica dos intentos y una
        pausa simulada de 2 segundos.
        """

        respuesta_error = Mock(spec=requests.Response)
        respuesta_error.status_code = 503
        respuesta_error.headers = {}
        respuesta_error.raise_for_status.side_effect = (
            requests.HTTPError(
                "503 Service Unavailable",
                response=respuesta_error,
            )
        )

        respuesta_ok = Mock(spec=requests.Response)
        respuesta_ok.status_code = 200
        respuesta_ok.raise_for_status.return_value = None
        respuesta_ok.json.return_value = {"resultado": "OK"}

        peticion.side_effect = [respuesta_error, respuesta_ok]

        resultado = enviar_peticion(
            "https://ejemplo.invalid",
            {"x-goog-api-key": "clave_simulada"},
            {"contents": []},
        )

        self.assertEqual(resultado, {"resultado": "OK"})
        self.assertEqual(peticion.call_count, 2)
        espera.assert_called_once_with(2)

    @patch("src.consumir_gemini.time.sleep")
    @patch("src.consumir_gemini.requests.post")
    def test_timeout_reintenta(self, peticion, espera):
        """Comprueba la recuperación después de un timeout.

        Simula un tiempo de espera agotado en el primer intento
        y una respuesta exitosa en el segundo. Verifica que
        el cliente aplique la pausa correspondiente.
        """

        respuesta_ok = Mock(spec=requests.Response)
        respuesta_ok.status_code = 200
        respuesta_ok.raise_for_status.return_value = None
        respuesta_ok.json.return_value = {"resultado": "OK"}

        peticion.side_effect = [
            requests.exceptions.Timeout("Tiempo agotado"),
            respuesta_ok,
        ]

        resultado = enviar_peticion(
            "https://ejemplo.invalid",
            {"x-goog-api-key": "clave_simulada"},
            {"contents": []},
        )

        self.assertEqual(resultado, {"resultado": "OK"})
        self.assertEqual(peticion.call_count, 2)
        espera.assert_called_once_with(2)

    @patch("src.consumir_gemini.time.sleep")
    @patch("src.consumir_gemini.requests.post")
    def test_retry_after_respeta_espera(self, peticion, espera):
        """Comprueba que Retry-After prevalezca sobre el backoff.

        Simula una respuesta HTTP 429 con Retry-After de 10 segundos.
        Verifica que el cliente utilice ese valor en lugar de
        la pausa exponencial inicial de 2 segundos.
        """

        respuesta_error = Mock(spec=requests.Response)
        respuesta_error.status_code = 429
        respuesta_error.headers = {"Retry-After": "10"}
        respuesta_error.raise_for_status.side_effect = (
            requests.HTTPError(
                "429 Too Many Requests",
                response=respuesta_error,
            )
        )

        respuesta_ok = Mock(spec=requests.Response)
        respuesta_ok.status_code = 200
        respuesta_ok.raise_for_status.return_value = None
        respuesta_ok.json.return_value = {"resultado": "OK"}

        peticion.side_effect = [respuesta_error, respuesta_ok]

        resultado = enviar_peticion(
            "https://ejemplo.invalid",
            {"x-goog-api-key": "clave_simulada"},
            {"contents": []},
        )

        self.assertEqual(resultado, {"resultado": "OK"})
        self.assertEqual(peticion.call_count, 2)
        espera.assert_called_once_with(10.0)

    @patch("src.consumir_gemini.time.sleep")
    @patch("src.consumir_gemini.requests.post")
    def test_error_503_agota_reintentos(self, peticion, espera):
        """Comprueba el límite de reintentos ante errores HTTP 503.

        Simula tres respuestas consecutivas de indisponibilidad.
        Verifica que el cliente finalice con RuntimeError después
        de tres intentos y dos pausas simuladas.
        """

        respuesta = Mock(spec=requests.Response)
        respuesta.status_code = 503
        respuesta.headers = {}
        respuesta.text = "Servicio temporalmente no disponible"
        respuesta.raise_for_status.side_effect = (
            requests.HTTPError(
                "503 Service Unavailable",
                response=respuesta,
            )
        )

        peticion.return_value = respuesta

        with self.assertRaisesRegex(
            RuntimeError,
            "HTTP 503",
        ):
            enviar_peticion(
                "https://ejemplo.invalid",
                {"x-goog-api-key": "clave_simulada"},
                {"contents": []},
            )

        self.assertEqual(peticion.call_count, 3)
        self.assertEqual(
            [llamada.args[0] for llamada in espera.call_args_list],
            [2, 4],
        )

    @patch("src.consumir_gemini.time.sleep")
    @patch("src.consumir_gemini.requests.post")
    def test_error_500_reintenta(self, peticion, espera):
        """Verifica que HTTP 500 permita recuperar una solicitud.

        Reutiliza el escenario de un error temporal seguido
        de una respuesta HTTP 200.
        """
        self._verificar_reintento_http(500, peticion, espera)

    @patch("src.consumir_gemini.time.sleep")
    @patch("src.consumir_gemini.requests.post")
    def test_error_502_reintenta(self, peticion, espera):
        """Verifica que HTTP 502 permita recuperar una solicitud.

        Reutiliza el escenario de un error temporal seguido
        de una respuesta HTTP 200.
        """
        self._verificar_reintento_http(502, peticion, espera)

    def _verificar_reintento_http(self, codigo, peticion, espera):
        """Valida un reintento exitoso después de un error HTTP.

        Args:
            codigo: Código HTTP temporal que se simulará.
            peticion: Mock de requests.post.
            espera: Mock de time.sleep.

        Comprueba que el cliente realice dos intentos,
        devuelva la respuesta exitosa y aplique una pausa
        simulada de 2 segundos.
        """

        # Simulamos un error temporal del proveedor.
        respuesta_error = Mock(spec=requests.Response)
        respuesta_error.status_code = codigo
        respuesta_error.headers = {}
        respuesta_error.raise_for_status.side_effect = requests.HTTPError(
            f"{codigo} Error temporal",
            response=respuesta_error,
        )

        # Simulamos la recuperación del servicio.
        respuesta_ok = Mock(spec=requests.Response)
        respuesta_ok.status_code = 200
        respuesta_ok.raise_for_status.return_value = None
        respuesta_ok.json.return_value = {"resultado": "OK"}

        peticion.side_effect = [respuesta_error, respuesta_ok]

        resultado = enviar_peticion(
            "https://ejemplo.invalid",
            {"x-goog-api-key": "clave_simulada"},
            {"contents": []},
        )

        self.assertEqual(resultado, {"resultado": "OK"})
        self.assertEqual(peticion.call_count, 2)
        espera.assert_called_once_with(2)


if __name__ == "__main__":
    unittest.main()
