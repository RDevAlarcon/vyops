
"""Pruebas de consistencia de respuestas estructuradas para VyOps.

Proyecto académico — Especialización en Desarrollo con IA Generativa.
Unidad 1 — Bloque 10: Ingeniería de prompts y consistencia.

Objetivo:
    Evaluar si Google Gemini genera respuestas JSON que cumplen
    las estructuras definidas en el banco de prompts de VyOps.

Metodología:
    Se ejecutan tres repeticiones de cada uno de los tres casos:
        1. Clasificación de solicitudes.
        2. Extracción de información.
        3. Priorización de solicitudes.

    Esto produce nueve consultas de evaluación en total.

Responsabilidades:
    1. Cargar los casos definidos en prompts/banco.py.
    2. Construir solicitudes con instrucciones y esquemas JSON.
    3. Enviar consultas mediante el cliente HTTP de Gemini.
    4. Interpretar las respuestas estructuradas.
    5. Validar tipos, valores permitidos y límites numéricos.
    6. Registrar los resultados exitosos y los errores.
    7. Guardar las evidencias después de cada consulta.
    8. Presentar un resumen de consistencia por prompt.

Persistencia:
    Los resultados se almacenan en registro_resultados.json.
    El archivo contiene el modelo, las fechas de ejecución
    y el resultado individual de cada prueba.

Fechas:
    Se registran marcas de tiempo en UTC y en la zona horaria
    America/Santiago para facilitar la revisión de evidencias.

Arquitectura:
    Reutiliza las funciones de src/consumir_gemini.py y los casos
    configurados en prompts/banco.py.

Alcance:
    Las pruebas verifican la estructura de las respuestas JSON.
    No constituyen una evaluación automática completa de su
    exactitud semántica ni de su calidad empresarial.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Serialización de resultados en formato JSON.
import json

# Configuración de rutas de importación de Python.
import sys

# Pausas entre consultas para controlar su frecuencia.
import time

# Manejo de fechas y marcas temporales en UTC.
from datetime import datetime, timezone

# Conversión de fechas a la zona horaria de Chile.
from zoneinfo import ZoneInfo

# Construcción de rutas independientes del sistema operativo.
from pathlib import Path


# ============================================================
# 2. CONFIGURACIÓN DE IMPORTACIONES DEL PROYECTO
# ============================================================

# Permite importar el cliente HTTP desde la carpeta src.

# Obtiene la raíz del proyecto a partir de la ubicación
# del archivo actual, situado dentro de prompts/.
RAIZ = Path(__file__).resolve().parents[1]

# Incorpora src/ al inicio de la búsqueda de módulos.
#
# Esto permite importar consumir_gemini directamente
# sin utilizar el prefijo src.
sys.path.insert(0, str(RAIZ / "src"))

# Funciones y configuración del cliente HTTP de Gemini.
#
# MODELO:
#     Identificador del modelo configurado.
#
# armar_peticion:
#     Construye la solicitud HTTP con las instrucciones,
#     el mensaje del usuario y el esquema de respuesta.
#
# enviar_peticion:
#     Envía la solicitud al servicio Gemini.
#
# extraer_texto:
#     Recupera el contenido textual de la respuesta.
#
# parsear_respuesta_json:
#     Interpreta la respuesta JSON y comprueba
#     las claves esperadas.
from consumir_gemini import (
    MODELO,
    armar_peticion,
    enviar_peticion,
    extraer_texto,
    parsear_respuesta_json,
)

# Banco de casos utilizado para evaluar
# la consistencia de los prompts.
from banco import BANCO_DE_PROMPTS


# ============================================================
# 3. PARÁMETROS DE EVALUACIÓN
# ============================================================

# Número de ejecuciones por cada prompt.
REPETICIONES = 3

# Tiempo de espera, en segundos, entre consultas.
PAUSA_ENTRE_CONSULTAS = 2

# Archivo JSON donde se conservará el registro acumulado.
#
# with_name() ubica el archivo en el mismo directorio
# que este módulo, independientemente del directorio
# desde el que se ejecute Python.
ARCHIVO_RESULTADOS = Path(__file__).with_name("registro_resultados.json")


# ============================================================
# 4. VALIDACIÓN DE RESPUESTAS ESTRUCTURADAS
# ============================================================

def validar_estructura(datos: dict, esquema: dict) -> None:
    """Valida los tipos y restricciones de una respuesta JSON.

    Recorre las propiedades definidas en el esquema y comprueba
    que los valores presentes cumplan las reglas configuradas.

    Validaciones realizadas:
        1. Tipos de datos: STRING, NUMBER, INTEGER, BOOLEAN,
           ARRAY y OBJECT.
        2. Valores permitidos mediante la propiedad enum.
        3. Límites numéricos mediante minimum y maximum.
        4. Rechazo de valores booleanos cuando se espera
           un número entero o decimal.

    Args:
        datos: Diccionario con la respuesta JSON interpretada.
        esquema: Diccionario con las propiedades y restricciones
            utilizadas para validar la respuesta.

    Returns:
        None. Si todas las comprobaciones se cumplen,
        la función finaliza sin devolver un valor.

    Raises:
        ValueError: Si el esquema contiene un tipo no reconocido,
            algún valor tiene un tipo incorrecto, no pertenece
            a las opciones permitidas o incumple un límite.

    Nota:
        Esta función valida únicamente las propiedades presentes
        en datos. No comprueba por sí misma que existan todas
        las claves obligatorias ni rechaza claves adicionales.

        La presencia de claves esperadas se comprueba previamente
        mediante parsear_respuesta_json().
    """

    # --------------------------------------------------------
    # 4.1. EQUIVALENCIA ENTRE TIPOS JSON Y PYTHON
    # --------------------------------------------------------

    # Diccionario de correspondencia entre los tipos
    # definidos en el esquema y los tipos de Python.
    #
    # NUMBER admite enteros y números decimales.
    # INTEGER admite únicamente enteros.
    tipos = {
        "STRING": str,
        "NUMBER": (int, float),
        "INTEGER": int,
        "BOOLEAN": bool,
        "ARRAY": list,
        "OBJECT": dict,
    }

    # --------------------------------------------------------
    # 4.2. RECORRIDO DE LAS PROPIEDADES DEL ESQUEMA
    # --------------------------------------------------------

    # Evalúa cada propiedad declarada en el esquema.
    #
    # Si properties no existe, utiliza un diccionario vacío.
    for clave, definicion in esquema.get("properties", {}).items():

        # Solo valida propiedades presentes en la respuesta.
        #
        # Las claves ausentes no generan errores aquí.
        if clave not in datos:
            continue

        # ----------------------------------------------------
        # 4.3. IDENTIFICACIÓN DEL TIPO ESPERADO
        # ----------------------------------------------------

        # Recupera el tipo declarado en el esquema.
        tipo_esperado = definicion.get("type")

        # Busca su correspondencia con un tipo de Python.
        tipo_python = tipos.get(tipo_esperado)

        # Rechaza tipos que no aparecen
        # en el diccionario de equivalencias.
        if tipo_python is None:
            raise ValueError(f"Tipo no reconocido: {tipo_esperado}")

        # Recupera el valor que será validado.
        valor = datos[clave]

        # ----------------------------------------------------
        # 4.4. VALIDACIÓN ESPECIAL DE BOOLEANOS
        # ----------------------------------------------------

        # En Python, bool es una subclase de int.
        #
        # Por ello, True y False podrían superar
        # una comprobación isinstance() de números.
        #
        # Esta condición evita aceptar booleanos
        # cuando se esperan NUMBER o INTEGER.
        if isinstance(valor, bool) and tipo_esperado in ("NUMBER", "INTEGER"):
            raise ValueError(f"Tipo incorrecto en '{clave}'.")

        # ----------------------------------------------------
        # 4.5. VALIDACIÓN DEL TIPO DE DATO
        # ----------------------------------------------------

        # Comprueba que el valor corresponda
        # al tipo declarado en el esquema.
        if not isinstance(valor, tipo_python):
            raise ValueError(f"Tipo incorrecto en '{clave}'.")

        # ----------------------------------------------------
        # 4.6. VALIDACIÓN DE VALORES PERMITIDOS
        # ----------------------------------------------------

        # Recupera las opciones admitidas mediante enum.
        opciones = definicion.get("enum")

        # Si el esquema define opciones, el valor
        # debe pertenecer al conjunto permitido.
        if opciones is not None and valor not in opciones:
            raise ValueError(f"Valor no permitido en '{clave}'.")

        # ----------------------------------------------------
        # 4.7. VALIDACIÓN DE LÍMITES NUMÉRICOS
        # ----------------------------------------------------

        # Validamos los límites numéricos definidos en el esquema.

        # Obtiene los límites configurados.
        #
        # Cuando no existe alguno, su valor será None.
        minimo = definicion.get("minimum")
        maximo = definicion.get("maximum")

        # Comprueba el límite inferior cuando está definido.
        if minimo is not None and valor < minimo:
            raise ValueError(
                f"El campo '{clave}' debe ser mayor o igual a {minimo}."
            )

        # Comprueba el límite superior cuando está definido.
        if maximo is not None and valor > maximo:
            raise ValueError(
                f"El campo '{clave}' debe ser menor o igual a {maximo}."
            )


# ============================================================
# 5. PERSISTENCIA DE RESULTADOS
# ============================================================

def guardar_resultados(registro: dict) -> None:
    """Guarda el registro acumulado de las pruebas de consistencia.

    Convierte el diccionario recibido a formato JSON y escribe
    su contenido en el archivo definido por ARCHIVO_RESULTADOS.

    Utiliza codificación UTF-8 para conservar correctamente
    los caracteres especiales y aplica una indentación de
    dos espacios para facilitar la lectura de la evidencia.

    Args:
        registro: Diccionario que contiene el modelo utilizado,
            las fechas de ejecución, las repeticiones configuradas
            y los resultados acumulados de las pruebas.

    Returns:
        None. El registro se almacena en un archivo JSON local.

    Raises:
        TypeError: Si el registro contiene valores que no pueden
            convertirse a JSON.
        OSError: Si ocurre un problema al escribir el archivo.

    Nota:
        Cada llamada sobrescribe el archivo con el registro
        completo recibido, no agrega información al final.

        ejecutar_pruebas() invoca esta función después de cada
        consulta para conservar los resultados acumulados.

        Esta función no realiza solicitudes a Gemini.
    """

    # Serializa el registro completo.
    #
    # ensure_ascii=False conserva caracteres Unicode.
    # indent=2 facilita la inspección manual.
    #
    # write_text() reemplaza el contenido anterior
    # del archivo con el estado acumulado actual.
    ARCHIVO_RESULTADOS.write_text(
        json.dumps(registro, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ============================================================
# 6. EJECUCIÓN DE PRUEBAS DE CONSISTENCIA
# ============================================================

def ejecutar_pruebas() -> None:
    """Ejecuta las pruebas de consistencia del banco de prompts.

    Inicializa un registro con el modelo utilizado y las fechas
    de ejecución en UTC y en la zona horaria de Santiago de Chile.

    Recorre los prompts definidos en BANCO_DE_PROMPTS y realiza
    la cantidad de repeticiones indicada por REPETICIONES.

    Para cada consulta:
        1. Construye una solicitud con instrucciones y esquema JSON.
        2. Envía la petición a Google Gemini.
        3. Extrae el texto de la respuesta.
        4. Convierte el texto en un diccionario JSON.
        5. Comprueba las claves esperadas y las restricciones.
        6. Registra el resultado exitoso o el error.
        7. Guarda la evidencia acumulada en un archivo JSON.

    Entre consultas aplica la pausa configurada, excepto
    después de la última ejecución.

    Al finalizar, muestra la cantidad de pruebas exitosas
    por cada prompt y la ubicación del archivo de evidencia.

    Returns:
        None. Los resultados se muestran en consola y se
        almacenan en registro_resultados.json.

    Manejo de errores:
        Captura ValueError y RuntimeError durante cada consulta.
        Si ocurre uno de estos errores, registra el fallo y
        continúa con la siguiente prueba.

    Advertencia:
        Esta función realiza consultas reales a Gemini y
        sobrescribe el archivo de evidencia al ejecutarse.
        No debe iniciarse durante una revisión documental.
    """

    # --------------------------------------------------------
    # 6.1. INICIALIZACIÓN DEL REGISTRO
    # --------------------------------------------------------

    # Crea la estructura principal de evidencia.
    #
    # Incluye:
    # - Modelo configurado.
    # - Fecha de inicio en UTC.
    # - Fecha de inicio en horario de Santiago.
    # - Cantidad de repeticiones por prompt.
    # - Lista inicialmente vacía de resultados.
    registro = {
        "modelo": MODELO,
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "fecha_chile": datetime.now(ZoneInfo("America/Santiago")).isoformat(),
        "repeticiones_por_prompt": REPETICIONES,
        "resultados": [],
    }

    # --------------------------------------------------------
    # 6.2. RECORRIDO DEL BANCO DE PROMPTS
    # --------------------------------------------------------

    # Evalúa cada caso definido en BANCO_DE_PROMPTS.
    for prompt in BANCO_DE_PROMPTS:

        # Obtiene el nombre utilizado para identificar
        # el caso dentro del registro de evaluación.
        nombre = prompt["nombre"]

        # Informa qué prompt está siendo evaluado.
        print(f"\nEvaluando: {nombre}")

        # ----------------------------------------------------
        # 6.3. REPETICIONES DEL CASO
        # ----------------------------------------------------

        # Ejecuta cada prompt REPETICIONES veces.
        #
        # El rango comienza en uno para facilitar
        # la identificación de las pruebas.
        for numero in range(1, REPETICIONES + 1):

            # Inicializa el resultado de la repetición.
            #
            # El estado comienza en False y solo cambia
            # a True después de completar las validaciones.
            prueba = {
                "prompt": nombre,
                "repeticion": numero,
                "exito": False,
            }

            try:
                # --------------------------------------------
                # 6.4. CONSTRUCCIÓN DE LA PETICIÓN
                # --------------------------------------------

                # Prepara la solicitud HTTP con:
                # - Ejemplo de entrada del usuario.
                # - Instrucción de sistema.
                # - Esquema JSON esperado.
                url, encabezados, cuerpo = armar_peticion(
                    prompt["ejemplo_usuario"],
                    prompt["system_instruction"],
                    prompt["response_schema"],
                )

                # --------------------------------------------
                # 6.5. CONSULTA AL MODELO GEMINI
                # --------------------------------------------

                # Envía la solicitud al proveedor.
                respuesta = enviar_peticion(url, encabezados, cuerpo)

                # Extrae el texto generado por el modelo.
                texto = extraer_texto(respuesta)

                # --------------------------------------------
                # 6.6. INTERPRETACIÓN DE LA RESPUESTA JSON
                # --------------------------------------------

                # Convierte la respuesta en datos estructurados
                # y comprueba las claves esperadas.
                datos = parsear_respuesta_json(
                    texto,
                    prompt["claves_esperadas"],
                )

                # --------------------------------------------
                # 6.7. VALIDACIÓN DEL ESQUEMA
                # --------------------------------------------

                # Comprueba tipos, opciones permitidas
                # y límites definidos en el esquema.
                validar_estructura(datos, prompt["response_schema"])

                # --------------------------------------------
                # 6.8. REGISTRO DE ÉXITO
                # --------------------------------------------

                # Marca la prueba como exitosa
                # después de superar las validaciones.
                prueba["exito"] = True

                # Conserva la respuesta interpretada
                # para su revisión posterior.
                prueba["respuesta"] = datos

                # Informa el resultado en consola.
                print(f"  Prueba {numero}: OK")

            # ------------------------------------------------
            # 6.9. MANEJO DE ERRORES DE EVALUACIÓN
            # ------------------------------------------------

            # Captura errores de validación y ejecución
            # representados por ValueError o RuntimeError.
            #
            # Otros tipos de excepciones no se capturan aquí.
            except (ValueError, RuntimeError) as error:

                # Conserva el mensaje de error
                # dentro del resultado de la prueba.
                prueba["error"] = str(error)

                # Informa el fallo en consola.
                print(f"  Prueba {numero}: ERROR - {error}")

            # ------------------------------------------------
            # 6.10. PERSISTENCIA INCREMENTAL
            # ------------------------------------------------

            # Incorpora el resultado de la repetición
            # al registro acumulado.
            registro["resultados"].append(prueba)

            # Guarda el registro completo después
            # de cada consulta, incluso si falló.
            guardar_resultados(registro)

            # ------------------------------------------------
            # 6.11. CONTROL DE PAUSAS ENTRE CONSULTAS
            # ------------------------------------------------

            # Esperamos entre todas las consultas, incluso
            # cuando pasamos de un prompt al siguiente.

            # Calcula el número total de consultas previstas.
            total_consultas = len(BANCO_DE_PROMPTS) * REPETICIONES

            # Obtiene la cantidad de pruebas ya registradas.
            consultas_realizadas = len(registro["resultados"])

            # No esperamos después de la última consulta.
            if consultas_realizadas < total_consultas:

                # Informa el tiempo de espera configurado.
                print(
                    f"  Esperando {PAUSA_ENTRE_CONSULTAS} segundos "
                    "antes de la siguiente consulta..."
                )

                # Suspende temporalmente la ejecución
                # antes de iniciar la próxima consulta.
                time.sleep(PAUSA_ENTRE_CONSULTAS)

    # ========================================================
    # 7. RESUMEN DE CONSISTENCIA
    # ========================================================

    # Presenta el encabezado del resumen final.
    print("\nResumen de consistencia:")

    # --------------------------------------------------------
    # 7.1. CÁLCULO DE ÉXITOS POR PROMPT
    # --------------------------------------------------------

    # Recorre nuevamente el banco de prompts
    # para calcular sus resultados individuales.
    for prompt in BANCO_DE_PROMPTS:

        # Filtra las pruebas asociadas al prompt actual.
        pruebas = [
            resultado
            for resultado in registro["resultados"]
            if resultado["prompt"] == prompt["nombre"]
        ]

        # Cuenta las pruebas cuyo estado exito es True.
        #
        # En Python, los booleanos pueden sumarse:
        # True equivale a uno y False equivale a cero.
        exitos = sum(resultado["exito"] for resultado in pruebas)

        # Presenta la cantidad de pruebas exitosas
        # respecto al total de repeticiones configurado.
        print(f"  {prompt['nombre']}: {exitos}/{REPETICIONES}")

    # --------------------------------------------------------
    # 7.2. UBICACIÓN DE LA EVIDENCIA
    # --------------------------------------------------------

    # Informa la ruta del archivo JSON
    # que contiene los resultados acumulados.
    print(f"\nEvidencia guardada en: {ARCHIVO_RESULTADOS}")


# ============================================================
# 8. PUNTO DE ENTRADA
# ============================================================

# Punto de entrada: pruebas de consistencia de prompts de VyOps.
#
# Este bloque se ejecuta únicamente cuando el archivo se inicia
# directamente desde la terminal.
#
# Al llamar a ejecutar_pruebas():
#   1. Carga los tres casos del banco de prompts.
#   2. Ejecuta tres consultas por cada caso (nueve en total).
#   3. Valida las respuestas JSON y sus restricciones.
#   4. Registra los resultados exitosos y los errores.
#   5. Guarda las evidencias en registro_resultados.json.
#   6. Muestra un resumen de consistencia por prompt.
#
# ADVERTENCIA:
# La ejecución realiza consultas reales a Google Gemini y
# sobrescribe el archivo de evidencia existente.
#
# Importar este módulo no ejecuta automáticamente las pruebas.

if __name__ == "__main__":
    ejecutar_pruebas()
