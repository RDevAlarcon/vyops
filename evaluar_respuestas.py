
"""Evalúa respuestas generadas por Gemini en el proyecto VyOps.

Bloques 15 y 16 — SkillNest.

Este módulo implementa dos mecanismos de evaluación
de respuestas generadas por modelos de lenguaje.

Bloque 15:
    Compara las respuestas de Gemini con textos de referencia
    mediante coincidencia léxica, antes y después de aplicar
    el pipeline de limpieza y tokenización de VyOps.

Bloque 16:
    Amplía la evaluación incorporando métricas de precisión,
    cobertura y F1, junto con funciones para:
        - Evaluar conjuntos de preguntas y referencias.
        - Guardar resultados en archivos JSON.
        - Calcular promedios de las métricas.
        - Identificar los casos con menor puntuación F1.
        - Presentar resúmenes en la terminal.

Las métricas permiten comparar el vocabulario utilizado
en las respuestas, pero no garantizan su corrección
semántica, factual o documental.

El módulo utiliza el cliente de Gemini y el pipeline
de procesamiento de texto existentes en VyOps.

Las funciones de evaluación realizan solicitudes reales
a Gemini cuando son ejecutadas.

La importación del módulo no inicia automáticamente
las evaluaciones.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Permite serializar los resultados de evaluación
# para conservarlos en archivos JSON.
import json

# Permite interpretar los argumentos proporcionados
# desde PowerShell u otra terminal.
import sys

# Facilita la construcción de rutas de archivos
# independientes del sistema operativo.
from pathlib import Path

# Cliente modular encargado de consultar Gemini.
from src.cliente_api import consultar_modelo

# Funciones del pipeline de texto de VyOps.
#
# calcular_coincidencia compara vocabulario con
# normalización opcional.
#
# calcular_metricas calcula precisión, cobertura y F1.
from src.pipeline_texto import calcular_coincidencia, calcular_metricas


# ============================================================
# 2. CASOS DE EVALUACIÓN — BLOQUE 16
# ============================================================

# Conjunto de evaluación utilizado para medir
# precisión, cobertura y F1.
#
# Cada caso contiene:
#     consulta: Pregunta enviada al modelo.
#     referencia: Texto esperado para la comparación.
#
# Las referencias son breves y permiten una evaluación
# léxica reproducible sobre las respuestas obtenidas.
#
# No representan todas las respuestas válidas posibles
# ni constituyen una verificación factual completa.
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


# ============================================================
# 3. EVALUACIÓN DE RESPUESTAS — BLOQUE 16
# ============================================================

def evaluar_casos_bloque_16(
    casos: list[dict[str, str]],
) -> list[dict[str, str | float]]:
    """Evalúa respuestas de Gemini mediante precisión, cobertura y F1.

    Recorre los casos proporcionados y consulta Gemini
    una vez por cada pregunta.

    Compara cada respuesta con su referencia utilizando
    el pipeline de procesamiento de texto de VyOps.

    Args:
        casos: Lista de diccionarios que contienen:
            - consulta: Pregunta enviada a Gemini.
            - referencia: Respuesta utilizada como referencia.

    Returns:
        Lista de diccionarios con los campos:
            - consulta: Pregunta evaluada.
            - respuesta: Texto generado por Gemini.
            - precision: Precisión léxica calculada.
            - cobertura: Cobertura léxica calculada.
            - f1: Media armónica de ambas métricas.

        Si la lista de entrada está vacía,
        devuelve una lista vacía.

    Notes:
        La función realiza una llamada a consultar_modelo()
        por cada caso de evaluación.

        No guarda automáticamente los resultados en disco.

        Las excepciones producidas por el cliente o el
        pipeline pueden propagarse al código que la invoca.
    """

    # Almacena los resultados de cada consulta evaluada.
    resultados: list[dict[str, str | float]] = []

    # Procesa los casos en el orden recibido.
    for caso in casos:

        # Recupera la pregunta y el texto de referencia.
        consulta = caso["consulta"]
        referencia = caso["referencia"]

        # Realiza una solicitud al cliente de Gemini
        # por cada caso de evaluación.
        respuesta = consultar_modelo(consulta)

        # Calcula las métricas mediante el pipeline
        # de limpieza y tokenización de VyOps.
        metricas = calcular_metricas(
            referencia,
            respuesta,
        )

        # Construye el registro de evaluación
        # con la respuesta y las métricas calculadas.
        resultado: dict[str, str | float] = {
            "consulta": consulta,
            "respuesta": respuesta,
            "precision": metricas["precision"],
            "cobertura": metricas["cobertura"],
            "f1": metricas["f1"],
        }

        resultados.append(resultado)

    return resultados


# ============================================================
# 4. PERSISTENCIA DE RESULTADOS
# ============================================================

def guardar_resultados_metricas(
    resultados: list[dict[str, str | float]],
    ruta_archivo: str | Path,
) -> None:
    """Guarda los resultados de evaluación en formato JSON.

    Serializa la lista de evaluaciones y la escribe
    en la ruta indicada.

    Args:
        resultados: Colección de resultados que contiene
            consultas, respuestas y métricas.
        ruta_archivo: Ruta de destino, expresada como
            cadena o como objeto Path.

    Returns:
        None: Los resultados se escriben en disco.

    Notes:
        Crea los directorios de destino cuando no existen.

        Utiliza codificación UTF-8 y conserva caracteres
        del español mediante ensure_ascii=False.

        El modo de apertura "w" reemplaza el contenido
        de un archivo existente en la misma ruta.

        Esta función no consulta Gemini.
    """

    # Normaliza la representación de la ruta de destino.
    ruta = Path(ruta_archivo)

    # Crea el directorio de destino y sus directorios
    # intermedios cuando sea necesario.
    ruta.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Abre el archivo en modo escritura.
    # El administrador de contexto garantiza su cierre.
    with ruta.open(
        mode="w",
        encoding="utf-8",
    ) as archivo:

        # Serializa los resultados con una indentación
        # legible y preservando los caracteres Unicode.
        json.dump(
            resultados,
            archivo,
            ensure_ascii=False,
            indent=2,
        )


# ============================================================
# 5. RESUMEN DE MÉTRICAS
# ============================================================

def resumir_metricas(
    resultados: list[dict[str, str | float]],
) -> dict[str, float]:
    """Calcula promedios de precisión, cobertura y F1.

    Obtiene la media aritmética de cada métrica
    considerando todos los resultados recibidos.

    Args:
        resultados: Lista de evaluaciones con los campos
            precision, cobertura y f1.

    Returns:
        Diccionario con:
            - precision: Precisión promedio.
            - cobertura: Cobertura promedio.
            - f1: Puntuación F1 promedio.

        Si la lista está vacía, devuelve 0.0
        para las tres métricas.

    Notes:
        Cada caso tiene el mismo peso en el promedio.

        Los valores se convierten a float antes
        de realizar las operaciones.

        Los promedios no representan una evaluación
        semántica ni una comprobación factual.
    """

    # Evita divisiones por cero cuando no existen
    # evaluaciones disponibles.
    if not resultados:
        return {
            "precision": 0.0,
            "cobertura": 0.0,
            "f1": 0.0,
        }

    cantidad_resultados = len(resultados)

    # Calcula la media aritmética de precisión.
    precision_promedio = (
        sum(float(resultado["precision"]) for resultado in resultados)
        / cantidad_resultados
    )

    # Calcula la media aritmética de cobertura.
    cobertura_promedio = (
        sum(float(resultado["cobertura"]) for resultado in resultados)
        / cantidad_resultados
    )

    # Calcula la media aritmética de F1.
    f1_promedio = (
        sum(float(resultado["f1"]) for resultado in resultados)
        / cantidad_resultados
    )

    return {
        "precision": precision_promedio,
        "cobertura": cobertura_promedio,
        "f1": f1_promedio,
    }


# ============================================================
# 6. IDENTIFICACIÓN DE CASOS CON MENOR F1
# ============================================================

def obtener_peores_casos(
    resultados: list[dict[str, str | float]],
    limite: int = 3,
) -> list[dict[str, str | float]]:
    """Selecciona las evaluaciones con menor puntuación F1.

    Ordena los resultados de forma ascendente por F1
    y devuelve como máximo la cantidad solicitada.

    Args:
        resultados: Lista de evaluaciones con sus métricas.
        limite: Número máximo de casos que se devolverán.
            Su valor predeterminado es 3.

    Returns:
        Lista de evaluaciones ordenadas por F1 ascendente.

        Devuelve una lista vacía si no existen resultados
        o si el límite solicitado es cero.

    Raises:
        ValueError:
            Si el límite es negativo.

    Notes:
        sorted() genera una nueva lista y conserva
        el orden original de los resultados recibidos.

        Los casos con menor F1 presentan menor coincidencia
        léxica, pero no necesariamente son incorrectos
        desde el punto de vista semántico o factual.
    """

    # Rechaza límites negativos.
    if limite < 0:
        raise ValueError(
            "El límite de casos no puede ser negativo."
        )

    # Evita ordenar cuando no hay resultados
    # o cuando no se solicita ningún caso.
    if not resultados or limite == 0:
        return []

    # Ordena las evaluaciones por puntuación F1.
    resultados_ordenados = sorted(
        resultados,
        key=lambda resultado: float(resultado["f1"]),
    )

    # Selecciona hasta la cantidad máxima solicitada.
    peores_casos = resultados_ordenados[:limite]

    return peores_casos


# ============================================================
# 7. EJECUCIÓN COMPLETA — BLOQUE 16
# ============================================================

def ejecutar_evaluacion_bloque_16() -> None:
    """Ejecuta el proceso de evaluación del Bloque 16.

    Consulta Gemini para los casos configurados,
    calcula precisión, cobertura y F1, guarda los
    resultados y presenta un resumen en consola.

    También identifica los tres casos con menor F1
    para facilitar su revisión posterior.

    Returns:
        None: Los resultados se guardan en JSON
        y el resumen se presenta en la terminal.

    Notes:
        Esta función realiza llamadas reales a Gemini.

        Los resultados se guardan en:
            resultados/resultados_metricas.json

        La ruta es relativa al directorio de trabajo
        desde el cual se ejecuta el programa.

        La ejecución puede sobrescribir un archivo
        de resultados existente en esa ubicación.
    """

    # Evalúa los casos configurados para el Bloque 16.
    resultados = evaluar_casos_bloque_16(
        CASOS_EVALUACION_BLOQUE_16
    )

    # Define la ubicación del archivo JSON de resultados.
    ruta_resultados = (
        Path("resultados") / "resultados_metricas.json"
    )

    # Conserva las evaluaciones para analizarlas
    # posteriormente sin repetir las consultas.
    guardar_resultados_metricas(
        resultados,
        ruta_resultados,
    )

    # Calcula los promedios de las métricas.
    resumen = resumir_metricas(resultados)

    # Selecciona los casos con menor F1.
    peores_casos = obtener_peores_casos(
        resultados,
        limite=3,
    )

    # Presenta el resumen general de evaluación.
    print("\n" + "=" * 60)
    print("BLOQUE 16 — EVALUACIÓN DE RESPUESTAS GEMINI")
    print("=" * 60)

    print(f"Respuestas evaluadas: {len(resultados)}")
    print(f"Precisión promedio: {resumen['precision']:.2%}")
    print(f"Cobertura promedio: {resumen['cobertura']:.2%}")
    print(f"F1 promedio: {resumen['f1']:.2%}")

    # Muestra los casos que requieren revisión
    # por presentar menor coincidencia léxica.
    print("\nCASOS CON MENOR F1")

    for posicion, caso in enumerate(peores_casos, start=1):
        print(
            f"{posicion}. {caso['consulta']} "
            f"| F1: {caso['f1']:.2%}"
        )

    print(f"\nResultados guardados en: {ruta_resultados}")


# ============================================================
# 8. CASOS DE EVALUACIÓN — BLOQUE 15
# ============================================================

# Casos utilizados para comparar coincidencia léxica
# antes y después de la normalización del texto.
#
# Cada caso contiene:
#     pregunta: Consulta enviada al modelo.
#     referencia: Texto esperado para la comparación.
#
# Las referencias no representan necesariamente
# todas las formulaciones correctas posibles.
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


# ============================================================
# 9. EVALUACIÓN DE COINCIDENCIA — BLOQUE 15
# ============================================================

def evaluar_respuestas() -> None:
    """Compara respuestas de Gemini con textos de referencia.

    Ejecuta los casos del Bloque 15 y calcula dos
    medidas de coincidencia para cada respuesta:

        - Coincidencia original, sin normalización.
        - Coincidencia después de aplicar el pipeline.

    Args:
        No recibe argumentos.

    Returns:
        None: Presenta los resultados en la terminal.

    Raises:
        ValueError:
            Si ocurre un problema de parámetros
            propagado por las funciones utilizadas.
        RuntimeError:
            Si el cliente informa un fallo de comunicación
            con Gemini.

    Notes:
        Realiza una consulta real a Gemini por cada caso.

        Las respuestas se comparan con las referencias
        mediante calcular_coincidencia().

        Esta evaluación no guarda archivos JSON.
    """

    # Procesa cada caso en el orden definido.
    for numero, caso in enumerate(CASOS_EVALUACION, start=1):

        pregunta = caso["pregunta"]
        referencia = caso["referencia"]

        # Solicita una respuesta al modelo.
        respuesta = consultar_modelo(pregunta)

        # Calcula coincidencia sin normalizar el texto.
        coincidencia_original = calcular_coincidencia(
            referencia,
            respuesta,
            normalizar=False,
        )

        # Calcula coincidencia aplicando la normalización
        # implementada en el pipeline de VyOps.
        coincidencia_normalizada = calcular_coincidencia(
            referencia,
            respuesta,
            normalizar=True,
        )

        # Presenta los textos utilizados en la comparación.
        print(f"\n{'=' * 60}")
        print(f"CASO DE EVALUACIÓN {numero}")
        print(f"{'=' * 60}")
        print(f"Pregunta: {pregunta}")
        print(f"Referencia: {referencia}")
        print(f"Respuesta Gemini: {respuesta}")

        # Muestra las coincidencias como porcentajes.
        print(
            f"Coincidencia original: "
            f"{coincidencia_original:.2%}"
        )
        print(
            f"Coincidencia normalizada: "
            f"{coincidencia_normalizada:.2%}"
        )


# ============================================================
# 10. PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    # Selecciona la evaluación según los argumentos
    # recibidos desde la terminal.
    #
    # Sin argumentos:
    #     Ejecuta la evaluación del Bloque 15.
    #
    # Con --bloque-16:
    #     Ejecuta la evaluación del Bloque 16.
    #
    # Los argumentos desconocidos producen ValueError.

    try:
        if len(sys.argv) == 1:
            evaluar_respuestas()

        elif sys.argv[1:] == ["--bloque-16"]:
            ejecutar_evaluacion_bloque_16()

        else:
            raise ValueError(
                "Argumento no reconocido. "
                "Usa --bloque-16 o ejecuta sin argumentos."
            )

    except ValueError as error:
        # Informa errores de configuración o parámetros.
        print(f"Error de configuración: {error}")

    except RuntimeError as error:
        # Informa errores de comunicación propagados
        # por el cliente de Gemini.
        print(f"Error al consultar Gemini: {error}")
