
"""Pruebas de consistencia del banco de prompts de VyOps.

Unidad U1.3 — Bloque 10.

Ejecuta tres consultas por prompt, valida las respuestas JSON
y guarda los resultados como evidencia de la actividad.
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
    """Comprueba los tipos y valores definidos en el esquema JSON."""
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
    """Guarda la evidencia acumulada después de cada consulta."""
    ARCHIVO_RESULTADOS.write_text(
        json.dumps(registro, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def ejecutar_pruebas() -> None:
    """Ejecuta el banco de prompts y registra cada resultado."""
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


if __name__ == "__main__":
    ejecutar_pruebas()
