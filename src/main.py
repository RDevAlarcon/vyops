
"""Punto de entrada de VyOps para las actividades de la Unidad 1.

Proyecto académico — Accenture / SkillNest.

Objetivo:
    Demostrar las funcionalidades desarrolladas antes del Bloque 12.

Pruebas:
    1. Consulta a Gemini y obtención de métricas.
    2. Consulta utilizando instrucciones de sistema.
    3. Validación de entradas incorrectas.

Arquitectura:
    Reutiliza las funciones de consumir_gemini.py.
    No duplica la autenticación, las peticiones HTTP,
    los reintentos ni el procesamiento de respuestas.

Consideraciones:
    Las pruebas 1 y 2 realizan consultas reales a Gemini.
    La prueba 3 utiliza una entrada inválida y no debería
    generar una solicitud al proveedor.
"""

from consumir_gemini import obtener_dato_de_prueba


def ejecutar_consulta(nombre: str, pregunta: str, system_instruction=None):
    """Ejecuta una consulta y controla los errores esperados.

    Args:
        nombre: Identificador de la prueba.
        pregunta: Texto que se enviará al modelo.
        system_instruction: Instrucción de sistema opcional.

    Returns:
        True si la consulta se completó correctamente.
        False si ocurrió un error controlado.
    """

    print(f"\n=== {nombre} ===")

    try:
        # Reutilizamos el cliente implementado durante la Unidad 1.
        resultado = obtener_dato_de_prueba(
            pregunta,
            system_instruction=system_instruction,
        )

        # Mostramos la respuesta y las métricas disponibles.
        print(resultado)
        return True

    except ValueError as error:
        # Error en la pregunta o en la configuración.
        print(f"Error de validación: {error}")
        return False

    except RuntimeError as error:
        # Error de comunicación, respuesta o procesamiento.
        # Los reintentos ya fueron gestionados por el cliente.
        print(f"Error durante la consulta a Gemini: {error}")
        return False


def main():
    """Ejecuta las tres pruebas funcionales de la Unidad 1."""

    # ---------------------------------------------------------
    # PRUEBA 1: CONSULTA NORMAL A GEMINI
    # ---------------------------------------------------------

    ejecutar_consulta(
        nombre="PRUEBA 1: CONSULTA A GEMINI",
        pregunta="¿Cuál es la capital de Inglaterra?",
    )

    # ---------------------------------------------------------
    # PRUEBA 2: INSTRUCCIONES DE SISTEMA
    # ---------------------------------------------------------

    # Configuramos el comportamiento esperado del modelo.
    instruccion = (
        "Eres un asistente de orientación municipal. "
        "Responde siempre en español, de forma breve y clara. "
        "Si no conoces la respuesta, indícalo."
    )

    ejecutar_consulta(
        nombre="PRUEBA 2: SYSTEM INSTRUCTION",
        pregunta="¿Cuál es tu función?",
        system_instruction=instruccion,
    )

    # ---------------------------------------------------------
    # PRUEBA 3: VALIDACIÓN DE ENTRADA INCORRECTA
    # ---------------------------------------------------------

    print("\n=== PRUEBA 3: VALIDACIÓN DE ENTRADA ===")

    try:
        # Enviamos intencionalmente una lista en lugar de texto.
        obtener_dato_de_prueba([1, 2])

    except ValueError as error:
        # El rechazo de esta entrada es el resultado esperado.
        print(f"Validación correcta: {error}")

    else:
        # Si no se produce ValueError, la validación no funcionó.
        print("ERROR: La entrada inválida no fue rechazada.")


# Ejecutamos las pruebas únicamente cuando este archivo
# se inicia directamente desde la terminal.
if __name__ == "__main__":
    main()
