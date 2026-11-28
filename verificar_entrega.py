"""Verifica los requisitos de entrega de la Unidad 3.3 de VyOps."""

import json
import re
import subprocess
import sys
from pathlib import Path

import yaml


BASE_DIR = Path(__file__).resolve().parent

ENCABEZADOS_OBLIGATORIOS = (
    "Requisitos",
    "Configuración",
    "Cómo arrancar",
    "Cómo comprobar que funciona",
    "Cómo detener",
    "Problemas frecuentes",
)

ARCHIVOS_OBLIGATORIOS = (
    "compose.yaml",
    "Dockerfile",
    ".dockerignore",
    "interfaz/Dockerfile",
    "interfaz/.dockerignore",
    ".env.example",
    ".gitignore",
    "README.md",
    "verificar_dockerfile.py",
    "verificar_stack.py",
    "buscar_secretos.py",
    "verificar_entrega.py",
    "docs/verificacion_cruzada.md",
)


def leer_archivo(nombre):
    """Lee un archivo del proyecto utilizando UTF-8."""
    return (BASE_DIR / nombre).read_text(encoding="utf-8-sig")


def ejecutar_comando(*argumentos):
    """Ejecuta un comando desde la raíz del proyecto."""
    return subprocess.run(
        argumentos,
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        check=False,
    )


def cargar_compose():
    """Carga la composición declarada en el repositorio."""
    return yaml.safe_load(leer_archivo("compose.yaml"))


def ent_1():
    """Comprueba la validez, los servicios y sus dependencias."""
    resultado = ejecutar_comando(
        "docker",
        "compose",
        "--env-file",
        ".env.example",
        "config",
        "--quiet",
    )

    if resultado.returncode != 0:
        return False, "La configuracion de Compose no es valida"

    servicios = cargar_compose().get("services", {})

    if len(servicios) < 2:
        return False, "Se requieren al menos dos servicios"

    dependencias = False

    for nombre, servicio in servicios.items():
        declaradas = servicio.get("depends_on", {})

        for dependencia in declaradas:
            if dependencia not in servicios or dependencia == nombre:
                return False, "Existe una dependencia invalida"

            dependencias = True

    if not dependencias:
        return False, "No existen dependencias entre servicios"

    return True, f"Composicion valida con {len(servicios)} servicios"


def ent_2():
    """Comprueba los seis encabezados obligatorios del README."""
    contenido = leer_archivo("README.md")

    encabezados = set(
        re.findall(r"^##[ \t]+(.+?)\s*$", contenido, re.MULTILINE)
    )

    faltantes = [
        encabezado
        for encabezado in ENCABEZADOS_OBLIGATORIOS
        if encabezado not in encabezados
    ]

    if faltantes:
        return False, "Encabezados faltantes: " + ", ".join(faltantes)

    return True, "Los seis encabezados obligatorios estan presentes"


def ent_3():
    """Comprueba que las variables de entorno estén documentadas."""
    readme = leer_archivo("README.md")
    ejemplo = leer_archivo(".env.example")
    compose = cargar_compose()

    # Obtiene las variables declaradas en la plantilla.
    variables = set(
        re.findall(
            r"^[ \t]*([A-Z_][A-Z0-9_]*)[ \t]*=",
            ejemplo,
            re.MULTILINE,
        )
    )

    # Incluye las variables declaradas directamente en los servicios.
    for servicio in compose.get("services", {}).values():
        entorno = servicio.get("environment", {})

        if isinstance(entorno, dict):
            variables.update(entorno.keys())

        elif isinstance(entorno, list):
            variables.update(
                variable.split("=", 1)[0]
                for variable in entorno
            )

    # Incluye las variables utilizadas en interpolaciones de Compose.
    variables.update(
        re.findall(
            r"\$\{([A-Z_][A-Z0-9_]*)",
            leer_archivo("compose.yaml"),
        )
    )

    faltantes = [
        variable
        for variable in sorted(variables)
        if not re.search(
            rf"\b{re.escape(variable)}\b",
            readme,
        )
    ]

    if faltantes:
        return False, "Variables sin documentar: " + ", ".join(faltantes)

    return True, f"{len(variables)} variables documentadas"


