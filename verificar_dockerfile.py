"""Verifica las condiciones minimas del empaquetado Docker de VyOps."""

import re
import sys
import shlex
import sys
from pathlib import Path


# Directorio base del proyecto.
BASE_DIR = Path(__file__).resolve().parent

# Identifica nombres de variables potencialmente sensibles.
SECRETOS = re.compile(
    r"KEY|TOKEN|SECRET|PASSWORD",
    re.IGNORECASE,
)

# Exclusiones minimas exigidas para el contexto de construccion.
IGNORAR_MINIMO = (
    ".env",
    ".git",
    ".venv",
)


def leer_archivo(ruta: Path) -> str | None:
    """Lee un archivo de configuracion utilizando UTF-8."""
    try:
        return ruta.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        return None


def obtener_instrucciones(
    contenido: str,
) -> list[tuple[str, str]]:
    """Extrae las instrucciones del Dockerfile y sus argumentos."""

    # Unifica instrucciones distribuidas en varias lineas.
    contenido = re.sub(
        r"\\[ \t]*\r?\n",
        " ",
        contenido,
    )

    instrucciones = []

    for linea in contenido.splitlines():
        linea = linea.strip()

        # Omite comentarios y lineas vacias.
        if not linea or linea.startswith("#"):
            continue

        partes = linea.split(maxsplit=1)

        nombre = partes[0].upper()
        argumentos = partes[1] if len(partes) > 1 else ""

        instrucciones.append((nombre, argumentos))

    return instrucciones

def verificar_df1(
    instrucciones: list[tuple[str, str]],
) -> tuple[bool, str]:
    """Comprueba que las imagenes base tengan una version explicita."""

    imagenes = []

    for nombre, argumentos in instrucciones:
        if nombre != "FROM":
            continue

        partes = argumentos.split()

        # Omite opciones como --platform.
        partes = [
            parte
            for parte in partes
            if not parte.startswith("--")
        ]

        if not partes:
            return False, "Instruccion FROM sin imagen base."

        imagen = partes[0]

        # Scratch es una imagen base especial sin version.
        if imagen == "scratch":
            continue

        # Un digest SHA-256 identifica una imagen inmutable.
        if re.fullmatch(
            r"[^@\s]+@sha256:[a-fA-F0-9]{64}",
            imagen,
        ):
            imagenes.append(imagen)
            continue

        # Evita confundir el puerto de un registro con una etiqueta.
        referencia = imagen.rsplit("/", 1)[-1]
        _, separador, etiqueta = referencia.partition(":")

        if (
            not separador
            or not etiqueta
            or etiqueta.lower() == "latest"
            or "$" in imagen
            or "@" in imagen
        ):
            return False, "Imagen base sin version explicita valida."

        imagenes.append(imagen)

    if not imagenes:
        return False, "No se encontro una imagen base versionada."

    return True, f"Imagenes base versionadas: {', '.join(imagenes)}"

def verificar_df2(
    instrucciones: list[tuple[str, str]],
) -> tuple[bool, str]:
    """Comprueba el orden de las capas de dependencias y codigo."""

    copia_dependencias = None
    instalacion_dependencias = None
    copia_codigo = None

    for indice, (nombre, argumentos) in enumerate(instrucciones):

        if nombre == "COPY":
            # Identifica la copia exclusiva de requirements.txt.
            if re.fullmatch(
                r"requirements\.txt\s+\S+",
                argumentos.strip(),
            ):
                if copia_dependencias is None:
                    copia_dependencias = indice

            elif copia_codigo is None:
                copia_codigo = indice

        elif nombre == "RUN":
            # Identifica la instalacion desde requirements.txt.
            if (
                re.search(r"\bpip(?:3)?\s+install\b", argumentos)
                and re.search(
                    r"(?:-r|--requirement)\s+requirements\.txt\b",
                    argumentos,
                )
            ):
                if instalacion_dependencias is None:
                    instalacion_dependencias = indice

    if copia_dependencias is None:
        return False, "Falta COPY requirements.txt."

    if instalacion_dependencias is None:
        return False, "Falta instalar las dependencias."

    if copia_codigo is None:
        return False, "Falta copiar el codigo de la aplicacion."

    if not (
        copia_dependencias
        < instalacion_dependencias
        < copia_codigo
    ):
        return False, "Orden incorrecto de las capas."

    return True, (
        "Orden correcto: COPY requirements.txt -> "
        "RUN pip install -> COPY codigo."
    )

