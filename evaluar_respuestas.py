"""Evaluación de respuestas generadas por Gemini.

Bloque 15 — SkillNest.

Este módulo permitirá comparar respuestas generadas por
un modelo de inteligencia artificial con textos de referencia.

Se evaluará la coincidencia de vocabulario antes y después
de aplicar el pipeline de limpieza y tokenización de VyOps.
"""
# Permite guardar los resultados de evaluación en formato JSON.
import json
# Permite leer los argumentos proporcionados desde PowerShell.
import sys
# Facilita la construcción de rutas independientes
# del sistema operativo utilizado.
from pathlib import Path
from src.cliente_api import consultar_modelo
# Importamos la función que integra el procesamiento
# de texto con las métricas de precisión, cobertura y F1.
from src.pipeline_texto import calcular_coincidencia, calcular_metricas

# Casos de evaluación correspondientes al Bloque 16.
#
# Cada caso contiene:
# - consulta: pregunta que enviaremos al modelo Gemini.
# - referencia: respuesta esperada con la que compararemos
#   el texto generado por el modelo.
#
# Estas referencias permiten calcular coincidencias léxicas,
# pero no constituyen una evaluación semántica ni factual completa.

CASOS_EVALUACION_BLOQUE_16: list[dict[str, str]] = [
    {
        "consulta": "¿Qué es Python?",
        "referencia": (
            "Python es un lenguaje de programación interpretado."
        ),
    },
    {
        "consulta": "¿Cuándo se creó Python?",
        "referencia": "Python fue creado en 1991.",
    },
    {
        "consulta": "¿Qué es una lista en Python?",
        "referencia": (
            "Una lista es una colección ordenada y modificable."
        ),
    },
]

def evaluar_casos_bloque_16(
    casos: list[dict[str, str]],
) -> list[dict[str, str | float]]:
    """Evalúa respuestas de Gemini mediante precisión, cobertura y F1.

    Recorre los casos de evaluación definidos para el Bloque 16.
    Para cada caso, consulta una sola vez al modelo Gemini,
    compara la respuesta con el texto de referencia y
    almacena las métricas obtenidas.

    Args:
        casos: Lista de diccionarios que contienen las claves
            "consulta" y "referencia".

    Returns:
        Lista de diccionarios con la consulta, la respuesta
        generada y las métricas de precisión, cobertura y F1.

        Si la lista de casos está vacía, devuelve una lista vacía.

    Nota:
        Esta función realiza llamadas reales a Gemini cuando
        se ejecuta. Definirla no genera solicitudes a la API.
    """

    # Preparamos una lista para almacenar los resultados
    # de todas las consultas evaluadas.
    resultados: list[dict[str, str | float]] = []

    # Recorremos los casos definidos para el Bloque 16.
    for caso in casos:

        # Recuperamos la pregunta y su respuesta de referencia.
        consulta = caso["consulta"]
        referencia = caso["referencia"]

        # Consultamos Gemini una sola vez por pregunta,
        # reutilizando el cliente existente de VyOps.
        respuesta = consultar_modelo(consulta)

        # Evaluamos la respuesta utilizando el pipeline
        # de limpieza, tokenización y métricas.
        metricas = calcular_metricas(
            referencia,
            respuesta,
        )

        # Guardamos la pregunta, la respuesta generada
        # y las tres métricas calculadas.
        resultado: dict[str, str | float] = {
            "consulta": consulta,
            "respuesta": respuesta,
            "precision": metricas["precision"],
            "cobertura": metricas["cobertura"],
            "f1": metricas["f1"],
        }

        # Incorporamos el resultado a la lista general.
        resultados.append(resultado)

    # Devolvemos todos los resultados para que puedan
    # guardarse posteriormente en un archivo JSON.
    return resultados

