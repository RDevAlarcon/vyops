
from tabulate import tabulate
"""Matriz de riesgos del asistente municipal VyOps."""

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




if __name__ == "__main__":
    print("=== MATRIZ DE RIESGOS VYOPS ===")

    riesgos_ordenados = sorted(
        RIESGOS,
        key=lambda item: item["probabilidad"] * item["impacto"],
        reverse=True,
    )

    for riesgo in riesgos_ordenados:
        puntaje, categoria = clasificar_riesgo(
            riesgo["probabilidad"],
            riesgo["impacto"],
        )

        print(f"\nRiesgo: {riesgo['riesgo']}")
        print(f"Probabilidad: {riesgo['probabilidad']}")
        print(f"Impacto: {riesgo['impacto']}")
        print(f"Puntaje: {puntaje}")
        print(f"Categoría: {categoria}")
        print(f"Mitigación: {riesgo['mitigacion']}")
        en_limite = esta_en_el_limite(
            riesgo["probabilidad"],
            riesgo["impacto"],
        )

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


if __name__ == "__main__":
    filas = []

    riesgos_ordenados = sorted(
        RIESGOS,
        key=lambda r: r["probabilidad"] * r["impacto"],
        reverse=True,
    )

    for riesgo in riesgos_ordenados:
        probabilidad = riesgo["probabilidad"]
        impacto = riesgo["impacto"]

        puntaje, categoria = clasificar_riesgo(
            probabilidad, impacto
        )

        limite = (
            "SÍ" if esta_en_el_limite(probabilidad, impacto)
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

    print(tabulate(
        filas,
        headers=encabezados,
        tablefmt="grid",
        stralign="left",
        numalign="center",
        maxcolwidths=[35, None, None, None, None, 45, None, 20],
    ))
