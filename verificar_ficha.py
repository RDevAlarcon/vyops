"""Verificador de la ficha de diseño funcional de VyOps.

Actividad correspondiente al Bloque 33 de SkillNest.
Comprueba la estructura, los requerimientos, el alcance
y las referencias documentales de la ficha funcional.
"""

import re
import unicodedata
from pathlib import Path


RAIZ_PROYECTO = Path(__file__).resolve().parent

RUTA_FICHA = (
    RAIZ_PROYECTO / "docs" / "ficha_diseno_funcional.md"
)

SECCIONES_OBLIGATORIAS = {
    1: "Problema de negocio",
    2: "Requerimientos y alcance (MVP)",
    3: "Arquitectura de la solución",
    4: "Criterios de aceptación",
    5: "Plan de construcción por hitos",
}

MIN_RF = 3
MIN_RNF = 2
MAX_RF_IMPRESCINDIBLES = 5

TERMINOS_SOLUCION = {
    "chatbot",
    "rag",
    "modelo",
    "inteligencia artificial",
    "llm",
}

def normalizar(texto: str) -> str:
    """Normaliza el texto para facilitar comparaciones.

    Convierte a minúsculas, elimina marcas diacríticas
    y reduce los espacios consecutivos.
    """
    texto = unicodedata.normalize("NFD", texto.lower())

    texto = "".join(
        caracter for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )

    return " ".join(texto.split())

def extraer_secciones(contenido: str) -> dict[int, dict]:
    """Extrae las secciones principales del documento Markdown.

    Identifica encabezados de segundo nivel numerados
    y separa sus títulos del contenido correspondiente.
    """
    patron = re.compile(
        r"^##[ \t]+(\d+)\.[ \t]+(.+)$",
        re.MULTILINE,
    )

    coincidencias = list(patron.finditer(contenido))
    secciones = {}

    for indice, coincidencia in enumerate(coincidencias):
        numero = int(coincidencia.group(1))
        titulo = coincidencia.group(2).strip()

        inicio = coincidencia.end()

        if indice + 1 < len(coincidencias):
            fin = coincidencias[indice + 1].start()
        else:
            fin = len(contenido)

        secciones[numero] = {
            "titulo": titulo,
            "contenido": contenido[inicio:fin].strip(),
        }

    return secciones

def validar_estructura(secciones: dict[int, dict]) -> list[str]:
    """Comprueba los encabezados y el contenido obligatorio.

    Las secciones 1 a 3 deben estar completas en el Bloque 33.
    Las secciones 4 y 5 pueden permanecer pendientes hasta
    el Bloque 34.
    """
    errores = []

    for numero, titulo_esperado in SECCIONES_OBLIGATORIAS.items():

        # Comprobar que la sección exista.
        if numero not in secciones:
            errores.append(
                f"Falta la seccion {numero}: {titulo_esperado}"
            )
            continue

        datos = secciones[numero]

        # Comparar el encabezado con el título obligatorio.
        if normalizar(datos["titulo"]) != normalizar(titulo_esperado):
            errores.append(
                f"Titulo incorrecto en la seccion {numero}. "
                f"Se esperaba: {titulo_esperado}"
            )

        # Las primeras tres secciones deben estar completas.
        if numero in (1, 2, 3):
            contenido = datos["contenido"]

            if not contenido or "[completar" in normalizar(contenido):
                errores.append(
                    f"Seccion {numero} incompleta: {titulo_esperado}"
                )

    return errores

def validar_problema(contenido: str) -> list[str]:
    """Detecta términos tecnológicos en el problema de negocio.

    Devuelve advertencias cuando la descripción del problema
    anticipa decisiones propias de la solución tecnológica.
    """
    avisos = []

    texto = normalizar(contenido)

    for termino in sorted(TERMINOS_SOLUCION):
        patron = rf"\b{re.escape(termino)}\b"

        if re.search(patron, texto):
            avisos.append(
                f"El problema de negocio contiene "
                f"un termino de solucion: {termino}"
            )

    return avisos

def extraer_requerimientos(
    contenido: str,
    prefijo: str,
) -> list[tuple[str, str]]:
    """Extrae los identificadores y descripciones de los requisitos.

    Reconoce el formato establecido en el Bloque 33:
    - RF-01: descripcion
    - RNF-01: descripcion
    """
    patron = (
        rf"^- ({re.escape(prefijo)}-\d{{2}}):[ \t]+(.+)$"
    )

    return re.findall(
        patron,
        contenido,
        flags=re.MULTILINE,
    )

def validar_requerimientos(contenido: str) -> list[str]:
    """Comprueba la cantidad, unicidad y medición de los requisitos."""
    errores = []

    rf = extraer_requerimientos(contenido, "RF")
    rnf = extraer_requerimientos(contenido, "RNF")

    # Comprobar las cantidades mínimas exigidas.
    if len(rf) < MIN_RF:
        errores.append(
            f"Se requieren al menos {MIN_RF} RF. "
            f"Encontrados: {len(rf)}."
        )

    if len(rnf) < MIN_RNF:
        errores.append(
            f"Se requieren al menos {MIN_RNF} RNF. "
            f"Encontrados: {len(rnf)}."
        )

    # Detectar identificadores duplicados.
    ids = [
        identificador
        for identificador, _ in rf + rnf
    ]

    duplicados = {
        identificador
        for identificador in ids
        if ids.count(identificador) > 1
    }

    if duplicados:
        errores.append(
            "Identificadores duplicados: "
            + ", ".join(sorted(duplicados))
        )

    # Comprobar que los RNF incluyan valores numéricos.
    for identificador, descripcion in rnf:

        if not re.search(r"\d", descripcion):
            errores.append(
                f"{identificador} no contiene "
                "un umbral numerico."
            )

    return errores

