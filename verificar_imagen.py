"""Verifica el comportamiento de una imagen Docker de VyOps."""

import re
import subprocess
import sys
import time

from pathlib import Path
from uuid import uuid4

import httpx2

from casos import CASOS, ejecutar_caso


# Directorio base del proyecto.
BASE_DIR = Path(__file__).resolve().parent

# Imagen predeterminada que se desea verificar.
IMAGEN_PREDETERMINADA = "vyops:0.2"

# Configuracion HTTP del entorno de verificacion.
HOST = "127.0.0.1"
PUERTO = 8099
PUERTO_INTERNO = 8000
URL_BASE = f"http://{HOST}:{PUERTO}"

# Limites de espera para evitar ejecuciones indefinidas.
TIMEOUT_DOCKER = 60
TIMEOUT_ARRANQUE = 30
TIMEOUT_HEALTHCHECK = 30
INTERVALO_ESPERA = 0.5

# Prefijo reservado para los contenedores de verificacion.
PREFIJO_CONTENEDOR = "vyops-verificacion"
# Etiqueta utilizada para identificar contenedores de verificacion.
ETIQUETA_PROPIEDAD = "cl.vytronix.vyops.verificacion"

def docker(*argumentos: str) -> tuple[int, str]:
    """Ejecuta un comando Docker y devuelve su codigo y salida."""

    try:
        resultado = subprocess.run(
            ["docker", *argumentos],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=TIMEOUT_DOCKER,
            check=False,
        )

    except FileNotFoundError:
        return 127, "Docker no se encuentra disponible."

    except subprocess.TimeoutExpired:
        return 124, "Tiempo de espera de Docker agotado."

    except OSError:
        return 1, "No fue posible ejecutar Docker."

    salida = "\n".join(
        parte.strip()
        for parte in (
            resultado.stdout,
            resultado.stderr,
        )
        if parte and parte.strip()
    )

    return resultado.returncode, salida


def generar_nombre_contenedor() -> str:
    """Genera un nombre unico para un contenedor temporal."""

    identificador = uuid4().hex

    return f"{PREFIJO_CONTENEDOR}-{identificador}"

def arrancar_contenedor(
    imagen: str,
    nombre: str,
) -> tuple[bool, str]:
    """Inicia un contenedor utilizando la configuracion original."""

    codigo, salida = docker(
        "run",
        "--detach",
        "--pull=never",
        "--name",
        nombre,
        "--label",
        f"{ETIQUETA_PROPIEDAD}={nombre}",
        "--publish",
        f"{HOST}:{PUERTO}:{PUERTO_INTERNO}",
        imagen,
    )

    if codigo != 0:
        return False, "No fue posible iniciar el contenedor."

    return True, salida


def eliminar_contenedor(nombre: str) -> tuple[bool, str]:
    """Elimina exclusivamente un contenedor temporal autorizado."""

    prefijo = f"{PREFIJO_CONTENEDOR}-"

    if not nombre.startswith(prefijo):
        return False, "Nombre de contenedor no autorizado."

    identificador = nombre[len(prefijo):]

    if (
        len(identificador) != 32
        or any(
            caracter not in "0123456789abcdef"
            for caracter in identificador
        )
    ):
        return False, "Identificador de contenedor no valido."

    # Verifica la etiqueta antes de realizar una operacion destructiva.
    formato = (
        '{{index .Config.Labels "'
        + ETIQUETA_PROPIEDAD
        + '"}}'
    )

    codigo, salida = docker(
        "container",
        "inspect",
        nombre,
        "--format",
        formato,
    )

    if codigo != 0:
        return False, "No fue posible verificar la propiedad."

    if salida.strip() != nombre:
        return False, "Propiedad del contenedor no confirmada."

    codigo, _ = docker(
        "container",
        "rm",
        "--force",
        nombre,
    )

    if codigo != 0:
        return False, "No fue posible eliminar el contenedor."

    return True, "Contenedor temporal eliminado."

