"""Herramientas para la evaluación de respuestas del Bloque 17.

Permite recuperar evaluaciones anteriores y reutilizar
sus respuestas para evitar consultas innecesarias a Gemini.

La recuperación de resultados no realiza llamadas a la API.
"""

import json
from pathlib import Path
from src.cliente_api import consultar_modelo
from src.pipeline_texto import calcular_metricas
from evaluar_respuestas import guardar_resultados_metricas

def cargar_resultados_anteriores(
    ruta_archivo: str | Path,
) -> list[dict[str, str | float]]:
    """Carga resultados de evaluaciones anteriores desde JSON.

    Args:
        ruta_archivo: Ubicación del archivo JSON que contiene
            las respuestas y métricas de evaluaciones previas.

    Returns:
        Lista de diccionarios con las evaluaciones recuperadas.

        Si el archivo no existe, devuelve una lista vacía.

    Raises:
        ValueError: Si el JSON no contiene una lista de resultados.
        json.JSONDecodeError: Si el archivo contiene JSON inválido.

    Nota:
        Esta función no modifica el archivo original ni
        realiza consultas a Gemini.
    """

    # Convertimos la ruta recibida en un objeto Path.
    ruta = Path(ruta_archivo)

    # Si todavía no existe el archivo, no hay resultados
    # anteriores disponibles para reutilizar.
    if not ruta.is_file():
        return []

    # Leemos el archivo utilizando UTF-8 para conservar
    # correctamente los caracteres del español.
    with ruta.open(mode="r", encoding="utf-8") as archivo:
        resultados = json.load(archivo)

    # Comprobamos que la estructura principal sea una lista.
    # Así evitamos procesar accidentalmente otro tipo de JSON.
    if not isinstance(resultados, list):
        raise ValueError(
            "El archivo de resultados debe contener una lista."
        )

    # Devolvemos los resultados sin alterar su contenido.
    return resultados

def obtener_casos_pendientes(
    casos: list[dict[str, str]],
    resultados_anteriores: list[dict[str, str | float]],
) -> list[dict[str, str]]:
    """Identifica los casos que todavía necesitan evaluación.

    Compara las consultas configuradas con las consultas
    presentes en los resultados anteriores.

    Args:
        casos: Banco completo de preguntas y referencias.
        resultados_anteriores: Evaluaciones recuperadas
            desde un archivo JSON.

    Returns:
        Lista de casos que aún no tienen una respuesta
        registrada.

    Nota:
        La comparación utiliza el texto exacto de cada
        consulta. No realiza llamadas a Gemini ni modifica
        las listas recibidas.
    """

    # Recuperamos las consultas que ya tienen resultados.
    # Utilizamos un conjunto para realizar búsquedas eficientes.
    consultas_evaluadas: set[str] = {
        str(resultado["consulta"])
        for resultado in resultados_anteriores
    }

    # Seleccionamos únicamente los casos cuya consulta
    # todavía no aparece en las evaluaciones anteriores.
    casos_pendientes: list[dict[str, str]] = [
        caso.copy()
        for caso in casos
        if caso["consulta"] not in consultas_evaluadas
    ]

    # Devolvemos los casos pendientes sin modificar
    # el banco original ni las evaluaciones existentes.
    return casos_pendientes