def verificar_df3(
    instrucciones: list[tuple[str, str]],
) -> tuple[bool, str]:
    """Comprueba la configuracion de escucha HTTP del servicio."""

    comandos = {}

    for nombre, argumentos in instrucciones:
        if nombre in ("CMD", "ENTRYPOINT"):
            comandos[nombre] = argumentos

    if not comandos:
        return False, "Falta CMD o ENTRYPOINT."

    # Reconoce el argumento --host en formato JSON o shell.
    patron_host = re.compile(
        r"""(?:^|[\s"'[])--host(?:["']?\s*,\s*["']|[=\s]+["']?)"""
        r"""0\.0\.0\.0(?=$|[\s"',\]])"""
    )

    for argumentos in comandos.values():
        if patron_host.search(argumentos):
            return True, "Servicio configurado en 0.0.0.0."

    return False, "Falta configurar --host 0.0.0.0."

def verificar_df4(
    instrucciones: list[tuple[str, str]],
) -> tuple[bool, str]:
    """Comprueba que el usuario final no sea root."""

    usuario_final = None

    for nombre, argumentos in instrucciones:
        if nombre == "USER":
            usuario_final = argumentos.strip()

    if not usuario_final:
        return False, "Falta declarar un usuario de ejecucion."

    # USER admite el formato usuario:grupo.
    usuario = usuario_final.split(":", maxsplit=1)[0]

    if not usuario or "$" in usuario_final:
        return False, "No se puede determinar el usuario final."

    # Detecta root por nombre o por identificador numerico.
    if usuario.lower() == "root" or (
        usuario.isdecimal() and int(usuario) == 0
    ):
        return False, "El servicio se ejecutaria como root."

    return True, f"Usuario de ejecucion declarado: {usuario_final}"

def verificar_df5(
    instrucciones: list[tuple[str, str]],
) -> tuple[bool, str]:
    """Detecta declaraciones de variables potencialmente sensibles."""

    encontradas = set()

    for nombre, argumentos in instrucciones:
        if nombre not in ("ENV", "ARG"):
            continue

        try:
            partes = shlex.split(argumentos)
        except ValueError:
            return False, f"Instruccion {nombre} mal formada."

        if not partes:
            return False, f"Instruccion {nombre} sin argumentos."

        # ENV admite tanto CLAVE=valor como CLAVE valor.
        if nombre == "ENV" and "=" not in partes[0]:
            variables = [partes[0]]

        else:
            variables = [
                parte.split("=", maxsplit=1)[0]
                for parte in partes
                if "=" in parte or nombre == "ARG"
            ]

        # Registra exclusivamente los nombres, nunca sus valores.
        for variable in variables:
            if SECRETOS.search(variable):
                encontradas.add(variable)

    if encontradas:
        nombres = ", ".join(sorted(encontradas))

        return False, (
            f"Variables potencialmente sensibles: {nombres}"
        )

    return True, "Sin variables sensibles declaradas en ENV o ARG."

def verificar_df6(
    contenido: str | None,
) -> tuple[bool, str]:
    """Comprueba las exclusiones minimas del archivo dockerignore."""

    if contenido is None:
        return False, "No existe el archivo .dockerignore."

    exclusiones = {
        nombre: False
        for nombre in IGNORAR_MINIMO
    }

    for linea in contenido.splitlines():
        linea = linea.strip()

        if not linea or linea.startswith("#"):
            continue

        # Identifica reglas de inclusion mediante el prefijo !.
        negada = linea.startswith("!")

        patron = linea[1:] if negada else linea

        # Normaliza las variantes simples de una misma ruta.
        patron = patron.strip().strip("/")

        if patron.startswith("./"):
            patron = patron[2:]

        if patron in exclusiones:
            exclusiones[patron] = not negada

    faltantes = [
        nombre
        for nombre, excluido in exclusiones.items()
        if not excluido
    ]

    if faltantes:
        return False, (
            "Exclusiones obligatorias ausentes o revertidas: "
            + ", ".join(faltantes)
        )

    return True, (
        "Exclusiones minimas presentes: "
        + ", ".join(IGNORAR_MINIMO)
    )