def esperar_servicio(
    url_base: str = URL_BASE,
    timeout: float = TIMEOUT_ARRANQUE,
) -> tuple[bool, str]:
    """Espera hasta que el servicio HTTP responda correctamente."""

    limite = time.monotonic() + timeout

    with httpx2.Client(
        timeout=2.0,
        trust_env=False,
    ) as cliente:

        while time.monotonic() < limite:
            try:
                respuesta = cliente.get(
                    f"{url_base}/salud"
                )

                if respuesta.status_code == 200:
                    if respuesta.json().get("estado") == "ok":
                        return True, "Servicio HTTP disponible."

            except (httpx2.HTTPError, ValueError):
                # El servicio puede encontrarse iniciando.
                pass

            time.sleep(INTERVALO_ESPERA)

    return False, "Tiempo de espera del servicio agotado."

def resolver_imagen(imagen: str) -> tuple[bool, str]:
    """Resuelve una referencia Docker a su identificador inmutable."""

    codigo, salida = docker(
        "image",
        "inspect",
        imagen,
        "--format",
        "{{.Id}}",
    )

    if codigo != 0:
        return False, "No fue posible inspeccionar la imagen local."

    identificador = salida.strip()

    if not re.fullmatch(
        r"sha256:[a-f0-9]{64}",
        identificador,
    ):
        return False, "Identificador de imagen no valido."

    return True, identificador


def verificar_img1(imagen: str) -> tuple[bool, str]:
    """Comprueba que la imagen Docker exista localmente."""

    aprobado, resultado = resolver_imagen(imagen)

    if not aprobado:
        return False, resultado

    return True, f"Imagen disponible: {resultado}"

def verificar_img2(
    url_base: str = URL_BASE,
) -> tuple[bool, str]:
    """Comprueba la disponibilidad HTTP del servicio."""

    return esperar_servicio(url_base)

def verificar_img3(nombre: str) -> tuple[bool, str]:
    """Comprueba que el usuario efectivo no sea root."""

    codigo, salida = docker(
        "exec",
        nombre,
        "id",
        "-u",
    )

    if codigo != 0:
        return False, "No fue posible consultar el UID."

    uid = salida.strip()

    if not uid.isascii() or not uid.isdecimal():
        return False, "UID de ejecucion no valido."

    if int(uid) == 0:
        return False, "El contenedor se ejecuta como root."

    return True, f"Usuario sin privilegios de root: UID {uid}"

def verificar_img4(nombre: str) -> tuple[bool, str]:
    """Inspecciona /app y rechaza archivos prohibidos o errores de acceso."""

    codigo_inspeccion = """
from pathlib import Path

raiz = Path("/app")

if not raiz.is_dir():
    raise SystemExit(2)

nombres_prohibidos = {
    ".env",
    ".git",
    ".venv",
    ".venv-viejo",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "tests",
    "docs",
    "dockerfile",
    "requirements-dev.txt",
}

extensiones_prohibidas = {
    ".pem",
    ".key",
    ".p12",
    ".pfx",
    ".sqlite",
    ".sqlite3",
    ".db",
    ".pyc",
    ".pyo",
    ".jsonl",
    ".log",
    ".bak",
}


def controlar_error(error):
    # Impide aprobar una inspeccion incompleta.
    raise error


encontrados = []

try:
    for directorio, subdirectorios, archivos in raiz.walk(
        on_error=controlar_error,
        follow_symlinks=False,
    ):
        for elemento in subdirectorios + archivos:
            ruta = directorio / elemento
            nombre = ruta.name.lower()

            if (
                nombre in nombres_prohibidos
                or nombre.startswith(".env.")
                or nombre.startswith("vectorstore")
                or ruta.suffix.lower() in extensiones_prohibidas
            ):
                encontrados.append(
                    ruta.relative_to(raiz).as_posix()
                )

except OSError:
    raise SystemExit(2)

if encontrados:
    for ruta in sorted(encontrados):
        print(ruta)

    raise SystemExit(1)

print("INSPECCION_OK")
"""

    codigo, salida = docker(
        "exec",
        nombre,
        "python",
        "-c",
        codigo_inspeccion,
    )

    if codigo == 1:
        return False, (
            "Se detectaron archivos prohibidos "
            "o un fallo durante la inspeccion."
        )

    if codigo != 0:
        return False, "No fue posible inspeccionar /app."

    if salida.strip() != "INSPECCION_OK":
        return False, "Resultado de inspeccion no valido."

    return True, "Sin archivos prohibidos detectados en /app."

