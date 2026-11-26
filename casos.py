"""Casos compartidos de pruebas del contrato HTTP de VyOps.

La misma matriz puede ejecutarse mediante TestClient o mediante
un cliente HTTP externo, sin duplicar las solicitudes.
"""

PREGUNTA_DOCUMENTAL = (
    "¿Cuál es el horario de atención presencial los viernes?"
)

PREGUNTA_NEGATIVA = (
    "¿Cuál es el presupuesto municipal aprobado para construir "
    "un hospital en Valle Claro durante 2035?"
)

FUENTE_ESPERADA = "atencion_ciudadana/canales_horarios.md"

PREGUNTA_LARGA = "a" * 600


CASOS = [
    # Casos válidos.
    {
        "id": "V-01",
        "descripcion": "Consulta documental válida (CA-01 y CA-02)",
        "metodo": "POST",
        "ruta": "/consultas",
        "json": {"pregunta": PREGUNTA_DOCUMENTAL},
        "estado": 200,
        "contiene": FUENTE_ESPERADA,
    },
    {
        "id": "V-02",
        "descripcion": "Abstención segura sin evidencia (CA-03)",
        "metodo": "POST",
        "ruta": "/consultas",
        "json": {"pregunta": PREGUNTA_NEGATIVA},
        "estado": 200,
        "contiene": "abstencion_segura",
    },
    {
        "id": "V-03",
        "descripcion": "Disponibilidad del servicio",
        "metodo": "GET",
        "ruta": "/salud",
        "estado": 200,
        "contiene": "ok",
    },
    {
        "id": "V-04",
        "descripcion": "Consulta válida con espacios exteriores",
        "metodo": "POST",
        "ruta": "/consultas",
        "json": {
            "pregunta": f"   {PREGUNTA_DOCUMENTAL}   "
        },
        "estado": 200,
        "contiene": FUENTE_ESPERADA,
    },

    # Casos inválidos.
    {
        "id": "I-01",
        "descripcion": "Campo obligatorio ausente",
        "metodo": "POST",
        "ruta": "/consultas",
        "json": {},
        "estado": 422,
        "contiene": "El campo es obligatorio.",
    },
    {
        "id": "I-02",
        "descripcion": "Pregunta vacía",
        "metodo": "POST",
        "ruta": "/consultas",
        "json": {"pregunta": ""},
        "estado": 422,
        "contiene": "Debe contener al menos 3 caracteres.",
    },
    {
        "id": "I-03",
        "descripcion": "Pregunta con solo espacios",
        "metodo": "POST",
        "ruta": "/consultas",
        "json": {"pregunta": "     "},
        "estado": 422,
        "contiene": "Debe contener al menos 3 caracteres.",
    },
    {
        "id": "I-04",
        "descripcion": "Pregunta inferior a la longitud mínima",
        "metodo": "POST",
        "ruta": "/consultas",
        "json": {"pregunta": "ab"},
        "estado": 422,
        "contiene": "Debe contener al menos 3 caracteres.",
    },
    {
        "id": "I-05",
        "descripcion": "Pregunta superior a la longitud máxima",
        "metodo": "POST",
        "ruta": "/consultas",
        "json": {"pregunta": PREGUNTA_LARGA},
        "estado": 422,
        "contiene": "Debe contener como máximo 500 caracteres.",
    },
    {
        "id": "I-06",
        "descripcion": "Pregunta de tipo numérico",
        "metodo": "POST",
        "ruta": "/consultas",
        "json": {"pregunta": 123},
        "estado": 422,
        "contiene": "El campo debe ser una cadena de texto.",
    },
    {
        "id": "I-07",
        "descripcion": "Cuerpo JSON malformado",
        "metodo": "POST",
        "ruta": "/consultas",
        "contenido": '{"pregunta":',
        "estado": 422,
        "contiene": "El cuerpo de la solicitud no contiene JSON válido.",
    },
    {
        "id": "I-08",
        "descripcion": "Ruta inexistente",
        "metodo": "GET",
        "ruta": "/inexistente",
        "estado": 404,
        "contiene": "NO_ENCONTRADO",
    },
    {
        "id": "I-09",
        "descripcion": "Método HTTP incorrecto",
        "metodo": "GET",
        "ruta": "/consultas",
        "estado": 405,
        "contiene": "METODO_NO_PERMITIDO",
    },
    {
        "id": "I-10",
        "descripcion": "Pregunta con valor nulo",
        "metodo": "POST",
        "ruta": "/consultas",
        "json": {"pregunta": None},
        "estado": 422,
        "contiene": "El campo debe ser una cadena de texto.",
    },
]


def ejecutar_caso(cliente, caso):
    """Envia el caso con cualquier cliente que tenga .request()."""
    if "contenido" in caso:
        r = cliente.request(
            caso["metodo"], caso["ruta"],
            content=caso["contenido"],
            headers={"Content-Type": "application/json"},
        )
    else:
        r = cliente.request(
            caso["metodo"], caso["ruta"], json=caso.get("json")
        )
    ok = r.status_code == caso["estado"] and caso["contiene"] in r.text
    return ok, r.status_code, r.text