def extraer_alcance(contenido: str) -> dict[str, list[str]]:
    """Extrae los RF clasificados en las categorias de alcance.

    Admite descripciones distribuidas en varias lineas.
    Una linea vacia o un encabezado Markdown finaliza
    la lectura de la categoria activa.
    """
    categorias = {
        "imprescindible": [],
        "deseable": [],
        "fuera de alcance": [],
    }

    patron_categoria = re.compile(
        r"^(Imprescindible|Deseable|Fuera de alcance)"
        r":[ \t]*(.*)$",
        flags=re.IGNORECASE,
    )

    categoria_activa = None

    for linea in contenido.splitlines():
        linea = linea.strip()

        # Una linea vacia o un encabezado cierra la categoria.
        if not linea or linea.startswith("#"):
            categoria_activa = None
            continue

        coincidencia = patron_categoria.match(linea)

        if coincidencia:
            # Identificar el inicio de una categoria.
            categoria_activa = normalizar(
                coincidencia.group(1)
            )

            descripcion = coincidencia.group(2)

        elif categoria_activa is not None:
            # Procesar una linea de continuacion.
            descripcion = linea

        else:
            continue

        identificadores = re.findall(
            r"\bRF-\d{2}\b",
            descripcion,
        )

        categorias[categoria_activa].extend(
            identificadores
        )

    return categorias

def validar_alcance(contenido: str) -> list[str]:
    """Comprueba la clasificación única de los RF del MVP."""
    errores = []

    rf = extraer_requerimientos(contenido, "RF")

    ids_rf = {
        identificador
        for identificador, _ in rf
    }

    categorias = extraer_alcance(contenido)

    # Reunir todos los identificadores clasificados.
    clasificados = [
        identificador
        for identificadores in categorias.values()
        for identificador in identificadores
    ]

    # Detectar requerimientos sin clasificación.
    faltantes = ids_rf - set(clasificados)

    if faltantes:
        errores.append(
            "RF sin clasificar: "
            + ", ".join(sorted(faltantes))
        )

    # Detectar referencias a requerimientos inexistentes.
    desconocidos = set(clasificados) - ids_rf

    if desconocidos:
        errores.append(
            "RF clasificados pero no definidos: "
            + ", ".join(sorted(desconocidos))
        )

    # Detectar requerimientos clasificados más de una vez.
    duplicados = {
        identificador
        for identificador in clasificados
        if clasificados.count(identificador) > 1
    }

    if duplicados:
        errores.append(
            "RF con clasificacion multiple: "
            + ", ".join(sorted(duplicados))
        )

    # Verificar el máximo de RF imprescindibles.
    cantidad_imprescindibles = len(
        set(categorias["imprescindible"])
    )

    if cantidad_imprescindibles > MAX_RF_IMPRESCINDIBLES:
        errores.append(
            f"Maximo de {MAX_RF_IMPRESCINDIBLES} "
            f"RF imprescindibles permitido. "
            f"Encontrados: {cantidad_imprescindibles}."
        )

    return errores

def validar_diagrama(
    contenido: str,
    raiz: Path = RAIZ_PROYECTO,
) -> list[str]:
    """Comprueba las referencias a diagramas de arquitectura.

    Identifica imágenes PNG, JPG y JPEG dentro de docs/
    y verifica que los archivos referenciados existan.
    """
    errores = []

    patron = r"\bdocs/[\w./-]+\.(?:png|jpg|jpeg)\b"

    referencias = re.findall(
        patron,
        contenido,
        flags=re.IGNORECASE,
    )

    if not referencias:
        errores.append(
            "No se encontro una referencia al diagrama "
            "de arquitectura."
        )
        return errores

    # Eliminar referencias repetidas antes de comprobarlas.
    for referencia in sorted(set(referencias)):
        """raiz: Directorio raíz utilizado para resolver las
        rutas relativas de los diagramas.
        """
        ruta = raiz / referencia

        if not ruta.is_file():
            errores.append(
                f"Diagrama no encontrado: {referencia}"
            )

    return errores

def main() -> int:
    """Ejecuta las validaciones de la ficha funcional."""

    if not RUTA_FICHA.is_file():
        print("ERROR: No se encontro la ficha de diseno funcional.")
        return 1

    contenido = RUTA_FICHA.read_text(encoding="utf-8")
    secciones = extraer_secciones(contenido)

    errores = validar_estructura(secciones)
    avisos = []

    if 1 in secciones:
        avisos.extend(
            validar_problema(secciones[1]["contenido"])
        )
    if 2 in secciones:
        contenido_requisitos = secciones[2]["contenido"]

        # Validar únicamente cuando la sección esté completa.
        if "[completar" not in normalizar(contenido_requisitos):
            errores.extend(
                validar_requerimientos(contenido_requisitos)
            )

            errores.extend(
                validar_alcance(contenido_requisitos)
            )
    if 3 in secciones:
        contenido_arquitectura = secciones[3]["contenido"]

        # Evitar errores adicionales sobre la plantilla incompleta.
        if "[completar" not in normalizar(contenido_arquitectura):
            errores.extend(
                validar_diagrama(contenido_arquitectura)
            )

    print("=== VERIFICACION DE FICHA FUNCIONAL ===")

    for error in errores:
        print(f"ERROR: {error}")

    for aviso in avisos:
        print(f"AVISO: {aviso}")

    print(f"\nErrores: {len(errores)}")
    print(f"Avisos: {len(avisos)}")

    if errores:
        print("RESULTADO: FAIL")
        return 1

    print("Ficha verificada: secciones 1 a 3 completas")
    print("RESULTADO: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())