def arrancar_contenedor_integracion(
    imagen: str,
    nombre: str,
) -> tuple[bool, str]:
    """Inicia un contenedor con el RAG simulado para pruebas HTTP."""

    archivos = (
        "servidor_pruebas.py",
        "casos.py",
    )

    montajes = []

    for archivo in archivos:
        ruta = BASE_DIR / archivo

        if not ruta.is_file():
            return False, f"Falta el archivo de pruebas: {archivo}"

        montajes.extend(
            (
                "--mount",
                (
                    f"type=bind,source={ruta},"
                    f"target=/app/{archivo},readonly"
                ),
            )
        )

    # Sustituye exclusivamente la logica RAG por una simulacion.
    # La API, sus esquemas y validaciones siguen siendo reales.
    codigo_simulacion = (
        "from unittest.mock import patch; "
        "import uvicorn; "
        "from servidor_pruebas import app, responder_simulado; "
        "p = patch("
        "'servicio.logica.responder', "
        "side_effect=responder_simulado"
        "); "
        "p.start(); "
        "uvicorn.run("
        "app, host='0.0.0.0', port=8000"
        ")"
    )

    codigo, salida = docker(
        "run",
        "--detach",
        "--pull=never",
        "--name",
        nombre,
        "--label",
        f"{ETIQUETA_PROPIEDAD}={nombre}",
        "--publish",
        f"{HOST}:{PUERTO}:{PUERTO_INTERNO}",
        *montajes,
        imagen,
        "python",
        "-c",
        codigo_simulacion,
    )

    if codigo != 0:
        return False, "No fue posible iniciar el contenedor de integracion."

    return True, salida

def verificar_img5(
    url_base: str = URL_BASE,
) -> tuple[bool, str]:
    """Ejecuta los casos de integracion HTTP con el RAG simulado."""

    aprobadas = 0
    total = len(CASOS)

    if total == 0:
        return False, "No existen casos HTTP para ejecutar."

    with httpx2.Client(
        base_url=url_base,
        timeout=10.0,
        trust_env=False,
    ) as cliente:

        for caso in CASOS:
            identificador = caso["id"]

            try:
                aprobado, estado, _ = ejecutar_caso(
                    cliente,
                    caso,
                )

            except httpx2.HTTPError:
                print(
                    f"    FALLA {identificador} "
                    "- Error de comunicacion HTTP"
                )

                continue

            resultado = "PASA" if aprobado else "FALLA"

            print(
                f"    {resultado} {identificador} "
                f"- HTTP {estado}"
            )

            if aprobado:
                aprobadas += 1

    evidencia = (
        f"{aprobadas} de {total} casos HTTP aprobados "
        "con RAG simulado."
    )

    return aprobadas == total, evidencia

