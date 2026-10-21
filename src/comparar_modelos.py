

"""Evaluación comparativa de modelos Gemini para el proyecto VyOps.

Proyecto académico — Especialización en Desarrollo con IA Generativa.
Unidad 1: Evaluación de modelos, métricas y selección tecnológica.

Objetivo:
    Evaluar el modelo Gemini configurado mediante cinco casos
    representativos de las futuras funcionalidades de VyOps.

Casos de evaluación:
    1. Atención al cliente.
    2. Clasificación de solicitudes.
    3. Extracción de información.
    4. Selección de herramientas.
    5. Operaciones empresariales.

Responsabilidades:
    1. Recuperar resultados de evaluaciones anteriores.
    2. Ejecutar únicamente las pruebas pendientes.
    3. Registrar respuestas, tiempos y consumo de tokens.
    4. Calcular el costo estimado de cada consulta.
    5. Conservar resultados exitosos y errores.
    6. Exportar evidencias en formatos JSON y CSV.
    7. Presentar un resumen de las pruebas completadas.

Arquitectura:
    Reutiliza el cliente HTTP definido en consumir_gemini.py,
    evitando duplicar la lógica de autenticación, comunicación
    con el proveedor y procesamiento de respuestas.

Persistencia:
    Los resultados se almacenan en la carpeta resultados/,
    utilizando archivos independientes para cada modelo.

Seguridad:
    Las credenciales se gestionan mediante el cliente Gemini.
    Este módulo no almacena claves API en los resultados.

Alcance:
    La evaluación permite comparar métricas cuantitativas y
    conservar respuestas para una revisión cualitativa posterior.
    No realiza una calificación automática de calidad.
"""


import csv
import json
import time
from datetime import datetime
from pathlib import Path

from consumir_gemini import (
    MODELO,
    PRECIO_ENTRADA_MILLON,
    PRECIO_SALIDA_MILLON,
    armar_peticion,
    enviar_peticion,
    extraer_texto,
    extraer_uso_tokens,
    calcular_costo,
)


# Casos de prueba representativos de las funciones de VyOps.
PREGUNTAS = [
    {
        "id": 1,
        "categoria": "Atención al cliente",
        "pregunta": (
            "Un cliente pregunta por el horario de una empresa, "
            "pero no tenemos ese dato. ¿Cómo responderías? "
            "Redacta una respuesta breve para el cliente."
        ),
    },
    {
        "id": 2,
        "categoria": "Clasificación",
        "pregunta": (
            'Clasifica "Necesito cambiar mi reserva de mañana" '
            "como ventas, soporte o reservas. "
            'Devuelve solo JSON con la clave "categoria".'
        ),
    },
    {
        "id": 3,
        "categoria": "Extracción de datos",
        "pregunta": (
            'Extrae nombre, servicio y fecha de: '
            '"Soy Ana, necesito una limpieza el 20 de octubre". '
            "Devuelve solo JSON. No inventes el año."
        ),
    },
    {
        "id": 4,
        "categoria": "Selección de herramientas",
        "pregunta": (
            "Un usuario solicita consultar el estado de su "
            "pedido 1234. ¿Qué herramienta necesitarías y "
            "qué harías antes de responder? "
            "No inventes el estado del pedido."
        ),
    },
    {
        "id": 5,
        "categoria": "Operaciones empresariales",
        "pregunta": (
            "Una pyme recibe pedidos por WhatsApp y los copia "
            "manualmente a Excel. Propón tres mejoras "
            "priorizadas y explica brevemente sus beneficios."
        ),
    },
]


# Carpeta de resultados dentro del repositorio.
CARPETA_RESULTADOS = (
    Path(__file__).resolve().parent.parent / "resultados"
)


def cargar_resultados() -> list[dict]:
    """Carga los resultados históricos del modelo Gemini configurado.

    Busca en la carpeta resultados/ el archivo JSON correspondiente
    al modelo definido en la constante MODELO.

    Si el archivo todavía no existe, devuelve una lista vacía
    para permitir que la evaluación comience desde cero.

    Cuando existe, recupera su contenido y comprueba que la
    estructura principal sea una lista de resultados.

    Returns:
        Lista de diccionarios con las evaluaciones registradas.
        Devuelve una lista vacía si no existe el archivo.

    Raises:
        ValueError: Si el archivo contiene JSON válido, pero
            su estructura principal no es una lista.
        json.JSONDecodeError: Si el contenido no es JSON válido.
        OSError: Si ocurre un problema al leer el archivo.

    Nota:
        Esta función no ejecuta consultas a Gemini ni modifica
        los resultados almacenados.
    """

    ruta_json = CARPETA_RESULTADOS / f"{MODELO}_pruebas.json"

    if not ruta_json.exists():
        return []

    with ruta_json.open("r", encoding="utf-8") as archivo:
        resultados = json.load(archivo)

    if not isinstance(resultados, list):
        raise ValueError("El archivo de resultados no contiene una lista.")

    return resultados

