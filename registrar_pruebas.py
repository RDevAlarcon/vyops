"""Generador del registro de pruebas HTTP de VyOps.

Verifica la cobertura mínima de la matriz compartida,
ejecuta los casos contra el servicio HTTP y genera
un registro reproducible en formato Markdown.
"""

import json
import sys
from datetime import date
from pathlib import Path

import httpx2

from casos import CASOS, ejecutar_caso


RUTA = Path("docs/registro_pruebas.md")

URL_PREDETERMINADA = "http://127.0.0.1:8000"

ESTADOS_OBLIGATORIOS = (404, 405, 422)

COLUMNAS = (
    "Caso",
    "Descripción",
    "Petición",
    "Esperado",
    "Obtenido",
    "Resultado",
)


def verificar_cobertura(casos: list[dict]) -> list[str]:
    """Comprueba los requisitos mínimos de cobertura."""

    errores = []

    validos = [
        caso for caso in casos
        if caso["id"].startswith("V-")
    ]

    invalidos = [
        caso for caso in casos
        if caso["id"].startswith("I-")
    ]

    if len(validos) < 3:
        errores.append(
            "Se requieren al menos 3 casos válidos."
        )

    if len(invalidos) < 5:
        errores.append(
            "Se requieren al menos 5 casos inválidos."
        )

    estados = {
        caso["estado"]
        for caso in invalidos
    }

    for estado in ESTADOS_OBLIGATORIOS:
        if estado not in estados:
            errores.append(
                f"Falta un caso inválido con HTTP {estado}."
            )

    return errores


def limpiar_celda(valor: str) -> str:
    """Evita que el contenido altere la tabla Markdown."""

    return (
        valor.replace("|", "/")
        .replace("\r", " ")
        .replace("\n", " ")
    )


def describir(caso: dict) -> str:
    """Construye una descripción breve de la petición."""

    peticion = f"{caso['metodo']} {caso['ruta']}"

    if "contenido" in caso:
        cuerpo = caso["contenido"]

    elif caso.get("json") is not None:
        cuerpo = json.dumps(
            caso["json"],
            ensure_ascii=False,
        )

    else:
        cuerpo = ""

    # Solo se describen entradas sintéticas de la matriz.
    # No se incorporan cuerpos de respuesta del servidor.
    if cuerpo:
        if len(cuerpo) > 40:
            cuerpo = cuerpo[:40] + "..."

        peticion += f" {cuerpo}"

    return limpiar_celda(peticion)


def registrar(base_url: str) -> tuple[int, int]:
    """Ejecuta los casos y genera el registro Markdown."""

    errores = verificar_cobertura(CASOS)

    if errores:
        raise ValueError("; ".join(errores))

    filas = []

    with httpx2.Client(
        base_url=base_url,
        timeout=10.0,
    ) as cliente:

        for caso in CASOS:
            ok, estado, _ = ejecutar_caso(
                cliente,
                caso,
            )

            filas.append((caso, ok, estado))

    cumplidos = sum(
        int(ok)
        for _, ok, _ in filas
    )

    total = len(filas)

    lineas = [
        "# Registro de pruebas de la API",
        "",
        f"Fecha: {date.today().isoformat()}",
        "",
        f"Servicio probado: {base_url}",
        "",
        "Cliente HTTP: httpx2",
        "",
        "Modo declarado: SIMULADO",
        "",
        "Alcance: contrato HTTP con lógica documental controlada.",
        "",
        f"Resultado: {cumplidos} de {total} casos cumplidos.",
        "",
        "| " + " | ".join(COLUMNAS) + " |",
        "| " + " | ".join(
            ["---"] * len(COLUMNAS)
        ) + " |",
    ]

    for caso, ok, estado in filas:

        valores = (
            caso["id"],
            limpiar_celda(caso["descripcion"]),
            describir(caso),
            str(caso["estado"]),
            str(estado),
            "PASA" if ok else "FALLA",
        )

        lineas.append(
            "| " + " | ".join(valores) + " |"
        )

    lineas.extend([
        "",
        "## Resultado final",
        "",
        "PASS" if cumplidos == total else "FAIL",
        "",
        "El registro no certifica la precisión ni el "
        "rendimiento del RAG real.",
        "",
    ])

    # Crear el directorio únicamente si no existe.
    RUTA.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Sobrescribir el registro con la ejecución actual.
    RUTA.write_text(
        "\n".join(lineas),
        encoding="utf-8",
    )

    return cumplidos, total


def main() -> int:
    """Controla la ejecución y el código de salida."""

    base_url = (
        sys.argv[1]
        if len(sys.argv) > 1
        else URL_PREDETERMINADA
    )

    errores = verificar_cobertura(CASOS)

    if errores:
        print("COBERTURA INSUFICIENTE")

        for error in errores:
            print(f"- {error}")

        print("No se generó un nuevo registro.")

        return 1

    print("=== REGISTRO DE PRUEBAS VYOPS ===")
    print(f"Servicio: {base_url}")
    print("Cobertura: PASS")
    print("Modo declarado: SIMULADO")

    try:
        cumplidos, total = registrar(base_url)

    except httpx2.ConnectError:
        print("No fue posible conectar con el servicio.")
        print("No se generó un nuevo registro.")
        return 1

    except httpx2.RequestError:
        print("Error de comunicación con el servicio.")
        print("No se generó un nuevo registro.")
        return 1

    except OSError:
        print("No fue posible escribir el registro.")
        return 1

    print(
        f"Registro escrito en {RUTA.as_posix()}: "
        f"{cumplidos} de {total} casos cumplidos."
    )

    resultado = cumplidos == total

    print(
        "RESULTADO: PASS"
        if resultado
        else "RESULTADO: FAIL"
    )

    return 0 if resultado else 1


if __name__ == "__main__":
    sys.exit(main())