def verificar_img6(
    nombre: str,
    timeout: float = TIMEOUT_HEALTHCHECK,
) -> tuple[bool, str]:
    """Comprueba que Docker reporte el contenedor como saludable."""

    limite = time.monotonic() + timeout
    ultimo_estado = "desconocido"

    formato = (
        "{{if .State.Health}}"
        "{{.State.Health.Status}}"
        "{{else}}"
        "sin healthcheck"
        "{{end}}"
    )

    while time.monotonic() < limite:
        codigo, salida = docker(
            "container",
            "inspect",
            nombre,
            "--format",
            formato,
        )

        if codigo != 0:
            return False, (
                "No fue posible consultar el estado de salud."
            )

        ultimo_estado = salida.strip()

        if ultimo_estado == "healthy":
            return True, "Healthcheck en estado healthy."

        if ultimo_estado == "sin healthcheck":
            return False, "El contenedor no tiene healthcheck."

        if ultimo_estado not in ("starting", "unhealthy"):
            return False, "Estado de salud no reconocido."

        time.sleep(INTERVALO_ESPERA)

    return False, (
        "Tiempo de espera del healthcheck agotado. "
        f"Ultimo estado: {ultimo_estado}."
    )

def ejecutar_comprobacion(
    identificador: str,
    descripcion: str,
    funcion,
    *argumentos,
) -> bool:
    """Ejecuta una comprobacion y presenta su resultado."""

    try:
        aprobado, evidencia = funcion(*argumentos)

    except Exception:
        aprobado = False
        evidencia = "Error inesperado durante la comprobacion."

    estado = "PASA" if aprobado else "FALLA"

    print(f"{estado} {identificador} - {descripcion}")
    print(f"    Evidencia: {evidencia}")

    return aprobado

def limpiar_contenedor(nombre: str) -> bool:
    """Elimina un contenedor temporal y verifica su ausencia."""

    if not nombre.startswith(f"{PREFIJO_CONTENEDOR}-"):
        print("FALLA - Nombre de contenedor no autorizado.")
        return False

    # Consultamos los contenedores existentes sin interpretar
    # un error de Docker como ausencia del contenedor.
    codigo, salida = docker(
        "container",
        "ls",
        "--all",
        "--filter",
        f"name=^/{nombre}$",
        "--format",
        "{{.Names}}",
    )

    if codigo != 0:
        print("FALLA - No fue posible verificar el contenedor.")
        return False

    nombres = salida.splitlines()

    if nombre not in nombres:
        print("    Contenedor temporal ausente.")
        return True

    aprobado, evidencia = eliminar_contenedor(nombre)

    if not aprobado:
        print(f"FALLA - {evidencia}")
        return False

    codigo, salida = docker(
        "container",
        "ls",
        "--all",
        "--filter",
        f"name=^/{nombre}$",
        "--format",
        "{{.Names}}",
    )

    if codigo != 0 or nombre in salida.splitlines():
        print("FALLA - No se pudo confirmar la limpieza.")
        return False

    print(f"    {evidencia}")

    return True

