"""Evalúa la viabilidad del MVP con diferentes disponibilidades.

Actividad experimental del Bloque 33 de SkillNest.
Permite identificar el presupuesto mínimo necesario
para conservar las funcionalidades imprescindibles.
"""

from presupuesto_alcance import (
    funcionalidades,
    presupuesto,
    recortar,
    validar_mvp,
    horas_reales,
)


def evaluar_escenario(horas_disponibles: float) -> None:
    """Evalúa y presenta los resultados de un escenario."""

    limite = presupuesto(horas_disponibles)
    seleccionadas = recortar(funcionalidades, limite)

    horas_usadas = sum(
        horas_reales(f) for f in seleccionadas
    )

    errores = validar_mvp(seleccionadas, limite)

    print(f"\n=== ESCENARIO DE {horas_disponibles:.0f} HORAS ===")
    print(f"Presupuesto neto: {limite:.1f} horas")
    print(f"Horas seleccionadas: {horas_usadas:.1f}")
    print(f"Horas restantes: {limite - horas_usadas:.1f}")

    print("\nFuncionalidades seleccionadas:")

    for funcionalidad in seleccionadas:
        print(
            f'- {funcionalidad["id"]}: '
            f'{funcionalidad["nombre"]}'
        )

    print("\nValidacion del MVP:")

    if errores:
        for error in errores:
            print(f"ERROR: {error}")

        print("RESULTADO: FAIL")
    else:
        print("RESULTADO: PASS")


def main() -> None:
    """Ejecuta los escenarios de disponibilidad definidos."""

    escenarios = [60, 40, 30, 20]

    print("=== ANALISIS DE DISPONIBILIDAD VYOPS ===")

    for horas in escenarios:
        evaluar_escenario(horas)


if __name__ == "__main__":
    main()