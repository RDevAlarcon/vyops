
"""Pruebas unitarias del adaptador de embeddings con reintentos.

Este módulo verifica el comportamiento de
EmbeddingsConReintentos, definido en
src.embeddings_con_reintentos.

El adaptador utiliza un proveedor de embeddings
y gestiona determinados errores mediante reintentos.

Las pruebas comprueban cuatro escenarios:

    1. Generación exitosa de embeddings sin reintentos.
    2. Recuperación después de un error HTTP 429.
    3. Agotamiento de intentos ante errores HTTP 503.
    4. Rechazo inmediato de errores HTTP 401.

Se utiliza Mock para simular el proveedor de embeddings
y patch para sustituir temporalmente time.sleep.

De esta manera, las pruebas pueden verificar los
intervalos de espera sin introducir demoras reales.

También se construyen excepciones simuladas que
conservan la causa HTTP original, permitiendo
comprobar cómo el adaptador interpreta los errores
recibidos desde LangChain y Google GenAI.

Estas pruebas no realizan solicitudes reales
a Gemini ni generan embeddings mediante la API.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Framework de pruebas unitarias de Python.
import unittest

# Mock permite simular el proveedor de embeddings.
# patch permite sustituir temporalmente funciones.
from unittest.mock import Mock, patch

# Excepciones HTTP utilizadas por Google GenAI.
from google.genai.errors import ClientError, ServerError

# Excepción de LangChain utilizada para representar
# errores del proveedor Google Generative AI.
from langchain_google_genai._common import GoogleGenerativeAIError

# Adaptador que implementa la política de reintentos
# para la generación de embeddings.
from src.embeddings_con_reintentos import EmbeddingsConReintentos


# ============================================================
# 2. CONSTRUCCIÓN DE ERRORES SIMULADOS
# ============================================================

def error_gemini(codigo):
    """Construye un error de LangChain con su causa HTTP original.

    Simula una excepción GoogleGenerativeAIError
    asociada a un código de respuesta HTTP.

    Para códigos inferiores a 500 utiliza ClientError.
    Para códigos iguales o superiores a 500 utiliza
    ServerError.

    La excepción HTTP se asigna como causa original
    mediante el atributo __cause__.

    Args:
        codigo (int):
            Código HTTP que se desea simular.

    Returns:
        GoogleGenerativeAIError:
            Excepción simulada de LangChain que contiene
            la excepción HTTP original como causa.

    Esta función permite evaluar cómo el adaptador
    identifica errores recuperables y no recuperables.
    """

    # Selecciona el tipo de excepción HTTP
    # según el código proporcionado.
    clase = ClientError if codigo < 500 else ServerError

    # Construye la excepción original del proveedor.
    causa = clase(
        code=codigo,
        response_json={"error": {"message": "Error simulado"}},
    )

    # Construye la excepción que recibiría
    # el adaptador desde LangChain.
    error = GoogleGenerativeAIError("Error simulado")

    # Conserva la excepción HTTP como causa
    # para permitir inspeccionar su código.
    error.__cause__ = causa

    return error


# ============================================================
# 3. PRUEBAS DEL ADAPTADOR DE EMBEDDINGS
# ============================================================

class TestEmbeddingsConReintentos(unittest.TestCase):
    """Agrupa las pruebas de la política de reintentos.

    Los escenarios utilizan un proveedor simulado
    para controlar las respuestas y excepciones.

    Se comprueba tanto el resultado de la operación
    como la cantidad de invocaciones realizadas.

    El método time.sleep se sustituye en cada prueba
    para verificar las esperas sin detener realmente
    la ejecución.
    """

    # --------------------------------------------------------
    # 3.1. ÉXITO EN EL PRIMER INTENTO
    # --------------------------------------------------------

    @patch("src.embeddings_con_reintentos.time.sleep")
    def test_exito_inmediato(self, dormir):
        """Verifica la generación exitosa sin reintentos.

        Configura un proveedor que devuelve correctamente
        un vector de embeddings en su primera invocación.

        Verificaciones:
            - Se devuelve el vector esperado.
            - El proveedor se invoca una sola vez.
            - No se ejecutan esperas.

        Args:
            dormir:
                Mock que sustituye temporalmente
                la función time.sleep del módulo.
        """

        # Simula un proveedor que responde correctamente.
        proveedor = Mock()
        proveedor.embed_documents.return_value = [[0.1, 0.2]]

        # Construye el adaptador con el proveedor simulado.
        adaptador = EmbeddingsConReintentos(proveedor)

        # Comprueba que se devuelva el embedding esperado.
        self.assertEqual(
            adaptador.embed_documents(["documento"]),
            [[0.1, 0.2]],
        )

        # Una respuesta exitosa no debe requerir reintentos.
        self.assertEqual(proveedor.embed_documents.call_count, 1)

        # No deben existir esperas entre intentos.
        dormir.assert_not_called()

    # --------------------------------------------------------
    # 3.2. RECUPERACIÓN ANTE HTTP 429
    # --------------------------------------------------------

    @patch("src.embeddings_con_reintentos.time.sleep")
    def test_429_recuperable(self, dormir):
        """Verifica la recuperación después de un error HTTP 429.

        Simula una primera invocación que genera
        un error HTTP 429 y una segunda invocación
        que devuelve correctamente el embedding.

        Verificaciones:
            - Se obtiene el vector esperado.
            - El proveedor se invoca dos veces.
            - Se realiza una espera simulada de 2 segundos.

        Args:
            dormir:
                Mock utilizado para registrar
                los intervalos de espera.

        Este escenario comprueba que el adaptador
        permita recuperarse de un error 429
        mediante un nuevo intento.
        """

        # Configura un fallo inicial seguido
        # de una respuesta exitosa.
        proveedor = Mock()
        proveedor.embed_documents.side_effect = [
            error_gemini(429),
            [[0.1, 0.2]],
        ]

        # Construye el adaptador con el proveedor simulado.
        adaptador = EmbeddingsConReintentos(proveedor)

        # Comprueba que el segundo intento
        # permita obtener el embedding esperado.
        self.assertEqual(
            adaptador.embed_documents(["documento"]),
            [[0.1, 0.2]],
        )

        # Debe existir una invocación inicial
        # y un reintento posterior.
        self.assertEqual(proveedor.embed_documents.call_count, 2)

        # Comprueba la espera programada
        # antes del segundo intento.
        dormir.assert_called_once_with(2.0)

    # --------------------------------------------------------
    # 3.3. AGOTAMIENTO DE INTENTOS ANTE HTTP 503
    # --------------------------------------------------------

    @patch("src.embeddings_con_reintentos.time.sleep")
    def test_503_agota_intentos(self, dormir):
        """Verifica el agotamiento de intentos ante HTTP 503.

        Configura un proveedor que genera
        permanentemente un error HTTP 503.

        Verificaciones:
            - Se propaga GoogleGenerativeAIError.
            - El proveedor se invoca tres veces.
            - Las esperas simuladas son de 2 y 4 segundos.

        Este escenario comprueba el límite de intentos
        y los intervalos de espera esperados cuando
        el servicio permanece indisponible.

        Args:
            dormir:
                Mock que registra las llamadas
                a time.sleep sin realizar esperas reales.
        """

        # Simula un proveedor que falla
        # en todas las invocaciones.
        proveedor = Mock()
        proveedor.embed_documents.side_effect = error_gemini(503)

        # Construye el adaptador con el proveedor simulado.
        adaptador = EmbeddingsConReintentos(proveedor)

        # La excepción debe propagarse
        # cuando se agotan los intentos.
        with self.assertRaises(GoogleGenerativeAIError):
            adaptador.embed_documents(["documento"])

        # Comprueba el total de tres invocaciones.
        self.assertEqual(proveedor.embed_documents.call_count, 3)

        # Verifica los intervalos de espera registrados
        # antes de los intentos posteriores.
        self.assertEqual(
            [llamada.args[0] for llamada in dormir.call_args_list],
            [2.0, 4.0],
        )

    # --------------------------------------------------------
    # 3.4. ERROR HTTP 401 SIN REINTENTOS
    # --------------------------------------------------------

    @patch("src.embeddings_con_reintentos.time.sleep")
    def test_401_no_reintenta(self, dormir):
        """Verifica que un error HTTP 401 no genere reintentos.

        Simula un proveedor que devuelve un error
        de autenticación HTTP 401.

        Verificaciones:
            - Se propaga GoogleGenerativeAIError.
            - El proveedor se invoca una sola vez.
            - No se realizan esperas.

        Este escenario comprueba que el adaptador
        no repita automáticamente una operación
        ante el error de autenticación evaluado.

        Args:
            dormir:
                Mock que permite comprobar
                que no se invoque time.sleep.
        """

        # Simula un fallo de autenticación.
        proveedor = Mock()
        proveedor.embed_documents.side_effect = error_gemini(401)

        # Construye el adaptador con el proveedor simulado.
        adaptador = EmbeddingsConReintentos(proveedor)

        # Comprueba que el error se propague
        # sin intentar recuperarlo automáticamente.
        with self.assertRaises(GoogleGenerativeAIError):
            adaptador.embed_documents(["documento"])

        # El proveedor debe recibir una sola invocación.
        self.assertEqual(proveedor.embed_documents.call_count, 1)

        # No deben realizarse esperas
        # porque no corresponde reintentar.
        dormir.assert_not_called()


# ============================================================
# 4. EJECUCIÓN DIRECTA DEL MÓDULO
# ============================================================

# Permite ejecutar las pruebas mediante unittest
# cuando el archivo se inicia directamente.
if __name__ == "__main__":
    unittest.main()