def ejecutar_prueba(caso: dict) -> dict:
    """Ejecuta un caso de evaluación y registra sus métricas.

    Recibe un caso de prueba del banco de preguntas y construye
    una solicitud HTTP utilizando el cliente Gemini existente.

    Mide el tiempo de comunicación con el proveedor, incluyendo
    posibles reintentos, y recupera las métricas de consumo.

    Args:
        caso: Diccionario que contiene el identificador,
            la categoría y la pregunta de evaluación.

    Returns:
        Diccionario con los resultados de la ejecución:
            - fecha: Fecha y hora de la evaluación.
            - modelo: Modelo Gemini utilizado.
            - id_pregunta: Identificador del caso.
            - categoria: Categoría de la evaluación.
            - pregunta: Texto enviado al modelo.
            - estado: "exito" o "error".
            - respuesta: Texto generado por Gemini.
            - tiempo_segundos: Duración de la comunicación HTTP.
            - tokens_entrada: Tokens de entrada informados.
            - tokens_salida: Tokens de salida informados.
            - tokens_razonamiento: Tokens de razonamiento informados.
            - tokens_totales: Total de tokens informado.
            - costo_estimado_usd: Costo estimado de la consulta.
            - error: Descripción del fallo, si corresponde.

    Manejo de errores:
        Captura ValueError y RuntimeError para registrar el fallo
        sin perder la información del caso evaluado.

        Si la consulta falla, mantiene el estado "error" y
        conserva las métricas disponibles.

    Nota:
        Esta función ejecuta una consulta real a Gemini.
        No guarda archivos; esa responsabilidad corresponde
        a guardar_resultados().
    """

    resultado = {
        "fecha": datetime.now().astimezone().isoformat(),
        "modelo": MODELO,
        "id_pregunta": caso["id"],
        "categoria": caso["categoria"],
        "pregunta": caso["pregunta"],
        "estado": "error",
        "respuesta": "",
        "tiempo_segundos": None,
        "tokens_entrada": None,
        "tokens_salida": None,
        "tokens_razonamiento": None,
        "tokens_totales": None,
        "costo_estimado_usd": None,
        "error": "",
    }

    try:
        # Construimos la petición utilizando el cliente existente.
        url, encabezados, cuerpo = armar_peticion(caso["pregunta"])

        # Medimos exclusivamente la comunicación con Gemini.
        inicio = time.perf_counter()

        try:
            datos = enviar_peticion(url, encabezados, cuerpo)
        finally:
            resultado["tiempo_segundos"] = round(
                time.perf_counter() - inicio, 3
            )

        # Extraemos la respuesta y el consumo informado.
        respuesta = extraer_texto(datos)
        uso = extraer_uso_tokens(datos)

        costo = calcular_costo(
            datos,
            PRECIO_ENTRADA_MILLON,
            PRECIO_SALIDA_MILLON,
        )

        resultado.update(
            {
                "estado": "exito",
                "respuesta": respuesta,
                "tokens_entrada": uso["tokens_entrada"],
                "tokens_salida": uso["tokens_salida"],
                "tokens_razonamiento": uso["tokens_razonamiento"],
                "tokens_totales": uso["tokens_totales"],
                "costo_estimado_usd": costo,
            }
        )

    except (ValueError, RuntimeError) as error:
        resultado["error"] = str(error)

    return resultado


def guardar_resultados(resultados: list[dict]) -> None:
    """Guarda las evaluaciones del modelo en archivos JSON y CSV.

    Crea la carpeta resultados/ si todavía no existe y genera
    dos archivos identificados mediante la constante MODELO.

    El archivo JSON conserva las respuestas completas y las
    métricas de cada evaluación, facilitando su revisión.

    El archivo CSV organiza los mismos registros en columnas
    para permitir su análisis en Excel u otras herramientas.

    Args:
        resultados: Lista no vacía de diccionarios con los
            registros de evaluación y sus métricas.

    Returns:
        None. Los resultados se escriben en archivos locales.

    Raises:
        OSError: Si ocurre un problema al crear la carpeta
            o escribir alguno de los archivos.
        IndexError: Si la lista de resultados está vacía.

    Nota:
        Los archivos se identifican por modelo y se sobrescriben
        con el contenido completo de la lista recibida.

        El historial se conserva porque main() recupera los
        registros anteriores antes de agregar nuevas pruebas.

        Esta función no realiza consultas a Gemini.
    """

    CARPETA_RESULTADOS.mkdir(parents=True, exist_ok=True)

    ruta_json = CARPETA_RESULTADOS / f"{MODELO}_pruebas.json"
    ruta_csv = CARPETA_RESULTADOS / f"{MODELO}_pruebas.csv"

    # JSON conserva las respuestas completas para evaluar calidad.
    with ruta_json.open("w", encoding="utf-8") as archivo:
        json.dump(resultados, archivo, ensure_ascii=False, indent=2)

    # CSV facilita la comparación posterior de métricas.
    with ruta_csv.open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(
            archivo,
            fieldnames=list(resultados[0].keys()),
        )
        escritor.writeheader()
        escritor.writerows(resultados)

    print(f"\nJSON guardado: {ruta_json}")
    print(f"CSV guardado:  {ruta_csv}")

