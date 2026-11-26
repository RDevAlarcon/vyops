"""Aplicación FastAPI y endpoints públicos de VyOps."""

from fastapi import FastAPI

from servicio import logica
from servicio.esquemas import Consulta, Respuesta, Salud


app = FastAPI(
    title="VyOps API",
    version="0.1.0",
    description=(
        "Asistente documental municipal basado en RAG, "
        "con fuentes verificables y trazabilidad operacional."
    ),
)


@app.get(
    "/salud",
    response_model=Salud,
    tags=["sistema"],
    summary="Comprobar el servicio",
)
def salud() -> Salud:
    """Comprueba que la API HTTP está operativa."""
    return Salud(**logica.obtener_salud())


@app.post(
    "/consultas",
    response_model=Respuesta,
    tags=["consultas"],
    summary="Consultar el corpus documental municipal",
)
def consultar(consulta: Consulta) -> Respuesta:
    """Responde una pregunta documental e identifica sus fuentes."""
    return Respuesta(**logica.responder(consulta.pregunta))