def guardar_resultados_metricas(
    resultados: list[dict[str, str | float]],
    ruta_archivo: str | Path,
) -> None:
    """Guarda los resultados de evaluación en formato JSON.

    Almacena las consultas, respuestas generadas y métricas
    de precisión, cobertura y F1 en un archivo reutilizable.

    Args:
        resultados: Lista de resultados obtenidos durante
            la evaluación de las respuestas de Gemini.
        ruta_archivo: Ruta donde se guardará el archivo JSON.

    Returns:
        None. Los resultados se escriben en el archivo indicado.

    Nota:
        La función crea los directorios necesarios si no existen.
        Utiliza UTF-8 para conservar correctamente los caracteres
        del español y no realiza llamadas a la API de Gemini.
    """

    # Convertimos la ruta recibida en un objeto Path
    # para trabajar de forma independiente del sistema operativo.
    ruta = Path(ruta_archivo)

    # Creamos el directorio de destino si todavía no existe.
    # parents=True permite crear directorios intermedios.
    # exist_ok=True evita errores cuando ya está creado.
    ruta.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Abrimos el archivo en modo escritura con codificación UTF-8.
    # El administrador de contexto garantiza su cierre.
    with ruta.open(
        mode="w",
        encoding="utf-8",
    ) as archivo:

        # Guardamos los resultados como JSON.
        # ensure_ascii=False conserva tildes y caracteres especiales.
        # indent=2 facilita la lectura del archivo.
        json.dump(
            resultados,
            archivo,
            ensure_ascii=False,
            indent=2,
        )

def resumir_metricas(
    resultados: list[dict[str, str | float]],
) -> dict[str, float]:
    """Calcula los promedios de las métricas de evaluación.

    Recorre los resultados obtenidos durante la evaluación
    de respuestas generadas por Gemini y calcula el promedio
    aritmético de precisión, cobertura y F1.

    Args:
        resultados: Lista de diccionarios que contienen
            las métricas de cada respuesta evaluada.

    Returns:
        Diccionario con los promedios de:
            precision: Precisión promedio.
            cobertura: Cobertura promedio.
            f1: Puntuación F1 promedio.

        Si no existen resultados, devuelve cero
        para las tres métricas.

    Nota:
        Los promedios se calculan sobre los casos evaluados,
        asignando el mismo peso a cada respuesta.
        No representan una evaluación semántica o factual.
    """

    # Si no existen resultados, devolvemos valores
    # neutros y evitamos una división por cero.
    if not resultados:
        return {
            "precision": 0.0,
            "cobertura": 0.0,
            "f1": 0.0,
        }

    # Obtenemos la cantidad total de respuestas evaluadas.
    cantidad_resultados = len(resultados)

    # Sumamos los valores de precisión de todos los casos
    # y dividimos por la cantidad de respuestas.
    precision_promedio = (
        sum(float(resultado["precision"]) for resultado in resultados)
        / cantidad_resultados
    )

    # Calculamos el promedio de cobertura.
    cobertura_promedio = (
        sum(float(resultado["cobertura"]) for resultado in resultados)
        / cantidad_resultados
    )

    # Calculamos el promedio de las puntuaciones F1.
    f1_promedio = (
        sum(float(resultado["f1"]) for resultado in resultados)
        / cantidad_resultados
    )

    # Devolvemos los tres promedios en un diccionario
    # para facilitar su presentación y reutilización.
    return {
        "precision": precision_promedio,
        "cobertura": cobertura_promedio,
        "f1": f1_promedio,
    }

