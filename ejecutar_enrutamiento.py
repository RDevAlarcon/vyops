
"""Ejecuta el enrutamiento condicional de mensajes con Gemini.

Bloque 19 — SkillNest.

Este módulo proporciona el punto de entrada para ejecutar
una demostración del sistema de enrutamiento de VyOps.

El flujo realiza las siguientes operaciones:

    1. Carga las variables de entorno desde un archivo .env.
    2. Comprueba la disponibilidad de GEMINI_API_KEY.
    3. Inicializa el modelo Gemini configurado.
    4. Construye la cadena de enrutamiento de LangChain.
    5. Envía un mensaje de ejemplo a la cadena.
    6. Presenta la categoría detectada.
    7. Muestra la respuesta final generada.

La lógica de clasificación y enrutamiento se encuentra
en src.enrutamiento_langchain.

Este módulo se encarga exclusivamente de preparar
las dependencias y ejecutar el ejemplo.

La ejecución realiza las llamadas al modelo que requiera
la cadena de enrutamiento configurada.

Importar este archivo no ejecuta automáticamente
la demostración ni realiza solicitudes a Gemini.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Permite consultar las variables de entorno
# disponibles durante la ejecución.
import os

# Carga variables de entorno desde un archivo .env.
from dotenv import load_dotenv

# Cliente de Gemini integrado con LangChain.
from langchain_google_genai import ChatGoogleGenerativeAI

# Función que construye la cadena de clasificación
# y enrutamiento condicional definida en VyOps.
from src.enrutamiento_langchain import construir_cadena_enrutamiento


# ============================================================
# 2. EJECUCIÓN DEL ENRUTAMIENTO CONDICIONAL
# ============================================================

def main() -> None:
    """Configura Gemini y ejecuta un mensaje de demostración.

    Prepara las variables de entorno, verifica la existencia
    de la clave de API e inicializa el modelo Gemini.

    Posteriormente construye la cadena de enrutamiento
    y procesa una consulta municipal de ejemplo.

    Returns:
        None: Presenta el mensaje, la categoría detectada
        y la respuesta final en la terminal.

    Raises:
        RuntimeError:
            Si la variable GEMINI_API_KEY no está definida
            o contiene un valor vacío.

    Notes:
        Utiliza el modelo gemini-3.5-flash-lite.

        La configuración max_retries=0 deshabilita
        los reintentos automáticos del cliente.

        El mensaje de ejemplo consulta sobre los documentos
        necesarios para solicitar una patente comercial
        en Chile.

        La función realiza una invocación a la cadena
        de LangChain. Esta puede efectuar llamadas reales
        a Gemini según su implementación.

        Los errores propagados por el modelo o la cadena
        no se capturan dentro de esta función.
    """

    # Carga las variables definidas en el archivo .env,
    # cuando está disponible.
    load_dotenv()

    # Comprueba que exista una clave de API configurada
    # antes de inicializar el cliente de Gemini.
    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("No se encontró GEMINI_API_KEY.")

    # Inicializa el modelo utilizado por la cadena.
    #
    # max_retries=0 evita que el cliente realice
    # reintentos automáticos ante errores.
    modelo = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        max_retries=0,
    )

    # Construye la cadena de enrutamiento utilizando
    # la implementación existente en VyOps.
    cadena = construir_cadena_enrutamiento(modelo)

    # Define la consulta municipal utilizada
    # como ejemplo de clasificación y respuesta.
    mensaje = (
        "¿Qué documentos necesito para solicitar "
        "una patente comercial en Chile?"
    )

    # Presenta la consulta antes de ejecutar la cadena.
    print("Ejecutando enrutamiento condicional con Gemini...")
    print(f"\nMENSAJE: {mensaje}")

    # Invoca la cadena con un diccionario que contiene
    # el mensaje de entrada.
    #
    # La estructura esperada del resultado incluye
    # las claves "categoria" y "respuesta".
    resultado = cadena.invoke({"mensaje": mensaje})

    # Muestra la categoría determinada por la cadena.
    print("\nCATEGORÍA DETECTADA:")
    print(resultado["categoria"])

    # Presenta la respuesta final del enrutamiento.
    print("\nRESPUESTA FINAL:")
    print(resultado["respuesta"])


# ============================================================
# 3. PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    # Ejecuta la demostración únicamente cuando
    # este archivo se inicia directamente.
    #
    # Su importación desde otro módulo no activa
    # el proceso de enrutamiento.
    main()