def evaluar_casos_pendientes(
    casos_pendientes: list[dict[str, str]],
    ruta_archivo: str | Path,
    resultados_existentes: list[dict[str, str | float]] | None = None,
) -> list[dict[str, str | float]]:
    """Evalúa casos pendientes y guarda cada respuesta inmediatamente.

    Args:
        casos_pendientes: Casos que todavía requieren evaluación.
        ruta_archivo: Archivo JSON donde se guardarán los resultados.
        resultados_existentes: Evaluaciones previamente recuperadas.

    Returns:
        Lista completa de resultados, incluidos los anteriores.

    Nota:
        Esta función realiza llamadas reales a Gemini.
        Guarda cada respuesta después de calcular sus métricas.
        No debe utilizarse durante pruebas sin simular la API.
    """

    # Conservamos los resultados recibidos en una lista nueva.
    # Así evitamos modificar la lista original del llamador.
    resultados = list(resultados_existentes or [])

    # Evitamos sobrescribir un archivo que ya contiene resultados
    # si no fueron cargados explícitamente por el llamador.
    ruta = Path(ruta_archivo)

    if ruta.exists() and resultados_existentes is None:
        raise ValueError(
            "El archivo ya existe. Carga sus resultados antes "
            "de continuar para evitar sobrescribirlos."
        )

    # Identificamos las consultas que ya están registradas.
    consultas_guardadas = {
        str(resultado["consulta"])
        for resultado in resultados
    }

    # Procesamos únicamente los casos pendientes.
    for numero, caso in enumerate(casos_pendientes, start=1):
        consulta = caso["consulta"]
        referencia = caso["referencia"]

        # Protección adicional frente a consultas repetidas.
        if consulta in consultas_guardadas:
            print(f"Consulta ya evaluada, se omite: {consulta}")
            continue

        print(
            f"Evaluando caso {numero}/{len(casos_pendientes)}: "
            f"{consulta}",
            flush=True,
        )

        # Consultamos Gemini una vez por caso.
        respuesta = consultar_modelo(consulta)

        # Calculamos precisión, cobertura y F1.
        metricas = calcular_metricas(referencia, respuesta)

        # Guardamos también la referencia, necesaria
        # para la revisión manual del Bloque 17.
        resultado: dict[str, str | float] = {
            "consulta": consulta,
            "referencia": referencia,
            "respuesta": respuesta,
            "precision": metricas["precision"],
            "cobertura": metricas["cobertura"],
            "f1": metricas["f1"],
        }

        # Añadimos el resultado a la colección.
        resultados.append(resultado)
        consultas_guardadas.add(consulta)

        # Persistimos inmediatamente la evaluación.
        # Si una consulta posterior falla, las anteriores
        # permanecerán disponibles en el archivo JSON.
        guardar_resultados_metricas(resultados, ruta)

        print(
            f"Resultado guardado. Total acumulado: {len(resultados)}",
            flush=True,
        )

    return resultados

def seleccionar_muestra_revision(
    resultados: list[dict[str, str | float]],
    cantidad_por_extremo: int = 5,
) -> list[dict[str, str | float]]:
    """Selecciona respuestas con F1 bajo y alto para revisión.

    Ordena las evaluaciones por su puntuación F1 y selecciona
    casos de ambos extremos de la distribución.

    Args:
        resultados: Evaluaciones con sus métricas calculadas.
        cantidad_por_extremo: Número de casos que se
            seleccionarán de cada extremo.

    Returns:
        Lista de resultados seleccionados, sin duplicados.

    Raises:
        ValueError: Si la cantidad solicitada es negativa.

    Nota:
        La selección no determina si una respuesta es correcta.
        Solo identifica casos para una revisión humana posterior.
    """

    if cantidad_por_extremo < 0:
        raise ValueError(
            "La cantidad por extremo no puede ser negativa."
        )

    # Ordenamos por F1 sin modificar la lista original.
    ordenados = sorted(
        resultados,
        key=lambda resultado: float(resultado["f1"]),
    )

    # Seleccionamos primero los casos con menor F1.
    muestra = ordenados[:cantidad_por_extremo]

    # Registramos sus consultas para evitar duplicados.
    consultas_seleccionadas = {
        str(resultado["consulta"])
        for resultado in muestra
    }

    # Incorporamos los casos con mayor F1.
    for resultado in reversed(ordenados[-cantidad_por_extremo:]):
        consulta = str(resultado["consulta"])

        if consulta not in consultas_seleccionadas:
            muestra.append(resultado)
            consultas_seleccionadas.add(consulta)

    return muestra