
"""Pruebas unitarias del cliente HTTP de Gemini para VyOps.

Bloque 12 — SkillNest.

Verifica el manejo de errores de autenticación, respuestas HTTP
temporales, tiempos de espera y políticas de reintentos.

Los escenarios cubren:

    - HTTP 400: solicitud incorrecta sin reintentos.
    - HTTP 401: autenticación rechazada sin reintentos.
    - HTTP 403: acceso denegado sin reintentos.
    - HTTP 429: recuperación ante límite de solicitudes.
    - HTTP 500: recuperación ante error interno.
    - HTTP 502: recuperación ante error de pasarela.
    - HTTP 503: recuperación o agotamiento de intentos.
    - Timeout: recuperación después de una espera agotada.
    - Retry-After: aplicación de la espera indicada.
    - Jitter: variación controlada de los intervalos.

La política de reintentos evaluada utiliza esperas
exponenciales con una variación aleatoria de hasta el 10 %.

Las solicitudes HTTP y las pausas se simulan mediante mocks.
No se realizan llamadas reales a Gemini ni se utilizan API keys.

Las pruebas verifican el comportamiento de enviar_peticion()
ante respuestas y excepciones controladas.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Framework de pruebas unitarias.
import unittest

# Herramientas para simular respuestas HTTP
# y sustituir temporalmente funciones externas.
from unittest.mock import Mock, patch

# Biblioteca HTTP utilizada por el cliente Gemini.
import requests

# Función responsable de enviar las peticiones
# y gestionar los errores y reintentos.
from src.consumir_gemini import enviar_peticion


# ============================================================
# 2. PRUEBAS DEL CLIENTE HTTP
# ============================================================

class TestClienteGemini(unittest.TestCase):
    """Valida los errores HTTP y los reintentos del cliente.

    Comprueba que el cliente distinga entre errores
    que deben detener la operación y errores temporales
    que permiten realizar nuevos intentos.

    Las respuestas de requests.post se sustituyen
    mediante mocks para evitar conexiones externas.

    Cuando corresponde, también se sustituye time.sleep
    para inspeccionar los intervalos sin realizar esperas.
    """

    # --------------------------------------------------------
    # 2.1. HTTP 400: SOLICITUD INCORRECTA
    # --------------------------------------------------------

    @patch("src.consumir_gemini.requests.post")
    def test_error_400_no_reintenta(self, peticion):
        """Comprueba que HTTP 400 se informe sin reintentos.

        Simula una solicitud rechazada por Gemini, que puede
        deberse a una API key inválida o a parámetros incorrectos.

        Verifica que el cliente genere un RuntimeError con un
        mensaje orientativo y realice un único intento HTTP.

        Args:
            peticion:
                Mock que sustituye requests.post.
        """

        # Simulamos una respuesta HTTP 400 del proveedor.
        respuesta = Mock(spec=requests.Response)
        respuesta.status_code = 400
        respuesta.raise_for_status.side_effect = requests.HTTPError(
            "400 Bad Request",
            response=respuesta,
        )

        # Configuramos la respuesta devuelta por requests.post.
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

    # --------------------------------------------------------
    # 2.2. HTTP 401: AUTENTICACIÓN RECHAZADA
    # --------------------------------------------------------

    @patch("src.consumir_gemini.requests.post")
    def test_error_401_no_reintenta(self, peticion):
        """Comprueba que HTTP 401 detenga la solicitud sin reintentos.

        Simula un rechazo de autenticación y verifica que el cliente
        informe el error y realice un único intento de conexión.

        Args:
            peticion:
                Mock que sustituye la solicitud HTTP.
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

    # --------------------------------------------------------
    # 2.3. HTTP 403: ACCESO DENEGADO
    # --------------------------------------------------------

    @patch("src.consumir_gemini.requests.post")
    def test_error_403_no_reintenta(self, peticion):
        """Comprueba que HTTP 403 rechace el acceso sin reintentos.

        Simula una respuesta HTTP 403 Forbidden.

        Verificaciones:
            - Se propaga un RuntimeError orientativo.
            - La solicitud HTTP se ejecuta una sola vez.

        Args:
            peticion:
                Mock utilizado para simular requests.post.
        """

        # Construye una respuesta HTTP de acceso denegado.
        respuesta = Mock(spec=requests.Response)
        respuesta.status_code = 403
        respuesta.raise_for_status.side_effect = requests.HTTPError(
            "403 Forbidden",
            response=respuesta,
        )

        peticion.return_value = respuesta

        # Comprueba que se informe el rechazo de acceso.
        with self.assertRaisesRegex(
            RuntimeError,
            "La API rechazó la autenticación o el acceso",
        ):
            enviar_peticion(
                "https://ejemplo.invalid",
                {"x-goog-api-key": "clave_simulada"},
                {"contents": []},
            )

        # HTTP 403 no debe generar reintentos.
        peticion.assert_called_once()

    # --------------------------------------------------------
    # 2.4. HTTP 429: RECUPERACIÓN CON BACKOFF EXPONENCIAL
    # --------------------------------------------------------

    @patch("src.consumir_gemini.time.sleep")
    @patch("src.consumir_gemini.requests.post")
    def test_error_429_reintenta(self, peticion, espera):
        """Comprueba los reintentos exponenciales ante HTTP 429.

        Simula dos respuestas de límite de solicitudes y una
        respuesta exitosa. Verifica tres intentos y pausas
        de 2 y 4 segundos, sin realizar esperas reales.

        El jitter puede incrementar cada pausa hasta un 10 %.

        Args:
            peticion:
                Mock de requests.post.
            espera:
                Mock de time.sleep utilizado para registrar
                las duraciones de espera.
        """

        # Almacena las respuestas HTTP simuladas.
        respuestas = []

        # Dos errores HTTP 429 seguidos de una respuesta exitosa.
        for codigo in (429, 429, 200):
            respuesta = Mock(spec=requests.Response)
            respuesta.status_code = codigo
            respuesta.headers = {}

            if codigo == 429:
                # Los errores 429 generan una excepción HTTP.
                respuesta.raise_for_status.side_effect = (
                    requests.HTTPError(
                        "429 Too Many Requests",
                        response=respuesta,
                    )
                )
            else:
                # La respuesta final permite recuperar el resultado.
                respuesta.raise_for_status.return_value = None
                respuesta.json.return_value = {"resultado": "OK"}

            respuestas.append(respuesta)

        # Configura la secuencia de respuestas del proveedor.
        peticion.side_effect = respuestas

        # Ejecuta el envío con dos fallos temporales.
        resultado = enviar_peticion(
            "https://ejemplo.invalid",
            {"x-goog-api-key": "clave_simulada"},
            {"contents": []},
        )

        # Verificamos la recuperación y el backoff exponencial.
        self.assertEqual(resultado, {"resultado": "OK"})
        self.assertEqual(peticion.call_count, 3)

        # Comprobamos el backoff exponencial con jitter de hasta el 10 %.
        pausas = [llamada.args[0] for llamada in espera.call_args_list]

        # Deben existir dos pausas antes del tercer intento.
        self.assertEqual(len(pausas), 2)

        # Primera pausa: entre 2 y 2,2 segundos.
        self.assertGreaterEqual(pausas[0], 2)
        self.assertLessEqual(pausas[0], 2.2)

        # Segunda pausa: entre 4 y 4,4 segundos.
        self.assertGreaterEqual(pausas[1], 4)
        self.assertLessEqual(pausas[1], 4.4)

    # --------------------------------------------------------
    # 2.5. HTTP 503: RECUPERACIÓN DEL SERVICIO
    # --------------------------------------------------------

    @patch("src.consumir_gemini.time.sleep")
    @patch("src.consumir_gemini.requests.post")
    def test_error_503_reintenta(self, peticion, espera):
        """Comprueba la recuperación tras un error HTTP 503.

        Simula una indisponibilidad temporal del servicio seguida
        de una respuesta exitosa. Verifica dos intentos y una
        pausa simulada de 2 segundos.

        La pausa puede incluir jitter de hasta el 10 %.

        Args:
            peticion:
                Mock de requests.post.
            espera:
                Mock de time.sleep.
        """

        # Simula una respuesta de servicio no disponible.
        respuesta_error = Mock(spec=requests.Response)
        respuesta_error.status_code = 503
        respuesta_error.headers = {}
        respuesta_error.raise_for_status.side_effect = (
            requests.HTTPError(
                "503 Service Unavailable",
                response=respuesta_error,
            )
        )

        # Simula una respuesta exitosa posterior.
        respuesta_ok = Mock(spec=requests.Response)
        respuesta_ok.status_code = 200
        respuesta_ok.raise_for_status.return_value = None
        respuesta_ok.json.return_value = {"resultado": "OK"}

        # Configura un error seguido de recuperación.
        peticion.side_effect = [respuesta_error, respuesta_ok]

        resultado = enviar_peticion(
            "https://ejemplo.invalid",
            {"x-goog-api-key": "clave_simulada"},
            {"contents": []},
        )

        # Comprueba el resultado y los dos intentos.
        self.assertEqual(resultado, {"resultado": "OK"})
        self.assertEqual(peticion.call_count, 2)

        # Verificamos una única pausa con jitter de hasta el 10 %.
        espera.assert_called_once()
        duracion = espera.call_args.args[0]
        self.assertGreaterEqual(duracion, 2)
        self.assertLessEqual(duracion, 2.2)

    # --------------------------------------------------------
    # 2.6. RECUPERACIÓN DESPUÉS DE UN TIMEOUT
    # --------------------------------------------------------

    @patch("src.consumir_gemini.time.sleep")
    @patch("src.consumir_gemini.requests.post")
    def test_timeout_reintenta(self, peticion, espera):
        """Comprueba la recuperación después de un timeout.

        Simula un tiempo de espera agotado en el primer intento
        y una respuesta exitosa en el segundo. Verifica que
        el cliente aplique la pausa correspondiente.

        Args:
            peticion:
                Mock que simula el timeout y la respuesta exitosa.
            espera:
                Mock que registra la duración de la pausa.
        """

        # Prepara una respuesta HTTP exitosa.
        respuesta_ok = Mock(spec=requests.Response)
        respuesta_ok.status_code = 200
        respuesta_ok.raise_for_status.return_value = None
        respuesta_ok.json.return_value = {"resultado": "OK"}

        # La primera solicitud agota el tiempo de espera.
        # La segunda devuelve una respuesta válida.
        peticion.side_effect = [
            requests.exceptions.Timeout("Tiempo agotado"),
            respuesta_ok,
        ]

        resultado = enviar_peticion(
            "https://ejemplo.invalid",
            {"x-goog-api-key": "clave_simulada"},
            {"contents": []},
        )

        # Comprueba la recuperación en el segundo intento.
        self.assertEqual(resultado, {"resultado": "OK"})
        self.assertEqual(peticion.call_count, 2)

        # Verificamos una única pausa con jitter de hasta el 10 %.
        espera.assert_called_once()
        duracion = espera.call_args.args[0]
        self.assertGreaterEqual(duracion, 2)
        self.assertLessEqual(duracion, 2.2)

    # --------------------------------------------------------
    # 2.7. PRIORIDAD DEL ENCABEZADO RETRY-AFTER
    # --------------------------------------------------------

    @patch("src.consumir_gemini.time.sleep")
    @patch("src.consumir_gemini.requests.post")
    def test_retry_after_respeta_espera(self, peticion, espera):
        """Comprueba que Retry-After prevalezca sobre el backoff.

        Simula una respuesta HTTP 429 con Retry-After de 10 segundos.
        Verifica que el cliente utilice ese valor en lugar de
        la pausa exponencial inicial de 2 segundos.

        El jitter puede incrementar la espera hasta 11 segundos.

        Args:
            peticion:
                Mock que simula las respuestas HTTP.
            espera:
                Mock utilizado para inspeccionar la pausa.
        """

        # Simula un límite de solicitudes que solicita
        # esperar 10 segundos antes de reintentar.
        respuesta_error = Mock(spec=requests.Response)
        respuesta_error.status_code = 429
        respuesta_error.headers = {"Retry-After": "10"}
        respuesta_error.raise_for_status.side_effect = (
            requests.HTTPError(
                "429 Too Many Requests",
                response=respuesta_error,
            )
        )

        # Simula la recuperación del servicio.
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

        # Comprueba que la solicitud se recupere.
        self.assertEqual(resultado, {"resultado": "OK"})
        self.assertEqual(peticion.call_count, 2)

        # Retry-After establece una espera base de 10 segundos.
        # El jitter puede añadir hasta un 10 % adicional.
        espera.assert_called_once()
        duracion = espera.call_args.args[0]
        self.assertGreaterEqual(duracion, 10)
        self.assertLessEqual(duracion, 11)

    # --------------------------------------------------------
    # 2.8. HTTP 503: AGOTAMIENTO DE REINTENTOS
    # --------------------------------------------------------

    @patch("src.consumir_gemini.time.sleep")
    @patch("src.consumir_gemini.requests.post")
    def test_error_503_agota_reintentos(self, peticion, espera):
        """Comprueba el límite de reintentos ante errores HTTP 503.

        Simula tres respuestas consecutivas de indisponibilidad.
        Verifica que el cliente finalice con RuntimeError después
        de tres intentos y dos pausas simuladas.

        Las pausas esperadas siguen el backoff exponencial
        con jitter de hasta el 10 %.

        Args:
            peticion:
                Mock de requests.post.
            espera:
                Mock de time.sleep.
        """

        # Simula una respuesta persistente de error HTTP 503.
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

        # Todas las solicitudes recibirán el mismo error.
        peticion.return_value = respuesta

        # El cliente debe detenerse al agotar los intentos.
        with self.assertRaisesRegex(
            RuntimeError,
            "HTTP 503",
        ):
            enviar_peticion(
                "https://ejemplo.invalid",
                {"x-goog-api-key": "clave_simulada"},
                {"contents": []},
            )

        # Comprueba el límite de tres intentos.
        self.assertEqual(peticion.call_count, 3)

        # Comprobamos el backoff exponencial con jitter de hasta el 10 %.
        pausas = [llamada.args[0] for llamada in espera.call_args_list]

        self.assertEqual(len(pausas), 2)
        self.assertGreaterEqual(pausas[0], 2)
        self.assertLessEqual(pausas[0], 2.2)
        self.assertGreaterEqual(pausas[1], 4)
        self.assertLessEqual(pausas[1], 4.4)

    # --------------------------------------------------------
    # 2.9. HTTP 500: ERROR INTERNO RECUPERABLE
    # --------------------------------------------------------

    @patch("src.consumir_gemini.time.sleep")
    @patch("src.consumir_gemini.requests.post")
    def test_error_500_reintenta(self, peticion, espera):
        """Verifica que HTTP 500 permita recuperar una solicitud.

        Reutiliza el escenario de un error temporal seguido
        de una respuesta HTTP 200.

        Args:
            peticion:
                Mock de requests.post.
            espera:
                Mock de time.sleep.
        """

        # Ejecuta la validación común con HTTP 500.
        self._verificar_reintento_http(500, peticion, espera)

    # --------------------------------------------------------
    # 2.10. HTTP 502: ERROR DE PASARELA RECUPERABLE
    # --------------------------------------------------------

    @patch("src.consumir_gemini.time.sleep")
    @patch("src.consumir_gemini.requests.post")
    def test_error_502_reintenta(self, peticion, espera):
        """Verifica que HTTP 502 permita recuperar una solicitud.

        Reutiliza el escenario de un error temporal seguido
        de una respuesta HTTP 200.

        Args:
            peticion:
                Mock de requests.post.
            espera:
                Mock de time.sleep.
        """

        # Ejecuta la validación común con HTTP 502.
        self._verificar_reintento_http(502, peticion, espera)

    # --------------------------------------------------------
    # 2.11. VALIDACIÓN COMPARTIDA DE ERRORES TEMPORALES
    # --------------------------------------------------------

    def _verificar_reintento_http(self, codigo, peticion, espera):
        """Valida un reintento exitoso después de un error HTTP.

        Args:
            codigo: Código HTTP temporal que se simulará.
            peticion: Mock de requests.post.
            espera: Mock de time.sleep.

        Comprueba que el cliente realice dos intentos,
        devuelva la respuesta exitosa y aplique una pausa
        simulada de 2 segundos.

        El intervalo puede aumentar hasta un 10 %
        debido al jitter.
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

        # Configura el error inicial y la recuperación posterior.
        peticion.side_effect = [respuesta_error, respuesta_ok]

        resultado = enviar_peticion(
            "https://ejemplo.invalid",
            {"x-goog-api-key": "clave_simulada"},
            {"contents": []},
        )

        # Comprueba que se recupere el resultado esperado.
        self.assertEqual(resultado, {"resultado": "OK"})
        self.assertEqual(peticion.call_count, 2)

        # Validamos el backoff con jitter de hasta el 10 %.
        espera.assert_called_once()
        duracion = espera.call_args.args[0]
        self.assertGreaterEqual(duracion, 2)
        self.assertLessEqual(duracion, 2.2)

    # --------------------------------------------------------
    # 2.12. HTTP 429: VERIFICACIÓN DEL JITTER
    # --------------------------------------------------------

    @patch("src.consumir_gemini.time.sleep")
    @patch("src.consumir_gemini.random.uniform")
    @patch("src.consumir_gemini.requests.post")
    def test_error_429_aplica_jitter(self, peticion, aleatorio, espera):
        """Verifica que el backoff incorpore una variación controlada.

        Simula un error HTTP 429 seguido de una respuesta exitosa.
        Comprueba que se agregue jitter sin realizar pausas reales.

        La variación simulada es de 0,15 segundos,
        que se suma a la espera base de 2 segundos.

        Args:
            peticion:
                Mock de requests.post.
            aleatorio:
                Mock de random.uniform que devuelve 0,15.
            espera:
                Mock de time.sleep.
        """

        # Simula una respuesta HTTP 429.
        respuesta_error = Mock(spec=requests.Response)
        respuesta_error.status_code = 429
        respuesta_error.headers = {}
        respuesta_error.raise_for_status.side_effect = requests.HTTPError(
            "429 Too Many Requests",
            response=respuesta_error,
        )

        # Simula una respuesta HTTP 200 posterior.
        respuesta_ok = Mock(spec=requests.Response)
        respuesta_ok.status_code = 200
        respuesta_ok.raise_for_status.return_value = None
        respuesta_ok.json.return_value = {"resultado": "OK"}

        peticion.side_effect = [respuesta_error, respuesta_ok]

        # Simulamos un jitter de 0,15 segundos.
        aleatorio.return_value = 0.15

        resultado = enviar_peticion(
            "https://ejemplo.invalid",
            {"x-goog-api-key": "clave_simulada"},
            {"contents": []},
        )

        # Comprueba la recuperación en el segundo intento.
        self.assertEqual(resultado, {"resultado": "OK"})
        self.assertEqual(peticion.call_count, 2)

        # La variación debe solicitarse entre 0 y 0,2 segundos.
        aleatorio.assert_called_once_with(0, 0.2)

        # La espera final debe incorporar el jitter simulado.
        espera.assert_called_once_with(2.15)


# ============================================================
# 3. EJECUCIÓN DIRECTA DEL MÓDULO
# ============================================================

# Permite ejecutar las pruebas con unittest
# cuando este archivo se inicia directamente.
if __name__ == "__main__":
    unittest.main()
