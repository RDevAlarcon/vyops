
"""Verifica la ausencia de secretos en el repositorio y la imagen Docker."""

import json
import re
import subprocess
import sys
from pathlib import Path

from dotenv import variables


BASE_DIR = Path(__file__).resolve().parent

PATRON_GOOGLE = re.compile(r"AIza[0-9A-Za-z_-]{35}")

PATRON_ASIGNACION = re.compile(
    r"""(?m)^[ \t]*(?:export[ \t]+)?"""
    r"""([A-Z_][A-Z0-9_]*)[ \t]*=[ \t]*([^\r\n]*)"""
)

PATRON_NOMBRE_SECRETO = re.compile(
    r"KEY|TOKEN|SECRET|PASSWORD"
)


def ejecutar_comando(*argumentos):
    """Ejecuta un comando sin exponer su salida en pantalla."""
    return subprocess.run(
        argumentos,
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def contiene_secreto(contenido, formato_python=False):
    """Detecta claves de Google y asignaciones de secretos literales."""
    if PATRON_GOOGLE.search(contenido):
        return True

    for coincidencia in PATRON_ASIGNACION.finditer(contenido):
        nombre, valor = coincidencia.groups()

        if not PATRON_NOMBRE_SECRETO.search(nombre):
            continue

        valor = valor.strip()

        if formato_python:
            literal = re.match(r"""^(['"])(.*?)\1""", valor)
            if not literal:
                continue
            valor = literal.group(2)
        else:
            valor = valor.strip("'\"")

        if not valor or valor.startswith(("$", "#")):
            continue

        return True

    return False


def sec_1():
    """Comprueba los archivos versionados y no ignorados del repositorio."""
    resultado = ejecutar_comando(
        "git", "ls-files", "-z",
        "--cached", "--others", "--exclude-standard",
    )

    if resultado.returncode != 0:
        return False, "No fue posible listar los archivos"

    encontrados = []

    for nombre in sorted(set(resultado.stdout.split("\0"))):
        if not nombre:
            continue

        ruta = BASE_DIR / nombre

        # El archivo local de credenciales se comprueba en SEC-2 y SEC-3.
        if ruta.name == ".env" or not ruta.is_file():
            continue

        datos = ruta.read_bytes()

        if b"\0" in datos:
            continue

        contenido = datos.decode("utf-8", errors="replace")

        if contiene_secreto(contenido, ruta.suffix == ".py"):
            encontrados.append(nombre)

    if encontrados:
        return False, "Revisar: " + ", ".join(encontrados)

    return True, "Sin secretos detectados en el repositorio"


def sec_2():
    """Comprueba que Git ignore el archivo .env."""
    resultado = ejecutar_comando("git", "check-ignore", "-q", ".env")

    return (
        resultado.returncode == 0,
        "Proteccion de .env mediante .gitignore",
    )


def sec_3():
    """Comprueba que .env no forme parte del repositorio."""
    resultado = ejecutar_comando("git", "ls-files", "--", ".env")

    return (
        resultado.returncode == 0 and not resultado.stdout.strip(),
        "Archivo .env no versionado",
    )


def sec_4():
    """Comprueba que el archivo de ejemplo no contenga secretos."""
    ruta = BASE_DIR / ".env.example"

    if not ruta.is_file():
        return False, "No existe .env.example"

    contenido = ruta.read_text(encoding="utf-8-sig")

    return (
        not contiene_secreto(contenido),
        "Archivo .env.example sin credenciales",
    )


def sec_5(imagen):
    """Inspecciona las variables y el historial de la imagen Docker."""
    inspeccion = ejecutar_comando(
        "docker", "image", "inspect",
        "--format", "{{json .Config.Env}}", imagen,
    )

    historial = ejecutar_comando(
        "docker", "history", "--no-trunc",
        "--format", "{{.CreatedBy}}", imagen,
    )

    if inspeccion.returncode != 0 or historial.returncode != 0:
        return False, "No fue posible inspeccionar la imagen"

    variables = json.loads(inspeccion.stdout)

    # La imagen oficial de Python utiliza una huella GPG publica.
    variables = [
        variable
        for variable in (variables or [])
        if not re.fullmatch(r"GPG_KEY=[A-Fa-f0-9]{40}", variable)
    ]

    if contiene_secreto("\n".join(variables)):
        return False, "Secreto detectado en las variables de la imagen"

    if PATRON_GOOGLE.search(historial.stdout):
        return False, "Clave detectada en el historial"

    for coincidencia in re.finditer(
        r"""([A-Z_][A-Z0-9_]*)=([^\s;]+)""",
        historial.stdout,
    ):
        nombre, valor = coincidencia.groups()
        valor = valor.strip("'\"")
        # Una huella GPG publica no constituye una credencial.
        if nombre == "GPG_KEY" and re.fullmatch(r"[A-Fa-f0-9]{40}", valor):
            continue
        if (
            PATRON_NOMBRE_SECRETO.search(nombre)
            and valor
            and not valor.startswith("$")
        ):
            return False, "Secreto detectado en el historial"

    return True, "Sin secretos detectados en la imagen"


def main():
    """Ejecuta las cinco comprobaciones de seguridad."""
    imagen = sys.argv[1] if len(sys.argv) > 1 else "vyops:0.3"

    comprobaciones = [
        ("SEC-1", sec_1),
        ("SEC-2", sec_2),
        ("SEC-3", sec_3),
        ("SEC-4", sec_4),
        ("SEC-5", lambda: sec_5(imagen)),
    ]

    aprobadas = 0

    print("=== VERIFICACION DE SECRETOS VYOPS ===")

    for codigo, comprobar in comprobaciones:
        try:
            aprobado, detalle = comprobar()
        except Exception:
            aprobado = False
            detalle = "No fue posible completar la comprobacion"

        aprobadas += int(aprobado)
        estado = "PASA" if aprobado else "FALLA"

        print(f"{estado} {codigo} -> {detalle}")

    print(f"\n{aprobadas} de 5 comprobaciones cumplidas")
    print("RESULTADO:", "PASS" if aprobadas == 5 else "FAIL")

    return 0 if aprobadas == 5 else 1


if __name__ == "__main__":
    sys.exit(main())
