"""Verifica los endpoints y criterios de aceptación de VyOps."""

import argparse
from unittest.mock import patch

from fastapi.testclient import TestClient

from servicio.main import app


cliente = TestClient(app)

PREGUNTA = (
    "¿Cuál es el horario de atención presencial los viernes?"
)

PREGUNTA_NEGATIVA = (
    "¿Cuál es el presupuesto municipal aprobado para construir "
    "un hospital en Valle Claro durante 2035?"
)

FUENTE_ESPERADA = "atencion_ciudadana/canales_horarios.md"

CAMPOS_RESPUESTA = {
    "trace_id",
    "respuesta",
    "fuentes",
    "estado",
}


def esquema() -> dict:
    """Obtiene el contrato OpenAPI del servicio."""
    respuesta = cliente.get("/openapi.json")
    respuesta.raise_for_status()
    return respuesta.json()


def docs_navegables() -> tuple[bool, str]:
    """DOC-1: comprueba la documentación automática."""
    contrato = esquema()
    rutas = contrato["paths"]

    ok = (
        cliente.get("/docs").status_code == 200
        and cliente.get("/redoc").status_code == 200
        and "get" in rutas.get("/salud", {})
        and "post" in rutas.get("/consultas", {})
    )

    return ok, f"Rutas documentadas: {sorted(rutas)}"


def campos_documentados() -> tuple[bool, str]:
    """DOC-2: comprueba las descripciones de los modelos."""
    esquemas = esquema()["components"]["schemas"]

    sin_descripcion = [
        f"{nombre}.{campo}"
        for nombre in ("Consulta", "Respuesta", "Salud")
        for campo, datos in esquemas[nombre]["properties"].items()
        if not datos.get("description")
    ]

    return (
        not sin_descripcion,
        f"Campos sin descripción: {sin_descripcion}"
        if sin_descripcion
        else "Todos los campos tienen descripción",
    )


def documentacion_endpoints() -> tuple[bool, str]:
    """DOC-3: comprueba resúmenes, grupos y ejemplos."""
    contrato = esquema()

    operaciones = [
        contrato["paths"]["/salud"]["get"],
        contrato["paths"]["/consultas"]["post"],
    ]

    pregunta = contrato["components"]["schemas"][
        "Consulta"
    ]["properties"]["pregunta"]

    ok = (
        all(
            operacion.get("summary")
            and operacion.get("description")
            and operacion.get("tags")
            for operacion in operaciones
        )
        and bool(pregunta.get("examples"))
    )

    return ok, "Resúmenes, descripciones, grupos y ejemplos"


def verificar_salud() -> tuple[bool, str]:
    """Comprueba la disponibilidad de la API."""
    respuesta = cliente.get("/salud")

    ok = (
        respuesta.status_code == 200
        and respuesta.json().get("estado") == "ok"
    )

    return ok, f"HTTP {respuesta.status_code}"


def consultar(
    pregunta: str,
    resultado_simulado: dict,
    real: bool = False,
):
    """Ejecuta una consulta real o una prueba controlada."""
    if real:
        return cliente.post(
            "/consultas",
            json={"pregunta": pregunta},
        )

    with patch(
        "servicio.logica.responder",
        return_value=resultado_simulado,
    ) as responder:
        respuesta = cliente.post(
            "/consultas",
            json={"pregunta": pregunta},
        )

        responder.assert_called_once_with(pregunta)

    return respuesta


def resultado_documental() -> dict:
    """Genera una respuesta controlada para pruebas HTTP."""
    return {
        "trace_id": "trace-prueba-001",
        "respuesta": (
            "El horario de atención presencial los viernes "
            "es de 08:30 a 13:00 horas."
        ),
        "fuentes": [FUENTE_ESPERADA],
        "estado": "respuesta_generada",
    }


def ca_01(real: bool = False) -> tuple[bool, str]:
    """CA-01: comprueba el contrato JSON de consulta."""
    respuesta = consultar(
        PREGUNTA,
        resultado_documental(),
        real,
    )

    datos = respuesta.json()

    ok = (
        respuesta.status_code == 200
        and CAMPOS_RESPUESTA.issubset(datos)
        and isinstance(datos["trace_id"], str)
        and isinstance(datos["respuesta"], str)
        and isinstance(datos["fuentes"], list)
        and all(
            isinstance(fuente, str)
            for fuente in datos["fuentes"]
        )
        and isinstance(datos["estado"], str)
    )

    return (
        ok,
        f"HTTP {respuesta.status_code}, "
        f"campos: {sorted(datos)}",
    )