def ent_4():
    """Comprueba la existencia de los archivos obligatorios de entrega."""
    faltantes = [
        nombre
        for nombre in ARCHIVOS_OBLIGATORIOS
        if not (BASE_DIR / nombre).is_file()
    ]

    if faltantes:
        return False, "Archivos faltantes: " + ", ".join(faltantes)

    return True, "Todos los archivos obligatorios de entrega existen"


def ent_5():
    """Comprueba que los puertos publicados estén documentados."""
    resultado = ejecutar_comando(
        "docker",
        "compose",
        "--env-file",
        ".env.example",
        "config",
        "--format",
        "json",
    )

    if resultado.returncode != 0:
        return False, "No fue posible obtener la configuracion"

    compose = json.loads(resultado.stdout)
    readme = leer_archivo("README.md")
    puertos = set()

    for servicio in compose.get("services", {}).values():
        for puerto in servicio.get("ports", []):
            publicado = puerto.get("published")

            if publicado is not None:
                puertos.add(str(publicado))

    if not puertos:
        return False, "No existen puertos publicados"

    faltantes = [
        puerto
        for puerto in sorted(puertos)
        if not re.search(rf"\b{re.escape(puerto)}\b", readme)
    ]

    if faltantes:
        return False, "Puertos sin documentar: " + ", ".join(faltantes)

    return True, "Puertos documentados: " + ", ".join(sorted(puertos))


def ent_6():
    """Comprueba la estructura del registro de verificación cruzada."""
    ruta = BASE_DIR / "docs/verificacion_cruzada.md"

    if not ruta.is_file():
        return False, "No existe el registro de verificacion cruzada"

    contenido = leer_archivo("docs/verificacion_cruzada.md")

    campos = (
        "Revisor:",
        "Repositorio revisado:",
        "Fecha:",
        "## Resultado por criterio",
        "## Hallazgos",
    )

    for campo in campos:
        if campo not in contenido:
            return False, f"Falta el campo obligatorio: {campo}"

    for numero in range(1, 7):
        patron = (
            rf"VC-{numero}\s*\([^)]+\)"
            r"\s*:\s*(?:PASA|FALLA)\b"
        )

        if not re.search(patron, contenido):
            return False, f"Falta el resultado de VC-{numero}"

    return True, "Registro con los seis criterios y hallazgos"


def ent_7():
    """Reutiliza el detector de secretos existente."""
    resultado = ejecutar_comando(
        sys.executable,
        "buscar_secretos.py",
    )

    if resultado.returncode != 0:
        return False, "El detector de secretos no fue aprobado"

    return True, "Detector de secretos aprobado"


def main():
    """Ejecuta los siete criterios de entrega."""
    comprobaciones = (
        ("ENT-1", "Composicion valida", ent_1),
        ("ENT-2", "Estructura del README", ent_2),
        ("ENT-3", "Variables documentadas", ent_3),
        ("ENT-4", "Archivos existentes", ent_4),
        ("ENT-5", "Puertos documentados", ent_5),
        ("ENT-6", "Registro de verificacion cruzada", ent_6),
        ("ENT-7", "Verificacion de secretos", ent_7),
    )

    aprobadas = 0
    total = len(comprobaciones)

    print("=== VERIFICADOR DE ENTREGA VYOPS ===")
    print()

    for codigo, descripcion, comprobar in comprobaciones:
        try:
            aprobado, evidencia = comprobar()

        except Exception as error:
            aprobado = False
            evidencia = (
                "No fue posible completar la comprobacion: "
                f"{type(error).__name__}"
            )

        aprobadas += int(aprobado)
        estado = "PASA" if aprobado else "FALLA"

        print(f"{estado} {codigo} - {descripcion}")
        print(f"    Evidencia: {evidencia}")

    print()
    print(f"{aprobadas} de {total} comprobaciones cumplidas")

    if aprobadas == total:
        print("RESULTADO: PASS")
        return 0

    print("RESULTADO: FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())