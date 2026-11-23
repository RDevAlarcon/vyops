
"""Pruebas del registro de trazas y detección de repeticiones de VyOps.

Este módulo verifica el comportamiento de las funciones
de trazabilidad implementadas en src.trazas_agente.

Las pruebas cubren seis escenarios:

    1. Registro de una ejecución sin herramientas.
    2. Registro de una ejecución con una herramienta.
    3. Conservación de múltiples trazas en formato JSONL.
    4. Detección de tres llamadas consecutivas a una herramienta.
    5. Ausencia de alertas cuando las herramientas son diferentes.
    6. Manejo de un archivo de trazas inexistente.

El registro de trazas permite conservar información
sobre las interacciones y acciones ejecutadas por el agente.

La detección de repeticiones permite identificar patrones
de uso de herramientas que requieren revisión.

Las pruebas utilizan el fixture tmp_path de pytest
para trabajar con archivos temporales independientes.

No se realizan llamadas reales a Gemini ni se requiere
modificar los archivos de trazabilidad del proyecto.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Permite interpretar los registros almacenados como JSON.
import json

# Permite validar las marcas temporales de las trazas.
from datetime import datetime

# Representa una acción realizada por un agente
# mediante una herramienta de LangChain.
from langchain_core.agents import AgentAction

# Funciones del módulo de trazabilidad que se comprueban
# mediante los escenarios definidos en este archivo.
from src.trazas_agente import (
    marcar_repeticiones_sospechosas,
    registrar_traza,
)


# ============================================================
# 2. REGISTRO DE TRAZAS SIN HERRAMIENTAS
# ============================================================

def test_registrar_traza_sin_herramientas(tmp_path) -> None:
    """Verifica el registro de una ejecución sin herramientas.

    Comprueba que registrar_traza() cree un archivo JSONL
    con los datos básicos de una interacción del agente.

    Args:
        tmp_path:
            Directorio temporal proporcionado por pytest.

    Verificaciones:
        - Se crea el archivo de trazas.
        - El archivo contiene un único registro.
        - Se conserva el identificador de sesión.
        - Se conserva el texto de entrada.
        - No se registran acciones de herramientas.
        - Se conserva la respuesta final.
        - El timestamp es válido e incluye zona horaria.
    """

    # Define la ubicación temporal del archivo JSONL.
    ruta = tmp_path / "trazas.jsonl"

    # Registra una interacción simulada sin acciones
    # intermedias del agente.
    registrar_traza(
        session_id="sesion-prueba",
        entrada="Hola, VyOps.",
        resultado={
            "output": "Hola, ¿en qué puedo ayudarte?",
            "intermediate_steps": [],
        },
        ruta_archivo=ruta,
    )

    # Comprueba que se haya creado el archivo.
    assert ruta.exists()

    # Lee los registros como líneas independientes.
    registros = ruta.read_text(encoding="utf-8").splitlines()

    # Una interacción debe producir un único registro.
    assert len(registros) == 1

    # Convierte la primera línea JSON en un diccionario.
    traza = json.loads(registros[0])

    # Comprueba los datos básicos de la interacción.
    assert traza["session_id"] == "sesion-prueba"
    assert traza["entrada"] == "Hola, VyOps."

    # No deben existir acciones cuando el agente
    # no utilizó herramientas.
    assert traza["acciones"] == []

    # Comprueba que la respuesta final sea la esperada.
    assert traza["respuesta_final"] == "Hola, ¿en qué puedo ayudarte?"

    # Interpreta el timestamp en formato ISO.
    fecha = datetime.fromisoformat(traza["timestamp"])

    # Comprueba que la fecha incluya información
    # de zona horaria.
    assert fecha.tzinfo is not None


# ============================================================
# 3. REGISTRO DE TRAZAS CON HERRAMIENTAS
# ============================================================

def test_registrar_traza_con_herramienta(tmp_path) -> None:
    """Verifica el registro de una acción de herramienta.

    Simula una consulta al estado de una solicitud municipal
    utilizando un objeto AgentAction de LangChain.

    Args:
        tmp_path:
            Directorio temporal proporcionado por pytest.

    Verificaciones:
        - Se registra una acción.
        - Se conserva el nombre de la herramienta.
        - Se conservan los argumentos de entrada.
        - Se conserva la observación devuelta.

    La herramienta no se ejecuta realmente:
    su acción y resultado se proporcionan como datos
    simulados de la interacción.
    """

    # Define el archivo temporal para la prueba.
    ruta = tmp_path / "trazas.jsonl"

    # Construye una acción simulada del agente.
    #
    # La herramienta representa una consulta al estado
    # de una solicitud municipal.
    accion = AgentAction(
        tool="consultar_estado_solicitud",
        tool_input={"numero_solicitud": "SOL-12345"},
        log="Consulta simulada.",
    )

    # Registra una interacción que contiene
    # una acción y su observación correspondiente.
    registrar_traza(
        session_id="sesion-prueba",
        entrada="Consulta SOL-12345.",
        resultado={
            "output": "La solicitud está en revisión.",
            "intermediate_steps": [
                (accion, {"estado": "en_revision"}),
            ],
        },
        ruta_archivo=ruta,
    )

    # Recupera la traza registrada.
    traza = json.loads(ruta.read_text(encoding="utf-8"))

    # Comprueba que exista exactamente una acción.
    assert len(traza["acciones"]) == 1

    # Verifica el nombre de la herramienta utilizada.
    assert traza["acciones"][0]["herramienta"] == (
        "consultar_estado_solicitud"
    )

    # Comprueba que los argumentos se hayan conservado.
    assert traza["acciones"][0]["argumentos"] == {
        "numero_solicitud": "SOL-12345"
    }

    # Comprueba que se haya registrado la observación
    # correspondiente a la acción simulada.
    assert traza["acciones"][0]["observacion"] == {
        "estado": "en_revision"
    }


# ============================================================
# 4. PERSISTENCIA DE MÚLTIPLES TRAZAS
# ============================================================

def test_registrar_traza_agrega_lineas(tmp_path) -> None:
    """Comprueba que las nuevas trazas conserven las anteriores.

    Registra tres interacciones en un mismo archivo JSONL
    y verifica que los registros se acumulen.

    Args:
        tmp_path:
            Directorio temporal proporcionado por pytest.

    Verificaciones:
        - Se conservan tres registros independientes.
        - Cada registro ocupa una línea.
        - Los identificadores de sesión mantienen
          el orden en que fueron registrados.

    Esta prueba comprueba el comportamiento de agregado
    de registros, evitando que una nueva interacción
    reemplace las anteriores.
    """

    # Define un único archivo para las tres interacciones.
    ruta = tmp_path / "trazas.jsonl"

    # Registra tres ejecuciones simuladas.
    for numero in range(3):
        registrar_traza(
            session_id=f"sesion-{numero}",
            entrada=f"Consulta {numero}",
            resultado={
                "output": f"Respuesta {numero}",
                "intermediate_steps": [],
            },
            ruta_archivo=ruta,
        )

    # Recupera todas las líneas del archivo.
    registros = ruta.read_text(encoding="utf-8").splitlines()

    # Comprueba que las tres trazas estén presentes.
    assert len(registros) == 3

    # Extrae el identificador de sesión
    # de cada registro JSON.
    sesiones = [
        json.loads(linea)["session_id"]
        for linea in registros
    ]

    # Verifica que los registros se conservaron
    # en el orden de escritura.
    assert sesiones == [
        "sesion-0",
        "sesion-1",
        "sesion-2",
    ]


# ============================================================
# 5. DETECCIÓN DE LLAMADAS CONSECUTIVAS
# ============================================================

def test_detectar_tres_llamadas_consecutivas(tmp_path) -> None:
    """Verifica la detección de tres llamadas a una herramienta.

    Construye una interacción con tres acciones consecutivas
    que utilizan la misma herramienta.

    Args:
        tmp_path:
            Directorio temporal proporcionado por pytest.

    Verificaciones:
        - Se genera una única alerta.
        - La alerta identifica la sesión.
        - La alerta identifica la herramienta repetida.
        - Se registra una cantidad de tres repeticiones.

    El escenario representa un patrón de ejecución
    repetitiva que el sistema de trazabilidad
    debe señalar para su revisión.
    """

    # Define la ubicación temporal de las trazas.
    ruta = tmp_path / "trazas.jsonl"

    # Construye tres acciones simuladas
    # con el mismo nombre de herramienta.
    acciones = [
        (
            AgentAction(
                tool="consultar_documentacion",
                tool_input={"tema": "permisos"},
                log="Consulta simulada.",
            ),
            {"resultado": "Documento encontrado"},
        )
        for _ in range(3)
    ]

    # Registra una interacción con las tres acciones.
    registrar_traza(
        session_id="sesion-repetitiva",
        entrada="Consulta documentación municipal.",
        resultado={
            "output": "Consulta finalizada.",
            "intermediate_steps": acciones,
        },
        ruta_archivo=ruta,
    )

    # Analiza las trazas buscando repeticiones sospechosas.
    alertas = marcar_repeticiones_sospechosas(ruta)

    # Comprueba que se haya generado una alerta.
    assert len(alertas) == 1

    # Verifica los datos incluidos en la alerta.
    assert alertas[0]["session_id"] == "sesion-repetitiva"
    assert alertas[0]["herramienta"] == "consultar_documentacion"
    assert alertas[0]["repeticiones"] == 3


# ============================================================
# 6. AUSENCIA DE ALERTAS PARA HERRAMIENTAS DIFERENTES
# ============================================================

def test_no_alertar_herramientas_diferentes(tmp_path) -> None:
    """Comprueba que distintas herramientas no generen alertas.

    Simula una interacción con tres herramientas diferentes
    y verifica que el detector no considere esta secuencia
    como una repetición sospechosa.

    Args:
        tmp_path:
            Directorio temporal proporcionado por pytest.

    Verificaciones:
        - Se registran las acciones simuladas.
        - No se generan alertas por repetición consecutiva.

    Este escenario permite comprobar que el detector
    distingue una secuencia variada de herramientas
    de una secuencia repetitiva.
    """

    # Define el archivo temporal de trazas.
    ruta = tmp_path / "trazas.jsonl"

    # Lista de herramientas distintas
    # utilizadas en la interacción simulada.
    nombres = [
        "consultar_documentacion",
        "calcular_metricas",
        "consultar_estado_solicitud",
    ]

    # Construye una acción por cada herramienta.
    acciones = [
        (
            AgentAction(
                tool=nombre,
                tool_input={},
                log="Acción simulada.",
            ),
            {"resultado": "correcto"},
        )
        for nombre in nombres
    ]

    # Registra la interacción con acciones diferentes.
    registrar_traza(
        session_id="sesion-normal",
        entrada="Ejecutar consultas.",
        resultado={
            "output": "Consultas finalizadas.",
            "intermediate_steps": acciones,
        },
        ruta_archivo=ruta,
    )

    # Comprueba que no existan alertas
    # de repeticiones sospechosas.
    assert marcar_repeticiones_sospechosas(ruta) == []


# ============================================================
# 7. MANEJO DE ARCHIVOS INEXISTENTES
# ============================================================

def test_detector_archivo_inexistente(tmp_path) -> None:
    """Comprueba el manejo de un archivo de trazas inexistente.

    Solicita analizar una ruta donde no se ha creado
    ningún archivo JSONL.

    Args:
        tmp_path:
            Directorio temporal proporcionado por pytest.

    Verificaciones:
        - El detector devuelve una lista vacía.
        - La ausencia del archivo no genera una alerta.

    Esta prueba verifica el comportamiento esperado
    cuando todavía no existen registros para analizar.
    """

    # Construye una ruta temporal sin crear el archivo.
    ruta = tmp_path / "inexistente.jsonl"

    # Ejecuta el detector sobre la ruta inexistente.
    alertas = marcar_repeticiones_sospechosas(ruta)

    # Comprueba que no se hayan detectado alertas.
    assert alertas == []