def obtener_peores_casos(
    resultados: list[dict[str, str | float]],
    limite: int = 3,
) -> list[dict[str, str | float]]:
    """Identifica las respuestas con menor puntuación F1.

    Ordena los resultados de evaluación desde la puntuación
    F1 más baja hasta la más alta y devuelve una cantidad
    limitada de casos para su revisión.

    Args:
        resultados: Lista de evaluaciones que contienen
            las respuestas y sus métricas.
        limite: Cantidad máxima de casos que se devolverán.
            Por defecto, se seleccionan los tres peores.

    Returns:
        Lista de resultados ordenados por F1 ascendente.

        Si no existen resultados o el límite es cero,
        devuelve una lista vacía.

    Raises:
        ValueError: Si el límite es negativo.

    Nota:
        Un F1 bajo señala poca coincidencia léxica,
        pero no demuestra necesariamente que la respuesta
        sea incorrecta. Los casos deben revisarse
        considerando su significado y exactitud factual.
    """

    # Evitamos aceptar cantidades negativas de resultados.
    if limite < 0:
        raise ValueError(
            "El límite de casos no puede ser negativo."
        )

    # Si no existen resultados o no se solicita ninguno,
    # devolvemos una lista vacía.
    if not resultados or limite == 0:
        return []

    # Ordenamos los resultados desde el menor F1.
    # sorted() genera una nueva lista, por lo que
    # no modifica el orden de los resultados originales.
    resultados_ordenados = sorted(
        resultados,
        key=lambda resultado: float(resultado["f1"]),
    )

    # Seleccionamos únicamente la cantidad solicitada.
    peores_casos = resultados_ordenados[:limite]

    # Devolvemos los casos que requieren revisión.
    return peores_casos

def ejecutar_evaluacion_bloque_16() -> None:
    """Ejecuta la evaluación completa de respuestas del Bloque 16.

    Consulta Gemini una sola vez por cada caso configurado,
    calcula precisión, cobertura y F1, guarda los resultados
    en JSON y presenta un resumen en la terminal.

    También identifica los tres casos con menor F1 para
    facilitar su revisión posterior.

    Nota:
        Esta función realiza llamadas reales a Gemini.
        No debe ejecutarse durante las pruebas unitarias.
    """

    # Evaluamos las consultas configuradas para el Bloque 16.
    # Cada pregunta genera una sola solicitud a Gemini.
    resultados = evaluar_casos_bloque_16(
        CASOS_EVALUACION_BLOQUE_16
    )

    # Definimos la ruta del archivo donde almacenaremos
    # las respuestas y sus métricas.
    ruta_resultados = (
        Path("resultados") / "resultados_metricas.json"
    )

    # Guardamos las evaluaciones para poder analizarlas
    # posteriormente sin volver a consultar Gemini.
    guardar_resultados_metricas(
        resultados,
        ruta_resultados,
    )

    # Calculamos los promedios de todas las evaluaciones.
    resumen = resumir_metricas(resultados)

    # Identificamos los tres casos con menor puntuación F1.
    peores_casos = obtener_peores_casos(
        resultados,
        limite=3,
    )

    # Presentamos el resumen general en la terminal.
    print("\n" + "=" * 60)
    print("BLOQUE 16 — EVALUACIÓN DE RESPUESTAS GEMINI")
    print("=" * 60)

    print(f"Respuestas evaluadas: {len(resultados)}")
    print(f"Precisión promedio: {resumen['precision']:.2%}")
    print(f"Cobertura promedio: {resumen['cobertura']:.2%}")
    print(f"F1 promedio: {resumen['f1']:.2%}")

    # Mostramos las preguntas con menor F1.
    # Estas requieren revisión, pero no necesariamente
    # contienen errores semánticos o factuales.
    print("\nCASOS CON MENOR F1")

    for posicion, caso in enumerate(peores_casos, start=1):
        print(
            f"{posicion}. {caso['consulta']} "
            f"| F1: {caso['f1']:.2%}"
        )

    # Informamos dónde quedaron almacenados los resultados.
    print(f"\nResultados guardados en: {ruta_resultados}")

# Definimos tres casos de evaluación.
# Cada caso contiene una pregunta para Gemini y una respuesta
# de referencia que utilizaremos para calcular coincidencias.
# Las referencias son breves y contienen información verificable.
# No representan todas las respuestas válidas posibles.

