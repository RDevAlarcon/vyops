
"""Pruebas unitarias del cliente modular de Gemini para VyOps.

Bloque 12 — SkillNest.

Verifica que la interfaz pública consultar_modelo() coordine
correctamente las funciones de construcción, envío y extracción
de respuestas.

También comprueba la integración de consultar_modelo_con_costos()
con el registro de costos de sesión.

Las pruebas cubren siete escenarios:

    1. Consulta exitosa mediante el cliente modular.
    2. Propagación de errores durante el envío.
    3. Registro del costo de una consulta exitosa.
    4. Ausencia de registro cuando falla el envío.
    5. Acumulación de costos de dos consultas.
    6. Ausencia de registro ante errores de extracción.
    7. Ausencia de registro ante errores de cálculo.

Utiliza mocks para simular las operaciones del cliente sin
realizar solicitudes reales a la API de Gemini.

Las pruebas verifican que cada operación se ejecute
según lo esperado y que los errores no produzcan
registros de costos incompletos.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Framework de pruebas unitarias de Python.
import unittest

# Permite sustituir temporalmente las funciones
# internas del cliente modular.
from unittest.mock import patch

# Interfaz pública utilizada para consultar Gemini.
from src.cliente_api import consultar_modelo

# Registro de costos asociado a una sesión de consultas.
from src.registro_costos import RegistroCostosSesion


# ============================================================
# 2. PRUEBAS DEL CLIENTE MODULAR
# ============================================================

class TestClienteModular(unittest.TestCase):
    """Valida la integración y propagación de errores del cliente.

    Comprueba la coordinación de las funciones internas
    de src.cliente_api y su integración con el registro
    de costos de sesión.

    Las funciones externas se sustituyen mediante patch
    para controlar las respuestas y los errores simulados.
    """

    # --------------------------------------------------------
    # 2.1. CONSULTA EXITOSA
    # --------------------------------------------------------

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

        Args:
            armar:
                Mock de la función que construye la solicitud.
            enviar:
                Mock de la función que envía la petición.
            extraer:
                Mock de la función que extrae el texto.

        Se comprueban los argumentos recibidos por cada etapa
        para verificar la transferencia de datos entre funciones.
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

        # Ejecutamos la interfaz pública del cliente.
        resultado = consultar_modelo(
            "¿Cuál es la capital de Chile?"
        )

        # Verificamos el resultado y los argumentos de cada etapa.
        self.assertEqual(resultado, "Santiago")

        # La construcción debe recibir la consulta original
        # y el segundo argumento con valor None.
        armar.assert_called_once_with(
            "¿Cuál es la capital de Chile?",
            None,
        )

        # El envío debe utilizar exactamente los datos
        # devueltos por la función de construcción.
        enviar.assert_called_once_with(
            "https://ejemplo.invalid",
            {"x-goog-api-key": "clave_simulada"},
            {"contents": []},
        )

        # La extracción debe recibir la respuesta simulada.
        extraer.assert_called_once_with(
            {"candidates": []}
        )

    # --------------------------------------------------------
    # 2.2. PROPAGACIÓN DE ERRORES DEL ENVÍO
    # --------------------------------------------------------

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

        Args:
            armar:
                Mock de la construcción de la solicitud.
            enviar:
                Mock configurado para generar RuntimeError.
            extraer:
                Mock utilizado para verificar que no se
                procese una respuesta después del fallo.
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

    # --------------------------------------------------------
    # 2.3. REGISTRO DEL COSTO DE UNA CONSULTA
    # --------------------------------------------------------

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
        """Comprueba que una consulta registre su costo una sola vez.

        Simula una consulta exitosa con metadatos de uso
        y un costo calculado de 0.000155.

        Verificaciones:
            - Se devuelve el texto esperado.
            - Se registra una única operación.
            - El total coincide con el costo registrado.
            - El cálculo y el envío se realizan una vez.

        Args:
            armar:
                Mock de construcción de la solicitud.
            enviar:
                Mock de envío de la petición.
            extraer:
                Mock de extracción del texto.
            calcular:
                Mock de cálculo del costo.
        """

        # Creamos un registro independiente para esta sesión.
        registro = RegistroCostosSesion()

        # Simulamos la construcción de la solicitud.
        armar.return_value = (
            "https://ejemplo.invalid",
            {"x-goog-api-key": "clave_simulada"},
            {"contents": []},
        )

        # Simulamos una respuesta exitosa de Gemini.
        # Los metadatos representan el consumo de tokens.
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

    # --------------------------------------------------------
    # 2.4. CONSULTA FALLIDA SIN REGISTRO DE COSTO
    # --------------------------------------------------------

    @patch("src.cliente_api.enviar_peticion")
    @patch("src.cliente_api.armar_peticion")
    def test_consulta_fallida_no_registra_costo(self, armar, enviar):
        """Comprueba que una consulta fallida no genere cargos.

        Simula un error HTTP 503 durante el envío.

        Verificaciones:
            - Se propaga RuntimeError.
            - No se agregan operaciones al registro.
            - El costo acumulado permanece en cero.
            - El envío se invoca una sola vez.

        Args:
            armar:
                Mock de construcción de la solicitud.
            enviar:
                Mock configurado para simular el error.
        """

        # Importamos la interfaz que registra costos.
        from src.cliente_api import consultar_modelo_con_costos

        # Utilizamos un registro vacío para esta prueba.
        registro = RegistroCostosSesion()

        # Preparamos una solicitud simulada.
        armar.return_value = (
            "https://ejemplo.invalid",
            {"x-goog-api-key": "clave_simulada"},
            {"contents": []},
        )

        # Simulamos un error del servicio.
        enviar.side_effect = RuntimeError("Error HTTP 503")

        # La excepción debe propagarse al llamador.
        with self.assertRaises(RuntimeError):
            consultar_modelo_con_costos(
                "Consulta de prueba",
                registro,
            )

        # El fallo no debe producir un registro de costo.
        self.assertEqual(registro.obtener_operaciones(), [])
        self.assertEqual(registro.obtener_total(), 0.0)
        enviar.assert_called_once()

    # --------------------------------------------------------
    # 2.5. ACUMULACIÓN DE COSTOS DE DOS CONSULTAS
    # --------------------------------------------------------

    @patch("src.cliente_api.calcular_costo")
    @patch("src.cliente_api.extraer_texto")
    @patch("src.cliente_api.enviar_peticion")
    @patch("src.cliente_api.armar_peticion")
    def test_acumula_costos_de_dos_consultas(
        self, armar, enviar, extraer, calcular,
    ):
        """Comprueba el costo acumulado de dos consultas exitosas.

        Simula dos operaciones consecutivas que utilizan
        el mismo registro de sesión.

        Costos simulados:
            - Primera consulta: 0.00015.
            - Segunda consulta: 0.00025.
            - Total esperado: 0.00040.

        Verificaciones:
            - Se conservan ambas respuestas.
            - Cada costo se registra por separado.
            - El total corresponde a la suma.
            - El envío y el cálculo se ejecutan dos veces.

        Args:
            armar:
                Mock de construcción de solicitudes.
            enviar:
                Mock de envío de peticiones.
            extraer:
                Mock que devuelve respuestas consecutivas.
            calcular:
                Mock que devuelve costos consecutivos.
        """

        # Importamos la función de consulta con costos.
        from src.cliente_api import consultar_modelo_con_costos

        # Compartimos un registro entre ambas consultas.
        registro = RegistroCostosSesion()

        # Configuramos las respuestas de las etapas simuladas.
        armar.return_value = (
            "https://ejemplo.invalid",
            {"x-goog-api-key": "clave_simulada"},
            {"contents": []},
        )
        enviar.return_value = {"usageMetadata": {}}
        extraer.side_effect = ["Primera respuesta", "Segunda respuesta"]
        calcular.side_effect = [0.00015, 0.00025]

        # Ejecutamos dos consultas utilizando el mismo registro.
        primera = consultar_modelo_con_costos("Primera consulta", registro)
        segunda = consultar_modelo_con_costos("Segunda consulta", registro)

        # Verificamos las respuestas y los costos individuales.
        self.assertEqual(primera, "Primera respuesta")
        self.assertEqual(segunda, "Segunda respuesta")
        self.assertEqual(
            registro.obtener_operaciones(),
            [0.00015, 0.00025],
        )

        # Comprueba el total acumulado de la sesión.
        self.assertAlmostEqual(registro.obtener_total(), 0.00040)

        # Cada consulta debe ejecutar su envío
        # y su cálculo de costo correspondiente.
        self.assertEqual(enviar.call_count, 2)
        self.assertEqual(calcular.call_count, 2)

    # --------------------------------------------------------
    # 2.6. ERROR DE EXTRACCIÓN SIN REGISTRO DE COSTO
    # --------------------------------------------------------

    @patch("src.cliente_api.calcular_costo")
    @patch("src.cliente_api.extraer_texto")
    @patch("src.cliente_api.enviar_peticion")
    @patch("src.cliente_api.armar_peticion")
    def test_error_extraccion_no_registra_costo(
        self, armar, enviar, extraer, calcular,
    ):
        """Comprueba que una respuesta inválida no registre costos.

        Simula un envío exitoso seguido de un error
        durante la extracción del texto.

        Verificaciones:
            - Se propaga ValueError.
            - No se registran operaciones.
            - El total permanece en cero.
            - No se invoca el cálculo del costo.
            - El envío se realiza una sola vez.

        Args:
            armar:
                Mock de construcción de la solicitud.
            enviar:
                Mock que devuelve una respuesta simulada.
            extraer:
                Mock configurado para generar ValueError.
            calcular:
                Mock utilizado para comprobar que
                no se calcule el costo tras el fallo.
        """

        # Importamos la función de consulta con costos.
        from src.cliente_api import consultar_modelo_con_costos

        # Creamos un registro independiente.
        registro = RegistroCostosSesion()

        # Simulamos la solicitud y la respuesta recibida.
        armar.return_value = (
            "https://ejemplo.invalid",
            {"x-goog-api-key": "clave_simulada"},
            {"contents": []},
        )
        enviar.return_value = {"candidates": []}

        # La extracción falla porque la respuesta no contiene texto.
        extraer.side_effect = ValueError("Respuesta sin texto")

        # Comprueba la propagación del error de extracción.
        with self.assertRaises(ValueError):
            consultar_modelo_con_costos(
                "Consulta de prueba",
                registro,
            )

        # No debe registrarse un costo después del fallo.
        self.assertEqual(registro.obtener_operaciones(), [])
        self.assertEqual(registro.obtener_total(), 0.0)

        # El cálculo no debe ejecutarse si falla la extracción.
        calcular.assert_not_called()
        enviar.assert_called_once()

    # --------------------------------------------------------
    # 2.7. ERROR DE CÁLCULO SIN REGISTRO DE COSTO
    # --------------------------------------------------------

    @patch("src.cliente_api.calcular_costo")
    @patch("src.cliente_api.extraer_texto")
    @patch("src.cliente_api.enviar_peticion")
    @patch("src.cliente_api.armar_peticion")
    def test_error_calculo_no_registra_costo(
        self, armar, enviar, extraer, calcular,
    ):
        """Comprueba que un error de cálculo no altere el registro.

        Simula una respuesta válida cuyo cálculo
        de costo genera un ValueError.

        Verificaciones:
            - Se propaga ValueError.
            - No se registran operaciones.
            - El costo total permanece en cero.
            - El cálculo se invoca una sola vez.
            - El envío se realiza una sola vez.

        Args:
            armar:
                Mock de construcción de la solicitud.
            enviar:
                Mock que devuelve los datos simulados.
            extraer:
                Mock que devuelve una respuesta válida.
            calcular:
                Mock configurado para generar ValueError.
        """

        # Importamos la función de consulta con costos.
        from src.cliente_api import consultar_modelo_con_costos

        # Creamos un registro vacío para verificar
        # que permanezca sin cambios después del error.
        registro = RegistroCostosSesion()

        # Simulamos las etapas exitosas de la consulta.
        armar.return_value = (
            "https://ejemplo.invalid",
            {"x-goog-api-key": "clave_simulada"},
            {"contents": []},
        )
        enviar.return_value = {"usageMetadata": {}}
        extraer.return_value = "Respuesta de prueba"

        # Simulamos un error al interpretar el uso de tokens.
        calcular.side_effect = ValueError("Uso de tokens inválido")

        # El error de cálculo debe propagarse.
        with self.assertRaises(ValueError):
            consultar_modelo_con_costos(
                "Consulta de prueba",
                registro,
            )

        # No debe agregarse un costo incompleto al registro.
        self.assertEqual(registro.obtener_operaciones(), [])
        self.assertEqual(registro.obtener_total(), 0.0)

        # El cálculo y el envío deben ejecutarse una sola vez.
        calcular.assert_called_once()
        enviar.assert_called_once()


# ============================================================
# 3. EJECUCIÓN DIRECTA DEL MÓDULO
# ============================================================

# Permite ejecutar estas pruebas mediante unittest
# cuando el archivo se inicia directamente.
if __name__ == "__main__":
    unittest.main()
