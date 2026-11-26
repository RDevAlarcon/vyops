"""
Extractor de datos de la ficha de diseño funcional de VyOps.

Actividad correspondiente al Bloque 34 de SkillNest.

Transforma el contenido Markdown de la ficha en estructuras
de datos reutilizables para generar resúmenes y comprobar
la coherencia entre requerimientos, criterios y hitos.
"""

import re
from pathlib import Path

from verificar_ficha import (
    RUTA_FICHA,
    extraer_secciones,
    extraer_requerimientos,
    extraer_alcance,
)


# Patrón para reconocer números enteros y decimales.
NUMERO = r"(\d+(?:[.,]\d+)?)"


def a_numero(texto: str) -> float:
    """Convierte un número textual a un valor decimal.

    Admite tanto el punto como la coma como separador decimal.
    """
    return float(texto.replace(",", "."))

def extraer_criterios(contenido: str) -> list[dict]:
    """Extrae los criterios de aceptación de la ficha funcional.

    Reconoce el identificador del criterio, los requerimientos
    asociados y la descripción de la comprobación.

    Args:
        contenido: Texto Markdown de la sección 4.

    Returns:
        Lista de criterios de aceptación estructurados.
    """

    criterios = []

    patron = re.compile(
        r"^- (CA-\d{2}) \(([^)]*)\):[ \t]+(.+)$",
        flags=re.MULTILINE,
    )

    for coincidencia in patron.finditer(contenido):

        identificador = coincidencia.group(1)
        referencias = coincidencia.group(2)
        descripcion = coincidencia.group(3).strip()

        # Extraer los RF y RNF asociados al criterio.
        requerimientos = re.findall(
            r"\b(?:RF|RNF)-\d{2}\b",
            referencias,
        )

        criterios.append({
            "id": identificador,
            "cubre": requerimientos,
            "texto": descripcion,
        })

    return criterios

def extraer_presupuesto(
    contenido: str,
) -> dict[str, float | None]:
    """Extrae el presupuesto temporal del plan de construcción.

    Identifica las horas disponibles y el margen reservado
    para imprevistos.

    Args:
        contenido: Texto Markdown de la sección 5.

    Returns:
        Diccionario con las horas disponibles y el margen.
        Los valores ausentes se representan mediante None.
    """

    patron_disponibles = (
        rf"^Horas disponibles:[ \t]*{NUMERO}[ \t]+h[ \t]*$"
    )

    patron_margen = (
        rf"^Margen de imprevistos:[ \t]*{NUMERO}[ \t]+h[ \t]*$"
    )

    disponibles = re.search(
        patron_disponibles,
        contenido,
        flags=re.MULTILINE,
    )

    margen = re.search(
        patron_margen,
        contenido,
        flags=re.MULTILINE,
    )

    return {
        "disponibles": (
            a_numero(disponibles.group(1))
            if disponibles else None
        ),
        "margen": (
            a_numero(margen.group(1))
            if margen else None
        ),
    }

def extraer_hitos(contenido: str) -> list[dict]:
    """Extrae los hitos del plan de construcción.

    Identifica el código del hito, su duración estimada,
    los requerimientos cubiertos y los criterios de aceptación
    asociados.

    Args:
        contenido: Texto Markdown de la sección 5.

    Returns:
        Lista de hitos estructurados.
    """

    hitos = []

    patron = re.compile(
        rf"^- (H\d+) \({NUMERO} h\):[ \t]+(.+)$",
        flags=re.MULTILINE,
    )

    for coincidencia in patron.finditer(contenido):

        identificador = coincidencia.group(1)
        horas = a_numero(coincidencia.group(2))
        texto = coincidencia.group(3).strip()

        # Identificar las referencias a requisitos y criterios.
        referencias = re.search(
            r"Cubre:(.*?)Se comprueba con:(.*)$",
            texto,
        )

        requerimientos = []
        criterios = []

        if referencias:

            requerimientos = re.findall(
                r"\b(?:RF|RNF)-\d{2}\b",
                referencias.group(1),
            )

            criterios = re.findall(
                r"\bCA-\d{2}\b",
                referencias.group(2),
            )

        hitos.append({
            "id": identificador,
            "horas": horas,
            "cubre": requerimientos,
            "criterios": criterios,
        })

    return hitos

def cargar(ruta: Path = RUTA_FICHA) -> dict:
    """Carga y estructura los datos de la ficha funcional.

    Reutiliza las funciones de extracción implementadas
    durante el Bloque 33.

    Args:
        ruta: Ubicación del archivo Markdown de la ficha.

    Returns:
        Diccionario con los datos estructurados de la ficha.
    """

    contenido = Path(ruta).read_text(encoding="utf-8")

    secciones = extraer_secciones(contenido)

    texto2 = secciones.get(2, {}).get("contenido", "")
    texto4 = secciones.get(4, {}).get("contenido", "")
    texto5 = secciones.get(5, {}).get("contenido", "")
    presupuesto = extraer_presupuesto(texto5)

    ficha = {
        "rf": dict(extraer_requerimientos(texto2, "RF")),
        "rnf": dict(extraer_requerimientos(texto2, "RNF")),
        "cajones": extraer_alcance(texto2),
        "criterios": extraer_criterios(texto4),
        "hitos": extraer_hitos(texto5),
        "texto4": texto4,
        "texto5": texto5,
        "disponibles": presupuesto["disponibles"],
        "margen": presupuesto["margen"],
    }

    return ficha