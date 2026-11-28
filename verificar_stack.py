
"""Verifica el despliegue de VyOps mediante Docker Compose.

Ejecuta las siete comprobaciones del stack en modo simulado,
sin consumir Gemini ni utilizar credenciales reales.
"""

import json
import os
import subprocess
from pathlib import Path

import httpx2

from casos import CASOS, PREGUNTA_DOCUMENTAL, FUENTE_ESPERADA, ejecutar_caso


BASE_DIR = Path(__file__).resolve().parent

API_URL = "http://127.0.0.1:8000"
INTERFAZ_URL = "http://127.0.0.1:8080"

COMPOSE = [
    "docker",
    "compose",
    "--env-file",
    ".env.example",
    "-f",
    "compose.yaml",
    "-f",
    "compose.pruebas.yaml",
]


def compose(*argumentos, timeout=60):
    """Ejecuta Docker Compose sin utilizar la clave real."""

    entorno = os.environ.copy()
    entorno["GEMINI_API_KEY"] = ""
    entorno["ENTORNO"] = "desarrollo"

    return subprocess.run(
        [*COMPOSE, *argumentos],
        cwd=BASE_DIR,
        env=entorno,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )


def verificar_configuracion():
    """STK-1: comprueba la validez de Docker Compose."""

    resultado = compose("config", "--quiet")
    return resultado.returncode == 0


def verificar_arranque():
    """STK-2: construye y espera el arranque de los servicios."""

    resultado = compose(
        "up",
        "-d",
        "--build",
        "--wait",
        "--wait-timeout",
        "120",
        timeout=600,
    )

    return resultado.returncode == 0


def verificar_contenedores():
    """STK-3: comprueba que ambos servicios estén saludables."""

    resultado = compose("ps", "--format", "json")

    if resultado.returncode != 0:
        return False

    salida = resultado.stdout.strip()

    if not salida:
        return False

    # Compose puede devolver un arreglo JSON o un objeto por línea.
    if salida.startswith("["):
        contenedores = json.loads(salida)
    else:
        contenedores = [
            json.loads(linea)
            for linea in salida.splitlines()
            if linea.strip()
        ]

    servicios = {
        contenedor.get("Service")
        for contenedor in contenedores
    }

    return (
        servicios == {"api", "interfaz"}
        and len(contenedores) == 2
        and all(
            contenedor.get("State") == "running"
            and contenedor.get("Health") == "healthy"
            for contenedor in contenedores
        )
    )


def verificar_api():
    """STK-4: comprueba la disponibilidad HTTP de la API."""

    with httpx2.Client(timeout=10, trust_env=False) as cliente:
        respuesta = cliente.get(f"{API_URL}/salud")

        return (
            respuesta.status_code == 200
            and respuesta.json().get("estado") == "ok"
        )


def verificar_interfaz():
    """STK-5: ejecuta una consulta documental desde la interfaz."""

    with httpx2.Client(timeout=40, trust_env=False) as cliente:
        respuesta = cliente.get(
            f"{INTERFAZ_URL}/preguntar",
            params={"texto": PREGUNTA_DOCUMENTAL},
        )

        if respuesta.status_code != 200:
            return False

        datos = respuesta.json()

        return (
            datos.get("estado") == "respuesta_generada"
            and FUENTE_ESPERADA in datos.get("fuentes", [])
        )


def verificar_casos():
    """STK-6: reutiliza los casos existentes del contrato HTTP."""

    aprobados = 0

    with httpx2.Client(
        base_url=API_URL,
        timeout=10,
        trust_env=False,
    ) as cliente:

        for caso in CASOS:
            try:
                correcto, estado, _ = ejecutar_caso(cliente, caso)

                if correcto:
                    aprobados += 1

                resultado = "PASA" if correcto else "FALLA"

                print(
                    f"    {caso['id']}: {resultado} "
                    f"(HTTP {estado})"
                )

            except httpx2.HTTPError:
                print(f"    {caso['id']}: FALLA (error HTTP)")

    print(f"    Casos aprobados: {aprobados}/{len(CASOS)}")

    return bool(CASOS) and aprobados == len(CASOS)


def verificar_apagado():
    """STK-7: elimina los servicios y comprueba su ausencia."""

    resultado = compose("down", timeout=120)

    if resultado.returncode != 0:
        return False

    contenedores = compose("ps", "--all", "--quiet")

    return (
        contenedores.returncode == 0
        and not contenedores.stdout.strip()
    )


def comprobar(id_prueba, descripcion, funcion):
    """Ejecuta una comprobación sin exponer datos sensibles."""

    try:
        correcto = funcion()

    except Exception as error:
        correcto = False
        print(f"    Error: {type(error).__name__}")

    resultado = "PASA" if correcto else "FALLA"

    print(f"{id_prueba} | {descripcion}: {resultado}")

    return correcto


def main():
    """Orquesta las siete comprobaciones y garantiza el intento de limpieza."""

    print("=== VERIFICACION DEL STACK VYOPS ===")
    print("Modo: SIMULADO")
    print("Consumo de Gemini: deshabilitado\n")

    # Evita detener una composición que ya estaba en funcionamiento.
    try:
        existentes = compose("ps", "--all", "--quiet")

        if existentes.returncode != 0:
            print("No se pudo comprobar el estado inicial.")
            return 1

        if existentes.stdout.strip():
            print("Existen contenedores de VyOps.")
            print("Detén la composición antes de verificarla.")
            return 1

    except Exception as error:
        print(f"Error inicial: {type(error).__name__}")
        return 1

    resultados = []

    try:
        configuracion = comprobar(
            "STK-1",
            "Configuracion de Compose",
            verificar_configuracion,
        )
        resultados.append(configuracion)

        if configuracion:
            arranque = comprobar(
                "STK-2",
                "Construccion y arranque",
                verificar_arranque,
            )
            resultados.append(arranque)

            if arranque:
                comprobaciones = [
                    (
                        "STK-3",
                        "Contenedores saludables",
                        verificar_contenedores,
                    ),
                    (
                        "STK-4",
                        "Disponibilidad de la API",
                        verificar_api,
                    ),
                    (
                        "STK-5",
                        "Consulta desde la interfaz",
                        verificar_interfaz,
                    ),
                    (
                        "STK-6",
                        "Casos del contrato HTTP",
                        verificar_casos,
                    ),
                ]

                for id_prueba, descripcion, funcion in comprobaciones:
                    resultados.append(
                        comprobar(id_prueba, descripcion, funcion)
                    )

    finally:
        resultados.append(
            comprobar(
                "STK-7",
                "Apagado limpio",
                verificar_apagado,
            )
        )

    aprobados = sum(resultados)

    print(f"\nResultado final: {aprobados}/7")

    return 0 if aprobados == 7 else 1


if __name__ == "__main__":
    raise SystemExit(main())
