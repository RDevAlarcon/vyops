
"""Adaptador de embeddings con reintentos controlados para Gemini.

Este módulo implementa un adaptador compatible con la interfaz
Embeddings de LangChain para gestionar determinados errores
temporales durante la generación de embeddings.

Su objetivo es mejorar la tolerancia a fallos transitorios
del proveedor antes de continuar con operaciones que
dependen de los vectores, como la indexación en ChromaDB.

Características principales:

    1. Reutiliza una implementación existente de Embeddings.
    2. Permite configurar el número máximo de intentos.
    3. Aplica una espera exponencial entre reintentos.
    4. Identifica códigos HTTP recuperables.
    5. Examina excepciones encadenadas mediante __cause__.
    6. Propaga errores no recuperables.
    7. Mantiene las interfaces embed_documents y embed_query.

Códigos HTTP considerados reintentables:

    429: límite de solicitudes alcanzado.
    500: error interno del servidor.
    502: respuesta incorrecta de un servidor intermediario.
    503: servicio temporalmente no disponible.

La espera exponencial se calcula mediante:

    espera = espera_inicial * (2 ** (intento - 1))

El número máximo de intentos incluye la primera ejecución.

IMPORTANTE:
    Este adaptador no escribe directamente en ChromaDB.

    Su responsabilidad consiste en generar embeddings
    mediante el proveedor configurado y gestionar
    los reintentos de las operaciones correspondientes.

    La persistencia de los vectores queda a cargo
    del componente que utiliza este adaptador.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Permite introducir esperas entre intentos consecutivos.
import time

# Excepción de la API de Google que proporciona
# información sobre el código HTTP del error.
from google.genai.errors import APIError

# Interfaz base de embeddings utilizada por LangChain.
from langchain_core.embeddings import Embeddings

# Excepción de integración de Google Generative AI
# utilizada para identificar fallos del proveedor.
from langchain_google_genai._common import GoogleGenerativeAIError


# ============================================================
# 2. CONFIGURACIÓN DE ERRORES REINTENTABLES
# ============================================================

# Conjunto de códigos HTTP considerados recuperables.
#
# El mecanismo de reintentos se activa únicamente
# cuando encuentra uno de estos códigos dentro
# de la cadena de excepciones correspondiente.
#
# Los demás códigos no generan nuevos intentos.
CODIGOS_REINTENTABLES = {429, 500, 502, 503}


# ============================================================
# 3. ADAPTADOR DE EMBEDDINGS CON REINTENTOS
# ============================================================

class EmbeddingsConReintentos(Embeddings):
    """Reintenta errores temporales antes de escribir en ChromaDB.

    Implementa la interfaz Embeddings de LangChain
    y delega la generación de vectores en otro
    objeto compatible con dicha interfaz.

    El adaptador incorpora una política de reintentos
    para determinadas excepciones del proveedor Gemini.

    Attributes:
        embeddings:
            Implementación de Embeddings utilizada
            para generar los vectores.

        max_intentos:
            Número máximo de ejecuciones permitidas
            para una operación, incluida la inicial.

        espera_inicial:
            Tiempo base, expresado en segundos,
            utilizado para calcular las esperas.

    Los errores no recuperables se propagan
    sin realizar nuevos intentos.
    """

    # --------------------------------------------------------
    # 3.1. INICIALIZACIÓN DEL ADAPTADOR
    # --------------------------------------------------------

    def __init__(
        self,
        embeddings: Embeddings,
        max_intentos: int = 3,
        espera_inicial: float = 2.0,
    ):
        """Inicializa el adaptador y valida su configuración.

        Args:
            embeddings:
                Implementación de Embeddings que ejecutará
                las operaciones reales de generación de vectores.

            max_intentos:
                Número máximo de intentos por operación.

                Debe ser mayor o igual a 1.

                El valor predeterminado es 3.

            espera_inicial:
                Tiempo base de espera entre intentos,
                expresado en segundos.

                Debe ser mayor o igual a cero.

                El valor predeterminado es 2.0.

        Raises:
            ValueError:
                Si max_intentos es menor que 1.

            ValueError:
                Si espera_inicial es negativa.

        La inicialización no genera embeddings
        ni realiza llamadas al proveedor.
        """

        # Exige al menos una ejecución de cada operación.
        if max_intentos < 1:
            raise ValueError("max_intentos debe ser al menos 1.")

        # Impide configurar tiempos de espera negativos.
        if espera_inicial < 0:
            raise ValueError("espera_inicial no puede ser negativa.")

        # Conserva la implementación original de embeddings.
        self.embeddings = embeddings

        # Almacena la cantidad máxima de intentos.
        self.max_intentos = max_intentos

        # Almacena el tiempo base para los reintentos.
        self.espera_inicial = espera_inicial

    # --------------------------------------------------------
    # 3.2. IDENTIFICACIÓN DEL CÓDIGO HTTP
    # --------------------------------------------------------

    @staticmethod
    def _codigo_http(error: Exception) -> int | None:
        """Busca el código HTTP en la cadena de excepciones.

        Recorre la excepción recibida y sus causas
        explícitas mediante el atributo __cause__.

        Args:
            error:
                Excepción desde la cual comienza
                la búsqueda del código HTTP.

        Returns:
            int | None:
                Código HTTP de la primera excepción
                APIError encontrada.

                Devuelve None cuando no encuentra
                una excepción de ese tipo.

        El conjunto visitados evita recorrer
        repetidamente una misma instancia de excepción.

        El método no modifica las excepciones
        ni determina por sí mismo si corresponde
        ejecutar un reintento.
        """

        # Comienza la búsqueda desde la excepción recibida.
        actual = error

        # Registra las identidades de las excepciones
        # examinadas para evitar recorridos repetidos.
        visitados = set()

        # Recorre las causas explícitas mientras
        # existan excepciones no visitadas.
        while actual is not None and id(actual) not in visitados:

            # Marca la excepción actual como examinada.
            visitados.add(id(actual))

            # Recupera el código HTTP cuando encuentra
            # una excepción de la API de Google.
            if isinstance(actual, APIError):
                return actual.code

            # Continúa con la causa explícita del error.
            actual = actual.__cause__

        # No se encontró un código HTTP en la cadena.
        return None

    # --------------------------------------------------------
    # 3.3. EJECUCIÓN CON REINTENTOS CONTROLADOS
    # --------------------------------------------------------

    def _ejecutar(self, operacion, *args):
        """Ejecuta una operación y reintenta solo errores recuperables.

        Centraliza la política de reintentos utilizada
        por embed_documents() y embed_query().

        Args:
            operacion:
                Función o método que ejecuta
                la generación de embeddings.

            *args:
                Argumentos que se entregan
                a la operación seleccionada.

        Returns:
            Resultado de la operación original
            cuando finaliza correctamente.

        Raises:
            GoogleGenerativeAIError:
                Si el error no corresponde a un código
                HTTP reintentable o se agotan los intentos.

            RuntimeError:
                Si el flujo alcanza inesperadamente
                el final del mecanismo de reintentos.

        Política de reintentos:
            - Solo captura GoogleGenerativeAIError.
            - Extrae el código HTTP de su cadena de causas.
            - Reintenta los códigos definidos
              en CODIGOS_REINTENTABLES.
            - No espera después del último intento.
            - Propaga los errores no recuperables.

        La espera se duplica después de cada fallo
        reintentable, según la fórmula exponencial.
        """

        # Recorre los intentos permitidos.
        #
        # El primer intento corresponde a la ejecución
        # inicial y también se contabiliza.
        for intento in range(1, self.max_intentos + 1):

            try:
                # Ejecuta la operación original.
                #
                # Si finaliza correctamente, devuelve
                # inmediatamente su resultado.
                return operacion(*args)

            # Captura los errores de la integración Gemini.
            except GoogleGenerativeAIError as error:

                # Busca el código HTTP en la excepción
                # y en sus causas explícitas.
                codigo = self._codigo_http(error)

                # Propaga el error cuando:
                #
                # 1. El código no admite reintentos.
                # 2. Se alcanzó el máximo de intentos.
                #
                # En ambos casos se conserva
                # la excepción original.
                if (
                    codigo not in CODIGOS_REINTENTABLES
                    or intento == self.max_intentos
                ):
                    raise

                # Calcula la espera exponencial.
                #
                # Con la configuración predeterminada:
                #
                # Después del intento 1: 2 segundos.
                # Después del intento 2: 4 segundos.
                #
                # No se realiza una espera adicional
                # después del último intento.
                espera = self.espera_inicial * (2 ** (intento - 1))

                # Suspende la ejecución antes de reintentar.
                time.sleep(espera)

        # Protección ante un estado de ejecución
        # que no debería alcanzarse durante
        # el funcionamiento normal del adaptador.
        raise RuntimeError("Estado de reintentos inesperado.")

    # --------------------------------------------------------
    # 3.4. GENERACIÓN DE EMBEDDINGS DE DOCUMENTOS
    # --------------------------------------------------------

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Genera embeddings de documentos con reintentos limitados.

        Args:
            texts:
                Lista de textos que deben transformarse
                en representaciones vectoriales.

        Returns:
            list[list[float]]:
                Lista de vectores numéricos generados
                por la implementación de embeddings.

        Delega la generación en el método embed_documents()
        del proveedor configurado.

        Si ocurre un error reintentable, aplica
        la política centralizada de _ejecutar().

        El método no almacena los vectores generados.
        """

        # Ejecuta la generación de embeddings
        # utilizando la política de reintentos.
        return self._ejecutar(self.embeddings.embed_documents, texts)

    # --------------------------------------------------------
    # 3.5. GENERACIÓN DE EMBEDDING DE CONSULTA
    # --------------------------------------------------------

    def embed_query(self, text: str) -> list[float]:
        """Genera el embedding de una consulta con reintentos limitados.

        Args:
            text:
                Texto de la consulta que debe transformarse
                en una representación vectorial.

        Returns:
            list[float]:
                Vector numérico generado para la consulta.

        Delega la operación en embed_query()
        de la implementación configurada.

        Utiliza la misma política de reintentos
        aplicada a los documentos para mantener
        un comportamiento consistente.
        """

        # Ejecuta la generación del vector de consulta
        # mediante el mecanismo centralizado de reintentos.
        return self._ejecutar(self.embeddings.embed_query, text)
