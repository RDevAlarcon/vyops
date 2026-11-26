"""
Bloque 34: criterios de aceptación ejecutables.

Simula un servicio de consultas documentales para comprobar
criterios de aceptación sin utilizar modelos generativos,
conexiones de red ni dependencias externas.
"""

import time


def consultar(pregunta: str) -> dict:
    """
    Simula una consulta a un servicio documental.

    Si la pregunta está relacionada con devoluciones,
    entrega una respuesta respaldada por una fuente.

    Si no dispone de información, devuelve una respuesta
    de abstención y una lista de fuentes vacía.

    Args:
        pregunta: Texto de la consulta.

    Returns:
        Diccionario con la respuesta y las fuentes documentales.
    """

    # Simula un pequeño tiempo de procesamiento.
    time.sleep(0.01)

    if "devol" in pregunta.lower():
        return {
            "respuesta": "Tienes 30 dias desde la compra para devolver.",
            "fuentes": ["manual.pdf"],
        }

    return {
        "respuesta": "No encuentro esa informacion en el manual.",
        "fuentes": [],
    }

def ca_01() -> tuple[bool, str]:
    """
    Comprueba la estructura de la respuesta del servicio.

    Verifica que el diccionario retornado contenga exactamente
    los campos respuesta y fuentes.

    Returns:
        Tupla con el resultado de la comprobación y su evidencia.
    """

    resultado = consultar(
        "Cual es el plazo para devolver un producto?"
    )

    campos_esperados = {"respuesta", "fuentes"}

    # Compara los campos recibidos con los campos esperados.
    cumple = set(resultado) == campos_esperados

    evidencia = f"campos: {sorted(resultado)}"

    return cumple, evidencia

def ca_02() -> tuple[bool, str]:
    """
    Comprueba el contenido y la fuente documental de la respuesta.

    Verifica que el servicio mencione el plazo de devolución
    esperado y cite el documento correspondiente.

    Returns:
        Tupla con el resultado de la comprobación y su evidencia.
    """

    resultado = consultar(
        "Cual es el plazo para devolver un producto?"
    )

    # Comprueba la presencia de la fuente documental esperada.
    fuente_correcta = "manual.pdf" in resultado["fuentes"]

    # Comprueba que la respuesta incluya el plazo esperado.
    contenido_correcto = "30 dias" in resultado["respuesta"]

    cumple = fuente_correcta and contenido_correcto

    evidencia = f"fuentes: {resultado['fuentes']}"

    return cumple, evidencia

def ca_03() -> tuple[bool, str]:
    """
    Comprueba la abstención ante información desconocida.

    Verifica que el servicio reconozca la ausencia de
    información documental y no proporcione fuentes inexistentes.

    Returns:
        Tupla con el resultado de la comprobación y su evidencia.
    """

    resultado = consultar("Venden gift cards?")

    # Comprueba que el servicio no entregue fuentes inexistentes.
    sin_fuentes = resultado["fuentes"] == []

    # Comprueba que la respuesta comunique la falta de información.
    abstencion_correcta = (
        "no encuentro" in resultado["respuesta"].lower()
    )

    cumple = sin_fuentes and abstencion_correcta

    evidencia = (
        f"respuesta: {resultado['respuesta']}; "
        f"fuentes: {resultado['fuentes']}"
    )

    return cumple, evidencia

def ca_05() -> tuple[bool, str]:
    """
    Comprueba el rendimiento del servicio simulado.

    Ejecuta diez consultas y verifica que al menos nueve
    se completen en menos de cinco segundos.

    Returns:
        Tupla con el resultado de la comprobación y su evidencia.
    """

    tiempos = []

    for _ in range(10):
        inicio = time.perf_counter()

        consultar("Cual es el plazo para devolver un producto?")

        duracion = time.perf_counter() - inicio
        tiempos.append(duracion)

    # Cuenta las consultas que cumplen el umbral establecido.
    rapidas = sum(1 for tiempo in tiempos if tiempo < 5)

    cumple = rapidas >= 9

    evidencia = f"{rapidas} de 10 en menos de 5 s"

    return cumple, evidencia

# Catálogo de criterios de aceptación y sus pruebas asociadas.
CRITERIOS = [
    (
        "CA-01",
        "RF-01",
        "respuesta JSON con respuesta y fuentes",
        ca_01,
    ),
    (
        "CA-02",
        "RF-02",
        "fuente manual.pdf y menciona 30 dias",
        ca_02,
    ),
    (
        "CA-03",
        "RF-02",
        "sin informacion en el manual: no inventa",
        ca_03,
    ),
    (
        "CA-05",
        "RNF-01",
        "9 de 10 consultas en menos de 5 s",
        ca_05,
    ),
]

def ejecutar(criterios: list) -> None:
    """
    Ejecuta los criterios de aceptación registrados.

    Presenta el resultado y la evidencia de cada prueba.
    Si una prueba genera una excepción, registra el fallo
    y continúa evaluando los criterios restantes.

    Args:
        criterios: Catálogo de criterios que serán evaluados.
    """

    cumplidos = 0

    for identificador, cubre, descripcion, prueba in criterios:

        try:
            cumple, evidencia = prueba()

        except Exception as error:
            cumple = False
            evidencia = (
                f"error: {type(error).__name__}({error})"
            )

        estado = "PASA " if cumple else "FALLA"

        print(
            f"{estado} {identificador} ({cubre}) "
            f"{descripcion} -> {evidencia}"
        )

        if cumple:
            cumplidos += 1

    print(
        f"\n{cumplidos} de {len(criterios)} "
        "criterios cumplidos"
    )


if __name__ == "__main__":
    ejecutar(CRITERIOS)