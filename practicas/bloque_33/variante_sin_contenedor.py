"""Evalúa la viabilidad del MVP sin la capa de contenerización.

Actividad experimental del Bloque 33 de SkillNest.
Comprueba que respetar el presupuesto no es suficiente
si falta una capa obligatoria de la arquitectura.
"""

from presupuesto_alcance import (
    funcionalidades,
    presupuesto,
    recortar,
    validar_mvp,
    horas_reales,
)


def main() -> None:
    """Ejecuta el escenario sin la capa de contenedor."""

    # Excluimos Docker sin modificar la lista original.
    candidatas = [
        f for f in funcionalidades
        if f["capa"] != "contenedor"
    ]

    limite = presupuesto()
    seleccionadas = recortar(candidatas, limite)

    horas_usadas = sum(
        horas_reales(f) for f in seleccionadas
    )

    errores = validar_mvp(seleccionadas, limite)

    print("=== VARIANTE SIN CONTENEDOR ===")
    print(f"Presupuesto neto: {limite:.1f} horas")
    print(f"Horas seleccionadas: {horas_usadas:.1f}")
    print(f"Horas restantes: {limite - horas_usadas:.1f}")

    print("\n=== VALIDACION DEL MVP ===")

    if errores:
        for error in errores:
            print(f"ERROR: {error}")

        print("RESULTADO: FAIL")
    else:
        print("RESULTADO: PASS")


if __name__ == "__main__":
    main()