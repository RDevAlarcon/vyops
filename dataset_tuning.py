
"""Prepara y valida un dataset de tuning para solicitudes municipales.

Este módulo forma parte de las prácticas de personalización
de modelos de inteligencia artificial del proyecto VyOps.

Define un conjunto de ejemplos supervisados para clasificar
solicitudes municipales según dos atributos:

    1. Intención de la solicitud:
       - consulta_estado
       - nueva_solicitud
       - cancelacion
       - reclamo

    2. Prioridad:
       - baja
       - media
       - alta

Cada ejemplo contiene un texto de entrada y una salida
estructurada en formato JSON.

El módulo permite:

    - Construir ejemplos compatibles con TuningExample.
    - Revisar la distribución de categorías.
    - Validar el formato de los datos de entrenamiento.
    - Detectar entradas vacías o duplicadas.
    - Comprobar intenciones y prioridades permitidas.
    - Consultar periódicamente el estado de un tuning.
    - Ejecutar una prueba negativa con ejemplos inválidos.

La ejecución directa realiza únicamente comprobaciones
locales del dataset.

La función esperar_a_que_termine() permite consultar
un trabajo de tuning existente mediante un cliente Gemini,
pero no se invoca automáticamente desde este archivo.

Este módulo no crea ni inicia trabajos de entrenamiento.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Permite serializar y validar salidas en formato JSON.
import json

# Facilita el conteo de ejemplos por categoría.
from collections import Counter

# Tipos de datos proporcionados por el SDK de Gemini.
from google.genai import types

# Permite introducir pausas entre consultas de estado.
import time

# Cliente del SDK de Gemini para consultar trabajos de tuning.
from google import genai


# ============================================================
# 2. DATASET DE CLASIFICACIÓN MUNICIPAL
# ============================================================

# Dataset supervisado de clasificación de solicitudes municipales.
#
# Cada entrada contiene:
#     - Un texto que representa una solicitud ciudadana.
#     - Un diccionario con la intención y la prioridad esperadas.
#
# Se incluyen cuatro intenciones y tres niveles de prioridad.
#
# El conjunto contiene 12 ejemplos:
#     - 3 consultas de estado.
#     - 3 nuevas solicitudes.
#     - 3 cancelaciones.
#     - 3 reclamos.
#
# Cada intención incluye ejemplos de prioridad
# baja, media y alta.

ejemplos_raw = [
    (
        "Quiero saber en qué estado está mi solicitud municipal.",
        {"intencion": "consulta_estado", "prioridad": "baja"},
    ),
    (
        "Mi trámite lleva varios días pendiente y necesito conocer su avance.",
        {"intencion": "consulta_estado", "prioridad": "media"},
    ),
    (
        "Necesito conocer urgentemente el estado de mi solicitud porque vence mañana.",
        {"intencion": "consulta_estado", "prioridad": "alta"},
    ),
    (
        "Quiero ingresar una solicitud para reparar una banca de la plaza.",
        {"intencion": "nueva_solicitud", "prioridad": "baja"},
    ),
    (
        "Necesito solicitar la reparación de una luminaria que no funciona.",
        {"intencion": "nueva_solicitud", "prioridad": "media"},
    ),
    (
        "Hay un árbol con riesgo de caída sobre la vía pública y necesito reportarlo.",
        {"intencion": "nueva_solicitud", "prioridad": "alta"},
    ),
    (
        "Quiero cancelar una solicitud que ingresé por equivocación.",
        {"intencion": "cancelacion", "prioridad": "baja"},
    ),
    (
        "Necesito anular un trámite pendiente porque los datos son incorrectos.",
        {"intencion": "cancelacion", "prioridad": "media"},
    ),
    (
        "Solicito cancelar urgentemente una gestión que vence hoy.",
        {"intencion": "cancelacion", "prioridad": "alta"},
    ),
    (
        "Quiero presentar un reclamo por la limpieza de una plaza.",
        {"intencion": "reclamo", "prioridad": "baja"},
    ),
    (
        "La recolección de basura lleva varios días sin realizarse en mi calle.",
        {"intencion": "reclamo", "prioridad": "media"},
    ),
    (
        "Necesito denunciar una situación peligrosa que ya provocó un accidente.",
        {"intencion": "reclamo", "prioridad": "alta"},
    ),
]


# ============================================================
# 3. CONVERSIÓN A EJEMPLOS DE TUNING
# ============================================================

# Convierte los datos originales a objetos TuningExample,
# compatibles con la estructura utilizada por el SDK.
#
# text_input:
#     Contiene la solicitud municipal.
#
# output:
#     Contiene la clasificación esperada serializada
#     como una cadena JSON.
#
# ensure_ascii=False conserva los caracteres Unicode,
# incluyendo tildes y caracteres del español.

ejemplos = [
    types.TuningExample(
        text_input=texto,
        output=json.dumps(salida, ensure_ascii=False),
    )
    for texto, salida in ejemplos_raw
]


# ============================================================
# 4. ANÁLISIS DEL BALANCE DEL DATASET
# ============================================================

def chequear_balance(
    datos: list[tuple[str, dict]],
    clave: str = "intencion",
) -> Counter:
    """Cuenta los ejemplos del dataset por categoría.

    Recorre las etiquetas asociadas a cada texto
    y contabiliza sus apariciones.

    Args:
        datos (list[tuple[str, dict]]):
            Colección de pares formados por un texto
            y un diccionario de clasificación.

        clave (str):
            Campo utilizado para agrupar los ejemplos.

            Su valor predeterminado es "intencion",
            aunque también puede utilizarse "prioridad".

    Returns:
        Counter:
            Conteo de ejemplos para cada valor
            de la categoría seleccionada.

    Notes:
        La función realiza un conteo descriptivo.

        No modifica los datos ni verifica que
        las categorías sean válidas.

        Si un diccionario no contiene la clave
        solicitada, se propaga un KeyError.
    """

    # Extrae el valor de la categoría seleccionada
    # y cuenta sus apariciones en el dataset.
    categorias = Counter(
        salida[clave]
        for _, salida in datos
    )

    return categorias


# ============================================================
# 5. CATEGORÍAS PERMITIDAS
# ============================================================

# Conjunto de intenciones reconocidas
# por el clasificador municipal.
INTENCIONES_VALIDAS = {
    "consulta_estado",
    "nueva_solicitud",
    "cancelacion",
    "reclamo",
}

# Niveles de prioridad permitidos
# para cada solicitud.
PRIORIDADES_VALIDAS = {
    "baja",
    "media",
    "alta",
}


# ============================================================
# 6. VALIDACIÓN DEL DATASET
# ============================================================

def validar_dataset(
    ejemplos: list[types.TuningExample],
    claves_esperadas: tuple[str, ...] = ("intencion", "prioridad"),
) -> list[str]:
    """Valida la estructura de los ejemplos de entrenamiento.

    Recorre los ejemplos y comprueba que sus entradas
    y salidas cumplan las condiciones definidas.

    Las comprobaciones incluyen:

        - Texto de entrada no vacío.
        - Salida no vacía.
        - Ausencia de entradas duplicadas.
        - Salida con sintaxis JSON válida.
        - Salida representada como objeto JSON.
        - Presencia de las claves requeridas.
        - Intenciones pertenecientes al conjunto permitido.
        - Prioridades pertenecientes al conjunto permitido.

    Args:
        ejemplos (list[types.TuningExample]):
            Ejemplos de entrenamiento que serán validados.

        claves_esperadas (tuple[str, ...]):
            Claves que deben estar presentes en cada
            objeto JSON de salida.

            Por defecto:
                ("intencion", "prioridad")

    Returns:
        list[str]:
            Lista de problemas detectados.

            Cada mensaje identifica el índice
            del ejemplo y la condición incumplida.

            Una lista vacía indica que no se detectaron
            problemas mediante estas comprobaciones.

    Notes:
        La función no modifica los ejemplos originales.

        Los índices utilizados en los mensajes comienzan
        desde cero.

        La detección de duplicados compara literalmente
        los textos de entrada.

        No normaliza mayúsculas, espacios ni acentos
        antes de comparar las entradas.

        Cuando una salida está vacía o no contiene
        un JSON válido, se omiten las comprobaciones
        posteriores de esa salida.

        No realiza llamadas a Gemini.
    """

    # Almacena los problemas encontrados
    # durante la validación.
    problemas = []

    # Registra los textos de entrada ya examinados
    # para detectar duplicados.
    vistos = set()

    # Recorre los ejemplos conservando su índice.
    for i, ejemplo in enumerate(ejemplos):
        entrada = ejemplo.text_input
        salida_texto = ejemplo.output

        # ----------------------------------------------------
        # 6.1. VALIDACIÓN DE LA ENTRADA
        # ----------------------------------------------------

        # Detecta textos de entrada vacíos
        # o compuestos únicamente por espacios.
        if not entrada or not entrada.strip():
            problemas.append(f"ejemplo {i}: text_input vacío")

        # ----------------------------------------------------
        # 6.2. VALIDACIÓN DE LA SALIDA
        # ----------------------------------------------------

        # Detecta salidas vacías.
        #
        # Si no existe contenido, continúa directamente
        # con el siguiente ejemplo.
        if not salida_texto or not salida_texto.strip():
            problemas.append(f"ejemplo {i}: output vacío")
            continue

        # ----------------------------------------------------
        # 6.3. DETECCIÓN DE DUPLICADOS
        # ----------------------------------------------------

        # Comprueba si el texto de entrada ya apareció
        # en un ejemplo anterior.
        if entrada in vistos:
            problemas.append(f"ejemplo {i}: text_input duplicado")

        # Registra la entrada para las siguientes iteraciones.
        vistos.add(entrada)

        # ----------------------------------------------------
        # 6.4. VALIDACIÓN DE JSON
        # ----------------------------------------------------

        # Intenta interpretar la salida como JSON.
        try:
            salida = json.loads(salida_texto)

        except json.JSONDecodeError:
            # Registra el error de formato y evita
            # validar una estructura inexistente.
            problemas.append(f"ejemplo {i}: output no es JSON válido")
            continue

        # Comprueba que la salida sea un objeto JSON
        # representado mediante un diccionario.
        if not isinstance(salida, dict):
            problemas.append(f"ejemplo {i}: output debe ser un objeto JSON")
            continue

        # ----------------------------------------------------
        # 6.5. VALIDACIÓN DE CLAVES OBLIGATORIAS
        # ----------------------------------------------------

        # Comprueba que estén presentes todas
        # las claves requeridas.
        for clave in claves_esperadas:
            if clave not in salida:
                problemas.append(
                    f"ejemplo {i}: output no tiene la clave '{clave}'"
                )

        # ----------------------------------------------------
        # 6.6. VALIDACIÓN DE INTENCIÓN
        # ----------------------------------------------------

        # Si la salida contiene una intención,
        # verifica que pertenezca al conjunto permitido.
        if "intencion" in salida:
            if salida["intencion"] not in INTENCIONES_VALIDAS:
                problemas.append(
                    f"ejemplo {i}: intención no permitida"
                )

        # ----------------------------------------------------
        # 6.7. VALIDACIÓN DE PRIORIDAD
        # ----------------------------------------------------

        # Si la salida contiene una prioridad,
        # verifica que pertenezca al conjunto permitido.
        if "prioridad" in salida:
            if salida["prioridad"] not in PRIORIDADES_VALIDAS:
                problemas.append(
                    f"ejemplo {i}: prioridad no permitida"
                )

    # Devuelve todos los problemas acumulados.
    return problemas


# ============================================================
# 7. SEGUIMIENTO DE TRABAJOS DE TUNING
# ============================================================

def esperar_a_que_termine(
    client: genai.Client,
    nombre_trabajo: str,
    intervalo_segundos: int = 30,
) -> types.TuningJob:
    """Espera hasta que un trabajo de tuning alcance un estado final.

    Consulta periódicamente el estado de un trabajo
    existente mediante el cliente de Gemini.

    El proceso continúa hasta encontrar uno
    de los estados finales configurados.

    Args:
        client (genai.Client):
            Cliente del SDK de Gemini previamente
            inicializado y configurado.

        nombre_trabajo (str):
            Identificador del trabajo de tuning
            que se desea consultar.

        intervalo_segundos (int):
            Tiempo de espera entre consultas,
            expresado en segundos.

            Su valor predeterminado es 30.

    Returns:
        types.TuningJob:
            Objeto del trabajo cuando alcanza
            uno de los estados finales reconocidos.

    Raises:
        ValueError:
            Si intervalo_segundos es menor
            o igual que cero.

    Notes:
        Los estados finales reconocidos son:
            - JOB_STATE_SUCCEEDED
            - JOB_STATE_FAILED
            - JOB_STATE_CANCELLED
            - JOB_STATE_PARTIALLY_SUCCEEDED

        Esta función realiza consultas reales
        al servicio mediante client.tunings.get().

        No crea, modifica ni cancela trabajos de tuning.

        No establece un tiempo máximo de espera.

        Si el trabajo permanece en un estado no final,
        el ciclo continúa consultando indefinidamente,
        salvo interrupción o error externo.
    """

    # Comprueba que el intervalo de consulta
    # sea un valor positivo.
    if intervalo_segundos <= 0:
        raise ValueError("El intervalo debe ser mayor que cero")

    # Define los estados que permiten considerar
    # finalizado el seguimiento del trabajo.
    estados_finales = {
        types.JobState.JOB_STATE_SUCCEEDED,
        types.JobState.JOB_STATE_FAILED,
        types.JobState.JOB_STATE_CANCELLED,
        types.JobState.JOB_STATE_PARTIALLY_SUCCEEDED,
    }

    # Consulta el estado del trabajo hasta que
    # alcance una condición de finalización.
    while True:

        # Recupera el estado actualizado del trabajo.
        trabajo = client.tunings.get(name=nombre_trabajo)

        # Informa el estado recibido desde el servicio.
        print(f"Estado actual: {trabajo.state}")

        # Si el trabajo terminó, devuelve
        # el objeto obtenido desde el SDK.
        if trabajo.state in estados_finales:
            return trabajo

        # Espera antes de realizar una nueva consulta.
        time.sleep(intervalo_segundos)


# ============================================================
# 8. EJECUCIÓN LOCAL DE VALIDACIONES
# ============================================================

if __name__ == "__main__":
    # --------------------------------------------------------
    # 8.1. ANÁLISIS DEL BALANCE
    # --------------------------------------------------------

    # Cuenta los ejemplos según su intención.
    balance = chequear_balance(ejemplos_raw)

    print("\n--- BALANCE DEL DATASET ---")

    # Presenta las categorías ordenadas por frecuencia.
    for categoria, cantidad in balance.most_common():
        print(f"{categoria}: {cantidad}")

    # --------------------------------------------------------
    # 8.2. VALIDACIÓN DEL DATASET ORIGINAL
    # --------------------------------------------------------

    print(f"\nTotal de ejemplos: {len(ejemplos)}")
    print("\n--- VALIDACIÓN DEL DATASET ---")

    # Comprueba el formato de los ejemplos preparados
    # para el proceso de tuning.
    problemas = validar_dataset(ejemplos)

    # Presenta la cantidad de ejemplos
    # y los problemas detectados.
    print(
        f"{len(ejemplos)} ejemplos, "
        f"{len(problemas)} problemas encontrados"
    )

    # Muestra cada problema identificado.
    for problema in problemas:
        print("-", problema)

    # --------------------------------------------------------
    # 8.3. PRUEBA NEGATIVA
    # --------------------------------------------------------

    # Define ejemplos deliberadamente incorrectos
    # para comprobar las reglas de validación.
    #
    # Se incluyen:
    #     - Una entrada vacía.
    #     - Dos entradas con el mismo texto.
    #     - Una salida que no es JSON.
    #     - Una salida sin la clave prioridad.
    print("\n--- PRUEBA NEGATIVA ---")

    ejemplos_invalidos = [
        types.TuningExample(
            text_input="",
            output='{"intencion": "reclamo", "prioridad": "alta"}',
        ),
        types.TuningExample(
            text_input="Solicitud duplicada",
            output='{"intencion": "reclamo", "prioridad": "media"}',
        ),
        types.TuningExample(
            text_input="Solicitud duplicada",
            output='{"intencion": "reclamo", "prioridad": "baja"}',
        ),
        types.TuningExample(
            text_input="Quiero consultar mi trámite",
            output="Esto no es JSON",
        ),
        types.TuningExample(
            text_input="Necesito ingresar una solicitud",
            output='{"intencion": "nueva_solicitud"}',
        ),
    ]

    # Ejecuta la validación sobre el conjunto
    # de ejemplos deliberadamente incorrectos.
    problemas_negativos = validar_dataset(ejemplos_invalidos)

    # Informa la cantidad de problemas detectados.
    print(f"Problemas detectados: {len(problemas_negativos)}")

    # Presenta cada problema identificado.
    for problema in problemas_negativos:
        print("-", problema)