def verificar_df7(
    instrucciones: list[tuple[str, str]],
) -> tuple[bool, str]:
    """Comprueba que exista un healthcheck habilitado."""

    healthcheck = None

    for nombre, argumentos in instrucciones:
        if nombre == "HEALTHCHECK":
            healthcheck = argumentos.strip()

    if not healthcheck:
        return False, "Falta declarar HEALTHCHECK."

    if healthcheck.upper() == "NONE":
        return False, "HEALTHCHECK se encuentra deshabilitado."

    # Comprueba que exista un comando de verificacion.
    if not re.match(
        r"^(?:--\S+\s+)*CMD\s+\S",
        healthcheck,
        re.IGNORECASE,
    ):
        return False, "HEALTHCHECK sin comando valido."

    return True, "HEALTHCHECK habilitado con comando de verificacion."

def ejecutar(directorio: Path = BASE_DIR) -> int:
    """Ejecuta las comprobaciones estaticas del empaquetado Docker."""

    print("=== VERIFICADOR ESTATICO DOCKER VYOPS ===")
    print(f"Directorio: {directorio}")
    print()

    # Carga los archivos necesarios para la verificacion.
    try:
        contenido = leer_archivo(directorio / "Dockerfile")
        dockerignore = leer_archivo(directorio / ".dockerignore")

    except (OSError, UnicodeError):
        print("FALLA - No fue posible leer los archivos.")
        return 1

    if contenido is None:
        print("FALLA - No existe el archivo Dockerfile.")
        return 1

    instrucciones = obtener_instrucciones(contenido)

    # Centraliza las comprobaciones y sus descripciones.
    comprobaciones = (
        (
            "DF-1",
            "Imagen base versionada",
            verificar_df1(instrucciones),
        ),
        (
            "DF-2",
            "Orden de las capas",
            verificar_df2(instrucciones),
        ),
        (
            "DF-3",
            "Configuracion de escucha HTTP",
            verificar_df3(instrucciones),
        ),
        (
            "DF-4",
            "Usuario sin privilegios de root",
            verificar_df4(instrucciones),
        ),
        (
            "DF-5",
            "Variables potencialmente sensibles",
            verificar_df5(instrucciones),
        ),
        (
            "DF-6",
            "Exclusiones minimas",
            verificar_df6(dockerignore),
        ),
        (
            "DF-7",
            "Healthcheck habilitado",
            verificar_df7(instrucciones),
        ),
    )

    aprobadas = 0
    total = len(comprobaciones)

    # Presenta el resultado y la evidencia de cada comprobacion.
    for identificador, descripcion, resultado in comprobaciones:
        aprobado, evidencia = resultado

        estado = "PASA" if aprobado else "FALLA"

        print(f"{estado} {identificador} - {descripcion}")
        print(f"    Evidencia: {evidencia}")

        if aprobado:
            aprobadas += 1

    print()
    print(f"{aprobadas} de {total} comprobaciones cumplidas")

    # El codigo de salida permite integrar el script en CI/CD.
    if aprobadas == total:
        print("RESULTADO: PASS")
        return 0

    print("RESULTADO: FAIL")
    return 1


if __name__ == "__main__":
    # Permite verificar otro directorio sin modificar el proyecto.
    if len(sys.argv) > 2:
        print("Uso: python verificar_dockerfile.py [directorio]")
        sys.exit(1)

    directorio = (
        Path(sys.argv[1]).resolve()
        if len(sys.argv) == 2
        else BASE_DIR
    )

    sys.exit(ejecutar(directorio))