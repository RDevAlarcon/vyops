import json
from collections import Counter

from google.genai import types
import time

from google import genai
# Dataset de clasificación de solicitudes municipales.
# Cada entrada debe producir un JSON con intención y prioridad.

ejemplos_raw = [
    (
        "Quiero saber en qué estado está mi solicitud municipal.",
        {"intencion": "consulta_estado", "prioridad": "baja"},
    ),
    (
        "Mi trámite lleva varios días pendiente y necesito conocer su avance.",
        {"intencion": "consulta_estado", "prioridad": "media"},
    ),
    (
        "Necesito conocer urgentemente el estado de mi solicitud porque vence mañana.",
        {"intencion": "consulta_estado", "prioridad": "alta"},
    ),
    (
        "Quiero ingresar una solicitud para reparar una banca de la plaza.",
        {"intencion": "nueva_solicitud", "prioridad": "baja"},
    ),
    (
        "Necesito solicitar la reparación de una luminaria que no funciona.",
        {"intencion": "nueva_solicitud", "prioridad": "media"},
    ),
    (
        "Hay un árbol con riesgo de caída sobre la vía pública y necesito reportarlo.",
        {"intencion": "nueva_solicitud", "prioridad": "alta"},
    ),
    (
        "Quiero cancelar una solicitud que ingresé por equivocación.",
        {"intencion": "cancelacion", "prioridad": "baja"},
    ),
    (
        "Necesito anular un trámite pendiente porque los datos son incorrectos.",
        {"intencion": "cancelacion", "prioridad": "media"},
    ),
    (
        "Solicito cancelar urgentemente una gestión que vence hoy.",
        {"intencion": "cancelacion", "prioridad": "alta"},
    ),
    (
        "Quiero presentar un reclamo por la limpieza de una plaza.",
        {"intencion": "reclamo", "prioridad": "baja"},
    ),
    (
        "La recolección de basura lleva varios días sin realizarse en mi calle.",
        {"intencion": "reclamo", "prioridad": "media"},
    ),
    (
        "Necesito denunciar una situación peligrosa que ya provocó un accidente.",
        {"intencion": "reclamo", "prioridad": "alta"},
    ),
]

ejemplos = [
    types.TuningExample(
        text_input=texto,
        output=json.dumps(salida, ensure_ascii=False),
    )
    for texto, salida in ejemplos_raw
]

def chequear_balance(
    datos: list[tuple[str, dict]],
    clave: str = "intencion",
) -> Counter:
    """Cuenta los ejemplos por categoría."""
    categorias = Counter(
        salida[clave]
        for _, salida in datos
    )
    return categorias

INTENCIONES_VALIDAS = {
    "consulta_estado",
    "nueva_solicitud",
    "cancelacion",
    "reclamo",
}

PRIORIDADES_VALIDAS = {
    "baja",
    "media",
    "alta",
}

def validar_dataset(
    ejemplos: list[types.TuningExample],
    claves_esperadas: tuple[str, ...] = ("intencion", "prioridad"),
) -> list[str]:
    """Valida el formato de los ejemplos de entrenamiento."""
    problemas = []
    vistos = set()

    for i, ejemplo in enumerate(ejemplos):
        entrada = ejemplo.text_input
        salida_texto = ejemplo.output

        if not entrada or not entrada.strip():
            problemas.append(f"ejemplo {i}: text_input vacío")

        if not salida_texto or not salida_texto.strip():
            problemas.append(f"ejemplo {i}: output vacío")
            continue

        if entrada in vistos:
            problemas.append(f"ejemplo {i}: text_input duplicado")

        vistos.add(entrada)

        try:
            salida = json.loads(salida_texto)
        except json.JSONDecodeError:
            problemas.append(f"ejemplo {i}: output no es JSON válido")
            continue

        if not isinstance(salida, dict):
            problemas.append(f"ejemplo {i}: output debe ser un objeto JSON")
            continue

        for clave in claves_esperadas:
            if clave not in salida:
                problemas.append(
                    f"ejemplo {i}: output no tiene la clave '{clave}'"
                )
        if "intencion" in salida:
            if salida["intencion"] not in INTENCIONES_VALIDAS:
                problemas.append(
                    f"ejemplo {i}: intención no permitida"
                )

        if "prioridad" in salida:
            if salida["prioridad"] not in PRIORIDADES_VALIDAS:
                problemas.append(
                    f"ejemplo {i}: prioridad no permitida"
                )

    return problemas

def esperar_a_que_termine(
    client: genai.Client,
    nombre_trabajo: str,
    intervalo_segundos: int = 30,
) -> types.TuningJob:
    """Consulta periódicamente el estado de un trabajo de tuning."""
    if intervalo_segundos <= 0:
        raise ValueError("El intervalo debe ser mayor que cero")

    estados_finales = {
        types.JobState.JOB_STATE_SUCCEEDED,
        types.JobState.JOB_STATE_FAILED,
        types.JobState.JOB_STATE_CANCELLED,
        types.JobState.JOB_STATE_PARTIALLY_SUCCEEDED,
    }

    while True:
        trabajo = client.tunings.get(name=nombre_trabajo)

        print(f"Estado actual: {trabajo.state}")

        if trabajo.state in estados_finales:
            return trabajo

        time.sleep(intervalo_segundos)


if __name__ == "__main__":
    balance = chequear_balance(ejemplos_raw)

    print("\n--- BALANCE DEL DATASET ---")
    for categoria, cantidad in balance.most_common():
        print(f"{categoria}: {cantidad}")

    print(f"\nTotal de ejemplos: {len(ejemplos)}")
    print("\n--- VALIDACIÓN DEL DATASET ---")

    problemas = validar_dataset(ejemplos)

    print(
        f"{len(ejemplos)} ejemplos, "
        f"{len(problemas)} problemas encontrados"
    )

    for problema in problemas:
        print("-", problema)



    print("\n--- PRUEBA NEGATIVA ---")

    ejemplos_invalidos = [
        types.TuningExample(
            text_input="",
            output='{"intencion": "reclamo", "prioridad": "alta"}',
        ),
        types.TuningExample(
            text_input="Solicitud duplicada",
            output='{"intencion": "reclamo", "prioridad": "media"}',
        ),
        types.TuningExample(
            text_input="Solicitud duplicada",
            output='{"intencion": "reclamo", "prioridad": "baja"}',
        ),
        types.TuningExample(
            text_input="Quiero consultar mi trámite",
            output="Esto no es JSON",
        ),
        types.TuningExample(
            text_input="Necesito ingresar una solicitud",
            output='{"intencion": "nueva_solicitud"}',
        ),
    ]

    problemas_negativos = validar_dataset(ejemplos_invalidos)

    print(f"Problemas detectados: {len(problemas_negativos)}")

    for problema in problemas_negativos:
        print("-", problema)