def ca_02(real: bool = False) -> tuple[bool, str]:
    """CA-02: comprueba el horario y la fuente documental."""
    respuesta = consultar(
        PREGUNTA,
        resultado_documental(),
        real,
    )

    datos = respuesta.json()
    texto = datos.get("respuesta", "")

    ok = (
        respuesta.status_code == 200
        and datos.get("estado") == "respuesta_generada"
        and "08:30" in texto
        and "13:00" in texto
        and FUENTE_ESPERADA in datos.get("fuentes", [])
    )

    return (
        ok,
        f"Horario esperado: 08:30 a 13:00; "
        f"fuentes: {datos.get('fuentes', [])}",
    )


def ca_03(real: bool = False) -> tuple[bool, str]:
    """CA-03: comprueba la abstención ante falta de evidencia."""
    resultado = {
        "trace_id": "trace-prueba-002",
        "respuesta": "No existe evidencia documental suficiente.",
        "fuentes": [],
        "estado": "abstencion_segura",
    }

    respuesta = consultar(
        PREGUNTA_NEGATIVA,
        resultado,
        real,
    )

    datos = respuesta.json()

    ok = (
        respuesta.status_code == 200
        and CAMPOS_RESPUESTA.issubset(datos)
        and datos.get("estado") == "abstencion_segura"
        and datos.get("fuentes") == []
        and bool(datos.get("respuesta", "").strip())
    )

    return (
        ok,
        f"Estado: {datos.get('estado')}; "
        f"fuentes: {datos.get('fuentes')}",
    )


def verificar_validacion() -> tuple[bool, str]:
    """Comprueba el rechazo de solicitudes incompatibles."""
    casos = [
        {},
        {"pregunta": None},
        {"pregunta": 123},
        {"pregunta": ["consulta"]},
    ]

    estados = []

    with patch("servicio.logica.responder") as responder:
        for caso in casos:
            respuesta = cliente.post(
                "/consultas",
                json=caso,
            )

            estados.append(respuesta.status_code)

        responder.assert_not_called()

    ok = all(estado == 422 for estado in estados)

    return ok, f"Códigos HTTP obtenidos: {estados}"


def main() -> int:
    """Ejecuta las comprobaciones y comunica su resultado."""
    parser = argparse.ArgumentParser(
        description="Verificador del servicio HTTP de VyOps."
    )

    parser.add_argument(
        "--real",
        action="store_true",
        help="Ejecuta las consultas contra el RAG real.",
    )

    argumentos = parser.parse_args()

    modo = "REAL" if argumentos.real else "SIMULADO"

    comprobaciones = [
        ("DOC-1", "Documentación navegable", docs_navegables),
        ("DOC-2", "Campos documentados", campos_documentados),
        ("DOC-3", "Documentación de endpoints", documentacion_endpoints),
        ("HTTP-1", "Disponibilidad HTTP", verificar_salud),
        ("CA-01", "Contrato JSON", lambda: ca_01(argumentos.real)),
        ("CA-02", "Horario y fuente", lambda: ca_02(argumentos.real)),
        ("CA-03", "Abstención segura", lambda: ca_03(argumentos.real)),
        ("VAL-1", "Validación de entrada", verificar_validacion),
    ]

    cumplidas = 0

    print("=== VERIFICACION DEL SERVICIO VYOPS ===")
    print(f"Modo de consultas: {modo}\n")

    for identificador, descripcion, prueba in comprobaciones:
        try:
            ok, evidencia = prueba()
        except Exception as error:
            ok = False
            evidencia = f"Error: {type(error).__name__}"

        estado = "PASA" if ok else "FALLA"

        print(
            f"{estado} {identificador} "
            f"{descripcion} -> {evidencia}"
        )

        cumplidas += int(ok)

    print(
        f"\n{cumplidas} de {len(comprobaciones)} "
        "comprobaciones cumplidas"
    )

    exito = cumplidas == len(comprobaciones)

    print(f"RESULTADO: {'PASS' if exito else 'FAIL'}")

    return 0 if exito else 1


if __name__ == "__main__":
    raise SystemExit(main())