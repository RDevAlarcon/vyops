
"""Interfaz web mínima para consultar la API de VyOps."""

import json
import os
import urllib.error
import urllib.request

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse


API_URL = os.environ.get("API_URL", "http://api:8000")

app = FastAPI(title="Interfaz de VyOps")


PAGINA = """<!doctype html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <title>VyOps - Asistente municipal</title>
</head>
<body>
    <h1>VyOps - Asistente documental municipal</h1>

    <p>Realiza una consulta sobre la documentación municipal.</p>

    <input id="q" size="60" placeholder="Escribe tu pregunta">
    <button onclick="preguntar()">Preguntar</button>

    <pre id="r"></pre>

    <script>
        async function preguntar() {
            const q = encodeURIComponent(
                document.getElementById("q").value
            );

            const r = await fetch("/preguntar?texto=" + q);

            document.getElementById("r").textContent =
                JSON.stringify(await r.json(), null, 2);
        }
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def inicio():
    """Devuelve la página principal de la interfaz."""
    return PAGINA


@app.get("/salud")
def salud():
    """Informa el estado de la interfaz y la dirección de la API."""
    return {"estado": "ok", "api": API_URL}


@app.get("/preguntar")
def preguntar(texto: str):
    """Envía la pregunta a la API y devuelve su respuesta."""
    datos = json.dumps({"pregunta": texto}).encode("utf-8")

    peticion = urllib.request.Request(
        API_URL + "/consultas",
        data=datos,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(peticion, timeout=35) as respuesta:
            return json.loads(respuesta.read())

    except urllib.error.HTTPError as error:
        return JSONResponse(
            content=json.loads(error.read()),
            status_code=error.code,
        )

    except OSError:
        return JSONResponse(
            content={
                "codigo": "api_no_disponible",
                "mensaje": "No se pudo contactar a la API.",
            },
            status_code=502,
        )
