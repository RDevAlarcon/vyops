"""Generador de resumen de la ficha funcional de VyOps.

Actividad correspondiente al Bloque 34 de SkillNest.

Presenta información sobre el alcance, los requerimientos,
los criterios de aceptación, los hitos y el presupuesto
temporal para facilitar la revisión de la ficha funcional.
"""

import argparse
from pathlib import Path

from ficha_datos import RUTA_FICHA, cargar

from ficha_datos import RUTA_FICHA, cargar


def lista(elementos: list[str]) -> str:
    """Convierte una colección de identificadores en texto.

    Cuando la colección está vacía, devuelve 'ninguno'
    para facilitar la lectura del resumen.

    Args:
        elementos: Identificadores que se desean presentar.

    Returns:
        Texto con los elementos separados por comas.
    """

    return ", ".join(elementos) if elementos else "ninguno"

def resumen(ficha: dict) -> None:
    """Presenta un resumen del estado de la ficha funcional.

    Analiza los requerimientos, las categorías del alcance
    y la cobertura de los criterios de aceptación.

    Args:
        ficha: Datos estructurados obtenidos mediante cargar().
    """

    rf = ficha["rf"]
    rnf = ficha["rnf"]
    cajones = ficha["cajones"]
    criterios = ficha["criterios"]

    print("=== RESUMEN DE LA FICHA FUNCIONAL ===")

    # Cantidad de requerimientos definidos.
    print(f"\nRequerimientos funcionales: {len(rf)}")
    print(f"Requerimientos no funcionales: {len(rnf)}")

    # Clasificación del alcance del MVP.
    print("\nAlcance del MVP:")

    for categoria, identificadores in cajones.items():
        print(
            f"  {categoria.capitalize()}: "
            f"{len(identificadores)} "
            f"({lista(identificadores)})"
        )

    # Identificar los requerimientos de cobertura obligatoria.
    obligatorios = (
        set(cajones["imprescindible"]) | set(rnf)
    )

    # Identificar los requerimientos cubiertos por criterios.
    cubiertos = {
        identificador
        for criterio in criterios
        for identificador in criterio["cubre"]
    }

    # Detectar requerimientos obligatorios sin cobertura.
    faltantes = sorted(obligatorios - cubiertos)

    print(f"\nCriterios de aceptacion: {len(criterios)}")

    print(
        "Requerimientos obligatorios sin criterio: "
        + lista(faltantes)
    )
    # Obtener los datos del plan de construcción.
    hitos = ficha["hitos"]
    disponibles = ficha["disponibles"]
    margen = ficha["margen"]

    # Calcular la duración total de los hitos.
    horas_planificadas = sum(
        hito["horas"]
        for hito in hitos
    )

    print(f"\nHitos de construccion: {len(hitos)}")
    print(f"Horas planificadas: {horas_planificadas:g} h")

    # Analizar el presupuesto cuando esté definido.
    if disponibles is not None and margen is not None:

        limite = disponibles - margen
        saldo = limite - horas_planificadas

        print(f"Horas disponibles: {disponibles:g} h")
        print(f"Margen de imprevistos: {margen:g} h")
        print(f"Limite de planificacion: {limite:g} h")

        print(
            f"Presupuesto utilizado: "
            f"{horas_planificadas:g}/{limite:g} h"
        )

        if saldo >= 0:
            print("Estado del presupuesto: DENTRO DEL LIMITE")
            print(f"Horas restantes: {saldo:g} h")
        else:
            print("Estado del presupuesto: EXCEDIDO")
            print(f"Exceso de horas: {abs(saldo):g} h")

    else:
        print("Presupuesto temporal: pendiente de definir")

        # Obtener todos los criterios definidos en la ficha.
    ids_criterios = {
        criterio["id"]
        for criterio in criterios
    }

    # Obtener los criterios asociados a los hitos.
    criterios_planificados = {
        identificador
        for hito in hitos
        for identificador in hito["criterios"]
    }

    # Detectar criterios que no están asociados a ningún hito.
    criterios_huerfanos = sorted(
        ids_criterios - criterios_planificados
    )

    # Detectar hitos que no tienen criterios de aceptación.
    hitos_sin_criterios = sorted(
        hito["id"]
        for hito in hitos
        if not hito["criterios"]
    )

    print("\nTrazabilidad del plan:")

    print(
        "Criterios huerfanos: "
        + lista(criterios_huerfanos)
    )

    print(
        "Hitos sin criterios: "
        + lista(hitos_sin_criterios)
    )

def main() -> int:
    """Genera el resumen de una ficha de diseño funcional.

    Permite utilizar la ficha oficial del proyecto o una
    ruta alternativa proporcionada desde la terminal.

    Returns:
        0 si el resumen se genera correctamente.
        1 si no se encuentra la ficha funcional.
    """

    parser = argparse.ArgumentParser(
        description="Generador de resumen de ficha funcional."
    )

    parser.add_argument(
        "ruta",
        nargs="?",
        type=Path,
        default=RUTA_FICHA,
        help="Ruta alternativa de la ficha funcional.",
    )

    argumentos = parser.parse_args()
    ruta = argumentos.ruta

    if not ruta.is_file():
        print(
            "ERROR: No se encontro la ficha "
            "de diseno funcional."
        )
        return 1

    ficha = cargar(ruta)

    resumen(ficha)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())