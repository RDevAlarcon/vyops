
"""Matriz de riesgos del asistente municipal VyOps."""

from tabulate import tabulate


# Riesgos identificados durante el Bloque 32 de SkillNest.
RIESGOS = [
    {
        "riesgo": "Inyección de prompt en documentos recuperados",
        "probabilidad": 4,
        "impacto": 4,
        "mitigacion": "Filtrar documentos y aislar el contexto no confiable.",
    },
    {
        "riesgo": "Exposición de datos personales en logs",
        "probabilidad": 3,
        "impacto": 5,
        "mitigacion": "Evitar registrar datos sensibles y revisar los logs.",
    },
    {
        "riesgo": "Respuesta municipal sin respaldo documental",
        "probabilidad": 3,
        "impacto": 4,
        "mitigacion": "Exigir citas y responder solo con evidencia recuperada.",
    },
    {
        "riesgo": "Documentos municipales desactualizados",
        "probabilidad": 3,
        "impacto": 3,
        "mitigacion": "Controlar vigencia y actualización de las fuentes.",
    },
    {
        "riesgo": "Cambio de prompt sin aprobación humana",
        "probabilidad": 2,
        "impacto": 4,
        "mitigacion": "Exigir aprobación explícita antes de aplicar cambios.",
    },
]


def clasificar_riesgo(probabilidad: int, impacto: int):
    """Calcula el puntaje y la categoría de un riesgo."""

    if not (1 <= probabilidad <= 5):
        raise ValueError("La probabilidad debe estar entre 1 y 5.")

    if not (1 <= impacto <= 5):
        raise ValueError("El impacto debe estar entre 1 y 5.")

    puntaje = probabilidad * impacto

    if puntaje >= 15:
        categoria = "CRÍTICO"
    elif puntaje >= 9:
        categoria = "ALTO"
    elif puntaje >= 4:
        categoria = "MEDIO"
    else:
        categoria = "BAJO"

    return puntaje, categoria


def esta_en_el_limite(probabilidad: int, impacto: int) -> bool:
    """Detecta si un cambio de un punto altera la categoría."""

    _, categoria_original = clasificar_riesgo(
        probabilidad,
        impacto,
    )

    variaciones = [
        (probabilidad - 1, impacto),
        (probabilidad + 1, impacto),
        (probabilidad, impacto - 1),
        (probabilidad, impacto + 1),
    ]

    for nueva_probabilidad, nuevo_impacto in variaciones:
        if not (
            1 <= nueva_probabilidad <= 5
            and 1 <= nuevo_impacto <= 5
        ):
            continue

        _, nueva_categoria = clasificar_riesgo(
            nueva_probabilidad,
            nuevo_impacto,
        )

        if nueva_categoria != categoria_original:
            return True

    return False


def obtener_riesgos_ordenados():
    """Ordena los riesgos de mayor a menor puntuación."""

    return sorted(
        RIESGOS,
        key=lambda riesgo: (
            riesgo["probabilidad"] * riesgo["impacto"]
        ),
        reverse=True,
    )


def mostrar_detalle_riesgos():
    """Muestra los riesgos y sus controles individualmente."""

    print("=== DETALLE DE RIESGOS VYOPS ===")

    for riesgo in obtener_riesgos_ordenados():
        probabilidad = riesgo["probabilidad"]
        impacto = riesgo["impacto"]

        puntaje, categoria = clasificar_riesgo(
            probabilidad,
            impacto,
        )

        en_limite = esta_en_el_limite(
            probabilidad,
            impacto,
        )

        print(f"\nRiesgo: {riesgo['riesgo']}")
        print(f"Probabilidad: {probabilidad}")
        print(f"Impacto: {impacto}")
        print(f"Puntaje: {puntaje}")
        print(f"Categoría: {categoria}")
        print(f"Mitigación: {riesgo['mitigacion']}")

        print(
            "Caso límite:",
            "SÍ - revisar clasificación"
            if en_limite
            else "NO",
        )

        if categoria in ("ALTO", "CRÍTICO"):
            print("Supervisión humana: REQUERIDA")
        else:
            print("Supervisión humana: Según procedimiento")


def mostrar_tabla_riesgos():
    """Construye y muestra la tabla comparativa de riesgos."""

    filas = []

    for riesgo in obtener_riesgos_ordenados():
        probabilidad = riesgo["probabilidad"]
        impacto = riesgo["impacto"]

        puntaje, categoria = clasificar_riesgo(
            probabilidad,
            impacto,
        )

        limite = (
            "SÍ"
            if esta_en_el_limite(probabilidad, impacto)
            else "NO"
        )

        supervision = (
            "REQUERIDA"
            if categoria in ("ALTO", "CRÍTICO")
            else "SEGÚN PROCEDIMIENTO"
        )

        filas.append([
            riesgo["riesgo"],
            probabilidad,
            impacto,
            puntaje,
            categoria,
            riesgo["mitigacion"],
            limite,
            supervision,
        ])

    encabezados = [
        "RIESGO",
        "PROBABILIDAD",
        "IMPACTO",
        "PUNTAJE",
        "CATEGORÍA",
        "MITIGACIÓN",
        "LÍMITE",
        "SUPERVISIÓN",
    ]

    print("\n=== MATRIZ DE RIESGOS VYOPS ===\n")

    print(
        tabulate(
            filas,
            headers=encabezados,
            tablefmt="grid",
            stralign="left",
            numalign="center",
            maxcolwidths=[
                35, None, None, None,
                None, 45, None, 20,
            ],
        )
    )


def main():
    """Ejecuta una sola vez el informe completo de riesgos."""

    mostrar_detalle_riesgos()
    mostrar_tabla_riesgos()


if __name__ == "__main__":
    main()
