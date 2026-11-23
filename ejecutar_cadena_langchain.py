
"""Ejecuta una cadena de tres etapas de LangChain con Gemini.

Bloque 18 — SkillNest.

Este módulo proporciona el punto de entrada para ejecutar
una demostración de procesamiento secuencial mediante
una cadena de LangChain integrada con Gemini.

El flujo realiza las siguientes operaciones:

    1. Carga las variables de entorno del proyecto.
    2. Verifica que exista GEMINI_API_KEY.
    3. Inicializa el cliente de Gemini.
    4. Construye la cadena de tres etapas.
    5. Define un informe de evaluación de ejemplo.
    6. Envía el informe a la cadena.
    7. Presenta el resultado final en la terminal.

La implementación de las tres etapas se encuentra
en el módulo src.cadena_langchain.

Este archivo se limita a configurar las dependencias,
proporcionar el texto de entrada y ejecutar la cadena.

La ejecución puede realizar llamadas reales a Gemini
según la implementación de la cadena.

Importar este módulo no inicia automáticamente
el procesamiento ni realiza consultas al modelo.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Permite acceder a las variables de entorno
# configuradas durante la ejecución.
import os

# Carga las variables definidas en un archivo .env.
from dotenv import load_dotenv

# Cliente de Gemini integrado con LangChain.
from langchain_google_genai import ChatGoogleGenerativeAI

# Función que construye la cadena de tres etapas
# implementada en el proyecto VyOps.
from src.cadena_langchain import construir_cadena


# ============================================================
# 2. EJECUCIÓN DE LA CADENA LANGCHAIN
# ============================================================

def main() -> None:
    """Configura Gemini y procesa un informe de evaluación.

    Inicializa el entorno necesario para ejecutar
    la cadena de tres etapas de LangChain.

    Posteriormente envía un informe de ejemplo
    sobre el rendimiento de un modelo de inteligencia
    artificial y presenta el resultado obtenido.

    Returns:
        None: El resultado de la cadena se imprime
        directamente en la terminal.

    Raises:
        RuntimeError:
            Si GEMINI_API_KEY no está definida
            o contiene un valor vacío.

    Notes:
        Utiliza el modelo gemini-3.5-flash-lite.

        El parámetro max_retries=0 deshabilita
        los reintentos automáticos del cliente.

        No se configura explícitamente la temperatura
        porque este modelo utiliza parámetros de
        muestreo fijos en la integración empleada.

        La función realiza una invocación a la cadena,
        pero la cantidad de solicitudes al modelo
        depende de su implementación interna.

        Los errores del cliente o de la cadena pueden
        propagarse al código que ejecuta esta función.
    """

    # --------------------------------------------------------
    # 2.1. CONFIGURACIÓN DEL ENTORNO
    # --------------------------------------------------------

    # Carga las variables de entorno desde el archivo .env,
    # cuando se encuentra disponible.
    load_dotenv()

    # Verifica que exista una clave de API antes
    # de inicializar el cliente de Gemini.
    #
    # Esta comprobación no valida las credenciales
    # contra el servicio remoto.
    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("No se encontró GEMINI_API_KEY.")

    # --------------------------------------------------------
    # 2.2. INICIALIZACIÓN DEL MODELO
    # --------------------------------------------------------

    # Este modelo utiliza parámetros de muestreo fijos.
    # No admite controlar la temperatura desde esta integración.
    #
    # max_retries=0 evita los reintentos automáticos
    # del cliente ante errores de ejecución.
    modelo = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        max_retries=0,
    )

    # --------------------------------------------------------
    # 2.3. CONSTRUCCIÓN DE LA CADENA
    # --------------------------------------------------------

    # Construye la cadena utilizando el modelo configurado.
    #
    # La composición de sus tres etapas está definida
    # en src.cadena_langchain, no en este ejecutor.
    cadena = construir_cadena(modelo)

    # --------------------------------------------------------
    # 2.4. PREPARACIÓN DEL INFORME
    # --------------------------------------------------------

    # Define un informe ficticio de evaluación
    # de conocimientos de programación Python.
    #
    # El informe contiene:
    #     - 20 preguntas evaluadas.
    #     - 16 respuestas correctas.
    #     - 4 respuestas incorrectas.
    #     - 2 errores sobre diccionarios.
    #     - 2 errores sobre manejo de excepciones.
    #     - 80 % de respuestas correctas.
    #
    # Este texto constituye la entrada de la cadena.
    informe = (
        "Se evaluó un modelo de inteligencia artificial con "
        "20 preguntas sobre programación Python. "
        "Respondió correctamente 16 preguntas y cometió "
        "4 errores. Dos errores fueron sobre diccionarios "
        "y otros dos sobre manejo de excepciones. "
        "El porcentaje de respuestas correctas fue del 80%."
    )

    # --------------------------------------------------------
    # 2.5. EJECUCIÓN DE LA CADENA
    # --------------------------------------------------------

    # Informa el inicio del procesamiento.
    print("Ejecutando cadena de tres etapas con Gemini...")

    # Envía el informe mediante la variable de entrada
    # "texto", esperada por la cadena de LangChain.
    #
    # La cadena procesa el contenido y devuelve
    # el resultado de su ejecución.
    resultado = cadena.invoke({"texto": informe})

    # --------------------------------------------------------
    # 2.6. PRESENTACIÓN DEL RESULTADO
    # --------------------------------------------------------

    # Presenta la salida final de la cadena
    # sin realizar transformaciones adicionales.
    print("\nRESULTADO FINAL:")
    print(resultado)


# ============================================================
# 3. PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    # Ejecuta la demostración únicamente cuando
    # este archivo se inicia directamente.
    #
    # Si otro módulo lo importa, main()
    # no se ejecuta automáticamente.
    main()
