def estimar_costo_de_etiquetar(
    num_ejemplos: int,
    minutos_por_ejemplo: float,
    costo_por_hora: float,
) -> tuple[float, float]:
    """Estima horas de trabajo y costo de etiquetar ejemplos."""
    horas = (num_ejemplos * minutos_por_ejemplo) / 60
    costo = horas * costo_por_hora
    return horas, costo


if __name__ == "__main__":
    horas_base, costo_base = estimar_costo_de_etiquetar(500, 4, 20)
    horas_revision, costo_revision = estimar_costo_de_etiquetar(
        500 * 0.20, 2, 20
    )

    total_horas = horas_base + horas_revision
    total_costo = costo_base + costo_revision
    jornadas = total_horas / 8

    print(f"Etiquetado base: {horas_base:.2f} horas, USD {costo_base:.2f}")
    print(f"Segunda revisión: {horas_revision:.2f} horas, USD {costo_revision:.2f}")
    print(f"Total: {total_horas:.2f} horas, USD {total_costo:.2f}")
    print(f"Jornadas de 8 horas: {jornadas:.1f}")