def ejecutar(
    imagen: str = IMAGEN_PREDETERMINADA,
) -> int:
    """Ejecuta las seis comprobaciones dinamicas de Docker."""

    print("=== VERIFICADOR DINAMICO DOCKER VYOPS ===")
    print(f"Imagen: {imagen}")
    print(f"URL de verificacion: {URL_BASE}")
    print()

    resultados = {
        f"IMG-{numero}": False
        for numero in range(1, 7)
    }

    limpieza_correcta = True

    # IMG-1: resolver la imagen una sola vez.
    try:
        aprobado, resultado = resolver_imagen(imagen)

    except Exception:
        aprobado = False
        resultado = (
            "Error inesperado durante la resolucion de la imagen."
        )

    resultados["IMG-1"] = aprobado

    if aprobado:
        imagen_id = resultado

        print("PASA IMG-1 - Existencia de la imagen")
        print(f"    Evidencia: Imagen disponible: {imagen_id}")

    else:
        print("FALLA IMG-1 - Existencia de la imagen")
        print(f"    Evidencia: {resultado}")

    if resultados["IMG-1"]:
        nombre_original = generar_nombre_contenedor()

        print()
        print("=== CONTENEDOR ORIGINAL ===")
        print(f"Contenedor: {nombre_original}")

        try:
            iniciado, evidencia = arrancar_contenedor(
                imagen_id,
                nombre_original,
            )

            if iniciado:
                resultados["IMG-2"] = ejecutar_comprobacion(
                    "IMG-2",
                    "Disponibilidad HTTP",
                    verificar_img2,
                )

                resultados["IMG-3"] = ejecutar_comprobacion(
                    "IMG-3",
                    "Usuario sin privilegios de root",
                    verificar_img3,
                    nombre_original,
                )

                resultados["IMG-4"] = ejecutar_comprobacion(
                    "IMG-4",
                    "Ausencia de archivos prohibidos",
                    verificar_img4,
                    nombre_original,
                )

                resultados["IMG-6"] = ejecutar_comprobacion(
                    "IMG-6",
                    "Healthcheck habilitado y saludable",
                    verificar_img6,
                    nombre_original,
                )

            else:
                print(f"FALLA - {evidencia}")

        except Exception:
            print(
                "FALLA - Error inesperado durante "
                "la verificacion del contenedor original."
            )

        finally:
            try:
                limpieza_correcta = limpiar_contenedor(
                    nombre_original
                )

            except Exception:
                limpieza_correcta = False

                print(
                    "FALLA - Error inesperado durante "
                    "la limpieza del contenedor original."
                )

        # Solo iniciamos la integracion cuando el contenedor
        # anterior fue eliminado correctamente.
        if limpieza_correcta:
            nombre_integracion = generar_nombre_contenedor()

            print()
            print("=== CONTENEDOR DE INTEGRACION ===")
            print(f"Contenedor: {nombre_integracion}")

            try:
                iniciado, evidencia = (
                    arrancar_contenedor_integracion(
                        imagen_id,
                        nombre_integracion,
                    )
                )

                if iniciado:
                    disponible, evidencia = esperar_servicio()

                    if disponible:
                        resultados["IMG-5"] = (
                            ejecutar_comprobacion(
                                "IMG-5",
                                "Integracion HTTP con RAG simulado",
                                verificar_img5,
                            )
                        )

                    else:
                        print(f"FALLA IMG-5 - {evidencia}")

                else:
                    print(f"FALLA IMG-5 - {evidencia}")

            except Exception:
                print(
                    "FALLA IMG-5 - Error inesperado durante "
                    "la verificacion de integracion."
                )

            finally:
                try:
                    limpieza_correcta = limpiar_contenedor(
                        nombre_integracion
                    )

                except Exception:
                    limpieza_correcta = False

                    print(
                        "FALLA - Error inesperado durante "
                        "la limpieza del contenedor de integracion."
                    )

        else:
            print(
                "IMG-5 no ejecutada por un fallo de limpieza."
            )

    else:
        print(
            "Comprobaciones restantes no ejecutadas "
            "porque la imagen no esta disponible."
        )

    # Consolidacion de resultados.
    print()
    print("=== RESUMEN DE VERIFICACION ===")

    for identificador, aprobado in resultados.items():
        estado = "PASA" if aprobado else "NO APROBADA"
        print(f"{estado} {identificador}")

    aprobadas = sum(resultados.values())
    total = len(resultados)

    print()
    print(f"{aprobadas} de {total} comprobaciones cumplidas")

    estado_limpieza = (
        "PASS" if limpieza_correcta else "FAIL"
    )

    print(f"Limpieza de contenedores: {estado_limpieza}")

    if aprobadas == total and limpieza_correcta:
        print("RESULTADO: PASS")
        return 0

    print("RESULTADO: FAIL")
    return 1

if __name__ == "__main__":
    if len(sys.argv) > 2:
        print("Uso: python verificar_imagen.py [imagen]")
        sys.exit(1)

    imagen = (
        sys.argv[1]
        if len(sys.argv) == 2
        else IMAGEN_PREDETERMINADA
    )

    sys.exit(ejecutar(imagen))