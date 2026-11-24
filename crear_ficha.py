"""Generador de la ficha de diseño funcional de VyOps.

Actividad correspondiente al Bloque 33 de SkillNest.
Genera la estructura inicial del documento de diseño
sin sobrescribir archivos existentes.
"""

from pathlib import Path


# Ruta relativa a la ubicación del script.
RUTA_FICHA = (
    Path(__file__).resolve().parent
    / "docs"
    / "ficha_diseno_funcional.md"
)


PLANTILLA = """# Ficha de Diseño Funcional

## 1. Problema de negocio

[COMPLETAR: describir el problema de negocio]

## 2. Requerimientos y alcance (MVP)

### Requerimientos funcionales

[COMPLETAR: definir los requerimientos funcionales]

### Requerimientos no funcionales

[COMPLETAR: definir los requerimientos no funcionales]

### Alcance

[COMPLETAR: clasificar los requerimientos funcionales]

## 3. Arquitectura de la solución

[COMPLETAR: documentar las decisiones de arquitectura]

Diagrama: docs/diagrama_arquitectura.png

## 4. Criterios de aceptación

[PENDIENTE: se completa en el Bloque 34]

## 5. Plan de construcción por hitos

[PENDIENTE: se completa en el Bloque 34]
"""


def crear_ficha() -> None:
    """Genera la plantilla sin sobrescribir documentos existentes."""

    RUTA_FICHA.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        with RUTA_FICHA.open("x", encoding="utf-8") as archivo:
            archivo.write(PLANTILLA)

    except FileExistsError:
        print("AVISO: La ficha de diseño funcional ya existe.")
        print("No se ha sobrescrito el archivo.")
        return

    print("Ficha de diseño funcional creada correctamente.")
    print(f"Ubicacion: {RUTA_FICHA}")


if __name__ == "__main__":
    crear_ficha()