"""Calcula y valida el presupuesto de alcance del MVP de VyOps.

Actividad correspondiente al Bloque 33 del programa SkillNest.
Permite priorizar funcionalidades según el tiempo disponible
y comprobar la cobertura de las capas obligatorias del Gate 3.
"""

# Incremento aplicado a tareas con tecnologías nuevas.
FACTOR_NOVEDAD = 1.5

# Disponibilidad estimada: 20 días de 3 horas.
HORAS_DISPONIBLES = 60

# Reserva para pruebas, documentación y defensa técnica.
RESERVA_PRUEBAS_DOCS = 0.30

# Margen destinado a imprevistos durante el desarrollo.
MARGEN_IMPREVISTOS = 0.20

# Capas que deben estar presentes en el MVP del Gate 3.
CAPAS_OBLIGATORIAS = {"api", "rag", "contenedor"}

# Funcionalidades candidatas para el alcance del Gate 3.
funcionalidades = [
    {
        "id": "RF-01",
        "nombre": "Endpoint de consulta FastAPI",
        "horas": 4,
        "capa": "api",
        "tipo": "imprescindible",
        "novedad": False,
        "sistema_real": False,
    },
    {
        "id": "RF-02",
        "nombre": "Recuperacion documental con citas",
        "horas": 2,
        "capa": "rag",
        "tipo": "imprescindible",
        "novedad": False,
        "sistema_real": False,
    },
    {
        "id": "RF-03",
        "nombre": "Abstencion por evidencia insuficiente",
        "horas": 1,
        "capa": "rag",
        "tipo": "imprescindible",
        "novedad": False,
        "sistema_real": False,
    },
    {
        "id": "RF-04",
        "nombre": "Proteccion contra inyeccion de prompts",
        "horas": 2,
        "capa": "otra",
        "tipo": "imprescindible",
        "novedad": False,
        "sistema_real": False,
    },
    {
        "id": "RF-05",
        "nombre": "Trazabilidad mediante trace_id",
        "horas": 2,
        "capa": "otra",
        "tipo": "imprescindible",
        "novedad": False,
        "sistema_real": False,
    },
    {
        "id": "RNF-03",
        "nombre": "Contenerizacion con Docker",
        "horas": 4,
        "capa": "contenedor",
        "tipo": "imprescindible",
        "novedad": False,
        "sistema_real": False,
    },
    {
        "id": "RF-06",
        "nombre": "Supervision humana simulada mediante API",
        "horas": 4,
        "capa": "otra",
        "tipo": "deseable",
        "novedad": False,
        "sistema_real": False,
    },
    {
        "id": "RF-07",
        "nombre": "Panel grafico de metricas",
        "horas": 6,
        "capa": "otra",
        "tipo": "deseable",
        "novedad": False,
        "sistema_real": False,
    },
    {
        "id": "RF-08",
        "nombre": "Interfaz web con autenticacion",
        "horas": 8,
        "capa": "otra",
        "tipo": "fuera_de_alcance",
        "novedad": False,
        "sistema_real": False,
    },
    {
        "id": "RF-09",
        "nombre": "Integracion con sistemas municipales reales",
        "horas": 10,
        "capa": "otra",
        "tipo": "fuera_de_alcance",
        "novedad": True,
        "sistema_real": True,
    },
    {
        "id": "RF-10",
        "nombre": "Gestion multiempresa",
        "horas": 12,
        "capa": "otra",
        "tipo": "fuera_de_alcance",
        "novedad": False,
        "sistema_real": False,
    },
]

def horas_reales(funcionalidad: dict) -> float:
    """Calcula las horas ajustadas según la novedad tecnológica."""
    return funcionalidad["horas"] * (
        FACTOR_NOVEDAD if funcionalidad["novedad"] else 1
    )

def presupuesto(horas_disponibles: float = HORAS_DISPONIBLES) -> float:
    """Calcula las horas netas disponibles para construir el MVP.

    Permite evaluar diferentes escenarios de disponibilidad
    sin modificar la configuración original del proyecto.
    """
    neto = 1 - RESERVA_PRUEBAS_DOCS - MARGEN_IMPREVISTOS

    return round(horas_disponibles * neto, 2)

def recortar(candidatas: list[dict], limite: float) -> list[dict]:
    """Selecciona funcionalidades según prioridad y presupuesto.

    Las funcionalidades imprescindibles se conservan para detectar
    posibles excesos de presupuesto. Las deseables se incorporan
    únicamente cuando existen horas disponibles.
    """
    seleccionadas = [
        f for f in candidatas
        if f["tipo"] == "imprescindible"
        and not f["sistema_real"]
    ]

    horas_usadas = sum(horas_reales(f) for f in seleccionadas)

    for funcionalidad in candidatas:
        if funcionalidad["tipo"] != "deseable":
            continue

        if funcionalidad["sistema_real"]:
            continue

        costo = horas_reales(funcionalidad)

        if horas_usadas + costo <= limite:
            seleccionadas.append(funcionalidad)
            horas_usadas += costo

    return seleccionadas