CASOS_EVALUACION = [
    {
        "pregunta": "¿Cuál es la capital de Chile? Responde brevemente.",
        "referencia": "La capital de Chile es Santiago.",
    },
    {
        "pregunta": "¿Cuánto es 5 multiplicado por 4? Responde brevemente.",
        "referencia": "Cinco multiplicado por cuatro es veinte.",
    },
    {
        "pregunta": "¿Qué lenguaje de programación utiliza la función print()? Responde brevemente.",
        "referencia": "La función print se utiliza en Python.",
    },
]

def evaluar_respuestas() -> None:
    """Evalúa tres respuestas reales generadas por Gemini.

    Recorre los casos de evaluación definidos previamente,
    consulta el modelo y compara cada respuesta con su
    correspondiente texto de referencia.

    Para cada caso calcula dos métricas:
        - Coincidencia sin normalización.
        - Coincidencia después de aplicar el pipeline.

    Los resultados se presentan en la terminal como
    porcentajes para facilitar su comparación.

    Raises:
        ValueError: Si existe un problema con los parámetros.
        RuntimeError: Si falla la comunicación con Gemini.

    Nota:
        Esta función realiza consultas reales a la API.
        No debe ejecutarse durante las pruebas unitarias.
    """

    # Recorremos los tres casos de evaluación.
    for numero, caso in enumerate(CASOS_EVALUACION, start=1):

        # Obtenemos la pregunta y su respuesta de referencia.
        pregunta = caso["pregunta"]
        referencia = caso["referencia"]

        # Consultamos Gemini utilizando el cliente modular
        # que desarrollamos en los bloques anteriores.
        respuesta = consultar_modelo(pregunta)

        # Calculamos la coincidencia conservando las
        # diferencias originales de formato.
        coincidencia_original = calcular_coincidencia(
            referencia,
            respuesta,
            normalizar=False,
        )

        # Calculamos la coincidencia después de aplicar
        # la limpieza y tokenización de nuestro pipeline.
        coincidencia_normalizada = calcular_coincidencia(
            referencia,
            respuesta,
            normalizar=True,
        )

        # Presentamos los textos utilizados en la evaluación.
        print(f"\n{'=' * 60}")
        print(f"CASO DE EVALUACIÓN {numero}")
        print(f"{'=' * 60}")
        print(f"Pregunta: {pregunta}")
        print(f"Referencia: {referencia}")
        print(f"Respuesta Gemini: {respuesta}")

        # Mostramos las métricas expresadas en porcentajes.
        print(
            f"Coincidencia original: "
            f"{coincidencia_original:.2%}"
        )
        print(
            f"Coincidencia normalizada: "
            f"{coincidencia_normalizada:.2%}"
        )

if __name__ == "__main__":
    # Este bloque se ejecuta únicamente cuando iniciamos
    # evaluar_respuestas.py directamente desde la terminal.
    # No se ejecuta al importar el módulo desde otro archivo.

    try:
        # Iniciamos la evaluación de los tres casos.
        # Cada caso realizará una consulta real a Gemini.
        # Seleccionamos la evaluación solicitada desde la terminal.
        # Sin argumentos, mantenemos el comportamiento del Bloque 15.
        if len(sys.argv) == 1:
            evaluar_respuestas()

        # El argumento --bloque-16 ejecuta exclusivamente
        # la evaluación con precisión, cobertura y F1.
        elif sys.argv[1:] == ["--bloque-16"]:
            ejecutar_evaluacion_bloque_16()

        # Rechazamos argumentos desconocidos para evitar
        # ejecutar una evaluación diferente a la solicitada.
        else:
            raise ValueError(
                "Argumento no reconocido. "
                "Usa --bloque-16 o ejecuta sin argumentos."
            )

    except ValueError as error:
        # Informamos los errores relacionados con parámetros
        # o configuración sin mostrar información sensible.
        print(f"Error de configuración: {error}")

    except RuntimeError as error:
        # Informamos los problemas de comunicación con Gemini,
        # incluyendo fallos que persistan después de los reintentos.
        print(f"Error al consultar Gemini: {error}")