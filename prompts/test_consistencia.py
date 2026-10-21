

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

import json
import sys
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

# Permite importar el cliente HTTP desde la carpeta src.
RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from consumir_gemini import (
    MODELO,
    armar_peticion,
    enviar_peticion,
    extraer_texto,
    parsear_respuesta_json,
)

from banco import BANCO_DE_PROMPTS


REPETICIONES = 3
PAUSA_ENTRE_CONSULTAS = 2
ARCHIVO_RESULTADOS = Path(__file__).with_name("registro_resultados.json")


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

    tipos = {
        "STRING": str,
        "NUMBER": (int, float),
        "INTEGER": int,
        "BOOLEAN": bool,
        "ARRAY": list,
        "OBJECT": dict,
    }

    for clave, definicion in esquema.get("properties", {}).items():
        if clave not in datos:
            continue

        tipo_esperado = definicion.get("type")
        tipo_python = tipos.get(tipo_esperado)

        if tipo_python is None:
            raise ValueError(f"Tipo no reconocido: {tipo_esperado}")

        valor = datos[clave]

        if isinstance(valor, bool) and tipo_esperado in ("NUMBER", "INTEGER"):
            raise ValueError(f"Tipo incorrecto en '{clave}'.")

        if not isinstance(valor, tipo_python):
            raise ValueError(f"Tipo incorrecto en '{clave}'.")

        opciones = definicion.get("enum")
        if opciones is not None and valor not in opciones:
            raise ValueError(f"Valor no permitido en '{clave}'.")

        # Validamos los límites numéricos definidos en el esquema.
        minimo = definicion.get("minimum")
        maximo = definicion.get("maximum")

        if minimo is not None and valor < minimo:
            raise ValueError(
                f"El campo '{clave}' debe ser mayor o igual a {minimo}."
            )

        if maximo is not None and valor > maximo:
            raise ValueError(
                f"El campo '{clave}' debe ser menor o igual a {maximo}."
            )


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

    ARCHIVO_RESULTADOS.write_text(
        json.dumps(registro, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


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

    registro = {
        "modelo": MODELO,
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "fecha_chile": datetime.now(ZoneInfo("America/Santiago")).isoformat(),
        "repeticiones_por_prompt": REPETICIONES,
        "resultados": [],
    }

    for prompt in BANCO_DE_PROMPTS:
        nombre = prompt["nombre"]
        print(f"\nEvaluando: {nombre}")

        for numero in range(1, REPETICIONES + 1):
            prueba = {
                "prompt": nombre,
                "repeticion": numero,
                "exito": False,
            }

            try:
                url, encabezados, cuerpo = armar_peticion(
                    prompt["ejemplo_usuario"],
                    prompt["system_instruction"],
                    prompt["response_schema"],
                )

                respuesta = enviar_peticion(url, encabezados, cuerpo)
                texto = extraer_texto(respuesta)

                datos = parsear_respuesta_json(
                    texto,
                    prompt["claves_esperadas"],
                )

                validar_estructura(datos, prompt["response_schema"])

                prueba["exito"] = True
                prueba["respuesta"] = datos
                print(f"  Prueba {numero}: OK")

            except (ValueError, RuntimeError) as error:
                prueba["error"] = str(error)
                print(f"  Prueba {numero}: ERROR - {error}")


            registro["resultados"].append(prueba)
            guardar_resultados(registro)

            # Esperamos entre todas las consultas, incluso
            # cuando pasamos de un prompt al siguiente.
            total_consultas = len(BANCO_DE_PROMPTS) * REPETICIONES
            consultas_realizadas = len(registro["resultados"])

            # No esperamos después de la última consulta.
            if consultas_realizadas < total_consultas:
                print(
                    f"  Esperando {PAUSA_ENTRE_CONSULTAS} segundos "
                    "antes de la siguiente consulta..."
                )
                time.sleep(PAUSA_ENTRE_CONSULTAS)


    print("\nResumen de consistencia:")

    for prompt in BANCO_DE_PROMPTS:
        pruebas = [
            resultado
            for resultado in registro["resultados"]
            if resultado["prompt"] == prompt["nombre"]
        ]
        exitos = sum(resultado["exito"] for resultado in pruebas)
        print(f"  {prompt['nombre']}: {exitos}/{REPETICIONES}")

    print(f"\nEvidencia guardada en: {ARCHIVO_RESULTADOS}")


# ---------------------------------------------------------------------------
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
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    ejecutar_pruebas()