def validar_mvp(seleccionadas: list[dict], limite: float) -> list[str]:
    """Verifica el presupuesto, las capas y los requisitos del MVP.

    Comprueba que la selección respete las restricciones
    presupuestarias y conserve todos los requisitos imprescindibles
    definidos para VyOps.
    """
    errores = []

    # Validar el presupuesto de construcción.
    horas_usadas = sum(horas_reales(f) for f in seleccionadas)

    if horas_usadas > limite:
        errores.append(
            f"Presupuesto excedido: {horas_usadas:.1f} "
            f"de {limite:.1f} horas."
        )

    # Comprobar las capas obligatorias de la arquitectura.
    capas_presentes = {f["capa"] for f in seleccionadas}
    capas_faltantes = CAPAS_OBLIGATORIAS - capas_presentes

    if capas_faltantes:
        errores.append(
            "Capas obligatorias faltantes: "
            + ", ".join(sorted(capas_faltantes))
        )

    # Obtener los identificadores imprescindibles del alcance original.
    ids_imprescindibles = {
        f["id"] for f in funcionalidades
        if f["tipo"] == "imprescindible"
    }

    ids_seleccionados = {
        f["id"] for f in seleccionadas
    }

    # Detectar requisitos imprescindibles que fueron omitidos.
    requisitos_faltantes = (
        ids_imprescindibles - ids_seleccionados
    )

    if requisitos_faltantes:
        errores.append(
            "Requisitos imprescindibles faltantes: "
            + ", ".join(sorted(requisitos_faltantes))
        )

    return errores

def obtener_excluidas(
    candidatas: list[dict],
    seleccionadas: list[dict],
) -> list[dict]:
    """Identifica las funcionalidades excluidas y sus motivos.

    Distingue entre restricciones del alcance académico,
    integraciones con sistemas reales y limitaciones
    del presupuesto disponible.
    """
    ids_seleccionados = {
        f["id"] for f in seleccionadas
    }

    excluidas = []

    for funcionalidad in candidatas:
        if funcionalidad["id"] in ids_seleccionados:
            continue

        if funcionalidad["sistema_real"]:
            motivo = "Integracion con sistemas reales"

        elif funcionalidad["tipo"] == "fuera_de_alcance":
            motivo = "Fuera del alcance academico"

        else:
            motivo = "Presupuesto insuficiente"

        excluidas.append({
            "id": funcionalidad["id"],
            "nombre": funcionalidad["nombre"],
            "horas": horas_reales(funcionalidad),
            "motivo": motivo,
        })

    return excluidas



if __name__ == "__main__":
    limite = presupuesto()
    pedido = sum(horas_reales(f) for f in funcionalidades)

    seleccionadas = recortar(funcionalidades, limite)
    horas_usadas = sum(horas_reales(f) for f in seleccionadas)

    errores = validar_mvp(seleccionadas, limite)

    excluidas = obtener_excluidas(
        funcionalidades,
        seleccionadas,
    )

    horas_excluidas = sum(
        f["horas"] for f in excluidas
    )
    print("=== PRESUPUESTO DE ALCANCE VYOPS ===")
    print(f"Horas disponibles: {HORAS_DISPONIBLES}")
    print(f"Presupuesto neto: {limite:.1f} horas")
    print(f"Total solicitado: {pedido:.1f} horas")

    print("\n=== FUNCIONALIDADES SELECCIONADAS ===")

    for funcionalidad in seleccionadas:
        print(
            f'{funcionalidad["id"]} - '
            f'{funcionalidad["nombre"]}: '
            f'{horas_reales(funcionalidad):.1f} h'
        )

    print(f"\nHoras seleccionadas: {horas_usadas:.1f}")
    print(f"Horas restantes: {limite - horas_usadas:.1f}")
    print("\n=== FUNCIONALIDADES EXCLUIDAS ===")

    if not excluidas:
        print("No existen funcionalidades excluidas.")

    for funcionalidad in excluidas:
        print(
            f'{funcionalidad["id"]} - '
            f'{funcionalidad["nombre"]}: '
            f'{funcionalidad["horas"]:.1f} h'
        )

        print(f'  Motivo: {funcionalidad["motivo"]}')

    print(f"\nHoras excluidas: {horas_excluidas:.1f}")

    print("\n=== VALIDACION DEL MVP ===")

    if errores:
        for error in errores:
            print(f"ERROR: {error}")

        print("RESULTADO: FAIL")
    else:
        print("Presupuesto respetado.")
        print("Capas obligatorias cubiertas.")
        print("RESULTADO: PASS")