def main() -> None:
    """Coordina la evaluación del modelo Gemini configurado.

    Recupera las evaluaciones anteriores e identifica los casos
    que ya finalizaron correctamente para evitar repetirlos.

    Recorre los cinco casos de prueba configurados y ejecuta
    únicamente aquellos que todavía están pendientes.

    Después de cada ejecución:
        1. Registra el resultado obtenido.
        2. Muestra el estado y las métricas disponibles.
        3. Guarda el historial actualizado en JSON y CSV.
        4. Detiene las pruebas si se registra un error.

    Al finalizar, presenta un resumen que incluye:
        - Cantidad de preguntas completadas.
        - Latencia promedio de las ejecuciones exitosas.
        - Costo estimado acumulado de las pruebas exitosas.

    Returns:
        None. Los resultados se muestran en consola y se
        conservan mediante guardar_resultados().

    Nota:
        La evaluación puede reanudarse después de una
        interrupción sin repetir los casos exitosos.

        Los intentos fallidos permanecen en el historial
        para facilitar su análisis posterior.

        Esta función puede realizar consultas reales a Gemini
        cuando existen casos pendientes.
    """

    # Recuperamos las ejecuciones anteriores del modelo activo.
    resultados = cargar_resultados()

    # Identificamos las preguntas que ya fueron completadas.
    preguntas_exitosas = {
        resultado["id_pregunta"]
        for resultado in resultados
        if resultado.get("modelo") == MODELO
        and resultado.get("estado") == "exito"
    }

    print(f"\nModelo evaluado: {MODELO}")
    print(f"Preguntas configuradas: {len(PREGUNTAS)}")
    print(f"Preguntas ya completadas: {len(preguntas_exitosas)}")

    for caso in PREGUNTAS:
        # No repetimos las preguntas que ya respondieron correctamente.
        if caso["id"] in preguntas_exitosas:
            print(
                f"\nPrueba {caso['id']}: "
                "ya completada, se omite."
            )
            continue

        print(
            f"\nPrueba {caso['id']}/{len(PREGUNTAS)}: "
            f"{caso['categoria']}"
        )

        resultado = ejecutar_prueba(caso)

        # Conservamos el historial, incluso si hubo un error.
        resultados.append(resultado)

        print(f"Estado: {resultado['estado']}")
        print(f"Tiempo: {resultado['tiempo_segundos']} s")
        print(f"Tokens totales: {resultado['tokens_totales']}")
        print(
            "Costo estimado: "
            f"USD {resultado['costo_estimado_usd']}"
        )

        if resultado["error"]:
            print(f"Error: {resultado['error']}")

        # Guardamos todas las ejecuciones anteriores y la nueva.
        guardar_resultados(resultados)

        if resultado["estado"] == "error":
            print("\nPruebas detenidas para revisar el error.")
            break

        preguntas_exitosas.add(caso["id"])

    # El resumen considera únicamente las preguntas exitosas.
    exitosas = [
        resultado
        for resultado in resultados
        if resultado.get("modelo") == MODELO
        and resultado.get("estado") == "exito"
    ]

    tiempos = [
        resultado["tiempo_segundos"]
        for resultado in exitosas
        if resultado.get("tiempo_segundos") is not None
    ]

    costo_total = sum(
        resultado["costo_estimado_usd"]
        for resultado in exitosas
        if resultado.get("costo_estimado_usd") is not None
    )

    print("\n--- Resumen del modelo ---")
    print(f"Preguntas completadas: {len(preguntas_exitosas)}/{len(PREGUNTAS)}")

    if tiempos:
        print(
            f"Latencia promedio: "
            f"{sum(tiempos) / len(tiempos):.3f} segundos"
        )

    print(f"Costo estimado acumulado: USD {costo_total:.8f}")

# ---------------------------------------------------------------------------
# Punto de entrada: evaluación de modelos Gemini para VyOps.
#
# Este bloque se ejecuta únicamente cuando el archivo se inicia
# directamente desde la terminal.
#
# Al llamar a main():
#   1. Recupera los resultados de evaluaciones anteriores.
#   2. Identifica las pruebas pendientes del modelo configurado.
#   3. Ejecuta las consultas necesarias a Google Gemini.
#   4. Guarda las evidencias en archivos JSON y CSV.
#   5. Muestra un resumen de latencia y costo estimado.
#
# Importar este módulo desde otro archivo no inicia las pruebas.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()