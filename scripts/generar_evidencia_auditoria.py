
"""Genera evidencia ficticia de auditoría para VyOps.

Script de demostración correspondiente al Bloque 23
del curso SkillNest.

Su objetivo es generar registros de auditoría
a partir de escenarios simulados de autonomía
y utilización de herramientas del agente VyOps.

Este script no ejecuta el agente municipal
ni realiza consultas a modelos de lenguaje.

Construye directamente objetos AgentAction
para representar herramientas ficticias
y sus respectivos resultados.

Escenarios incluidos:

    1. Consulta de bajo riesgo:
        Representa una consulta del estado
        de la solicitud ficticia SOL-12345.

        Herramienta:
            consultar_estado_solicitud

        Resultado simulado:
            La solicitud se encuentra en revisión.

    2. Cancelación de alto riesgo:
        Representa un intento de cancelación
        de la solicitud ficticia SOL-12345.

        Herramienta:
            cancelar_solicitud_simulada

        Resultado simulado:
            Cancelación bloqueada por falta
            de aprobación humana.

Responsabilidades principales:

    - Definir la ruta de evidencia.
    - Impedir el uso de un archivo ya existente.
    - Construir acciones ficticias de herramientas.
    - Registrar dos trazas de ejecución.
    - Analizar repeticiones consecutivas.
    - Mostrar un resumen de la evidencia generada.

Archivo de salida:

    evidencias/trazas_bloque_23.jsonl

Formato:

    JSON Lines (JSONL).

    Cada línea contiene una traza independiente
    con la entrada, las acciones y la respuesta final.

Protección de evidencia:

    Si el archivo ya existe antes de comenzar,
    el script genera FileExistsError.

    De esta forma, se evita reutilizar
    accidentalmente una evidencia anterior.

IMPORTANTE:
    Los resultados son completamente ficticios.

    El estado de consulta y el bloqueo
    de cancelación se proporcionan directamente
    como datos de demostración.

    El script no demuestra por sí mismo
    que el agente real haya aplicado
    correctamente sus controles de autonomía.

    Su propósito es comprobar y demostrar
    el registro y análisis de trazas.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Path permite definir y comprobar
# la ruta del archivo de evidencia.
from pathlib import Path

# AgentAction representa una acción de herramienta
# mediante su nombre, argumentos y registro descriptivo.
#
# En este script se utiliza para construir
# acciones ficticias sin ejecutar un agente.
from langchain_core.agents import AgentAction

# Funciones de trazabilidad de VyOps.
#
# registrar_traza:
#     Almacena una ejecución en formato JSONL.
#
# marcar_repeticiones_sospechosas:
#     Analiza secuencias consecutivas
#     de herramientas dentro de las trazas.
from src.trazas_agente import (
    marcar_repeticiones_sospechosas,
    registrar_traza,
)


# ============================================================
# 2. GENERACIÓN DE EVIDENCIA DE AUDITORÍA
# ============================================================

def main() -> None:
    """Registra dos escenarios simulados de autonomía.

    Genera evidencia ficticia de una consulta municipal
    y de un intento de cancelación bloqueado.

    Flujo:
        1. Definir la ruta del archivo JSONL.
        2. Comprobar que no exista evidencia previa.
        3. Construir una acción de consulta ficticia.
        4. Registrar la traza de bajo riesgo.
        5. Construir una acción de cancelación ficticia.
        6. Registrar la traza de alto riesgo.
        7. Analizar repeticiones de herramientas.
        8. Mostrar el resumen de resultados.

    Returns:
        None:
            La función escribe la evidencia
            y muestra información en la consola.

    Raises:
        FileExistsError:
            Cuando el archivo de evidencia
            ya existe antes de comenzar.

    Resultados esperados:

        - Dos ejecuciones registradas.
        - Una traza para cada escenario.
        - Ninguna alerta por repetición consecutiva.

    La ausencia de alertas se debe a que
    cada escenario contiene una sola acción.

    Esta función no realiza llamadas a Gemini
    ni ejecuta operaciones municipales reales.
    """

    # --------------------------------------------------------
    # 2.1. DEFINICIÓN DE LA RUTA DE EVIDENCIA
    # --------------------------------------------------------

    # Establece la ubicación del archivo JSONL
    # donde se registrarán los escenarios ficticios.
    ruta = Path("evidencias/trazas_bloque_23.jsonl")

    # --------------------------------------------------------
    # 2.2. PROTECCIÓN DE EVIDENCIA EXISTENTE
    # --------------------------------------------------------

    # Comprueba que no exista un archivo anterior.
    #
    # Si existe, detiene la ejecución
    # para evitar anexar nuevos registros
    # a una evidencia previamente generada.
    if ruta.exists():
        raise FileExistsError(
            "La evidencia ya existe. No se sobrescribirá."
        )

    # ========================================================
    # 3. ESCENARIO DE BAJO RIESGO
    # ========================================================

    # --------------------------------------------------------
    # 3.1. CONSTRUCCIÓN DE LA ACCIÓN DE CONSULTA
    # --------------------------------------------------------

    # Representa una llamada ficticia
    # a la herramienta consultar_estado_solicitud.
    #
    # AgentAction almacena la descripción de la acción,
    # pero no ejecuta la herramienta.
    consulta = AgentAction(
        tool="consultar_estado_solicitud",
        tool_input={"numero_solicitud": "SOL-12345"},
        log="Consulta ficticia de bajo riesgo.",
    )

    # --------------------------------------------------------
    # 3.2. REGISTRO DE LA CONSULTA
    # --------------------------------------------------------

    # Construye y almacena una traza de bajo riesgo.
    #
    # La respuesta y el estado de la solicitud
    # son datos ficticios definidos en el script.
    #
    # intermediate_steps contiene un par:
    # acción ejecutada y observación obtenida.
    registrar_traza(
        session_id="demo-bajo-riesgo",
        entrada="Consulta el estado de SOL-12345.",
        resultado={
            "output": "La solicitud ficticia está en revisión.",
            "intermediate_steps": [
                (consulta, {"estado": "en_revision"}),
            ],
        },
        ruta_archivo=ruta,
    )

    # ========================================================
    # 4. ESCENARIO DE ALTO RIESGO
    # ========================================================

    # --------------------------------------------------------
    # 4.1. CONSTRUCCIÓN DE LA ACCIÓN DE CANCELACIÓN
    # --------------------------------------------------------

    # Representa una llamada ficticia
    # a la herramienta cancelar_solicitud_simulada.
    #
    # El escenario está diseñado para documentar
    # una operación sensible que aparece bloqueada
    # por falta de aprobación humana.
    #
    # No se solicita autorización real
    # ni se ejecuta una cancelación.
    cancelacion = AgentAction(
        tool="cancelar_solicitud_simulada",
        tool_input={"numero_solicitud": "SOL-12345"},
        log="Cancelación ficticia de alto riesgo.",
    )

    # --------------------------------------------------------
    # 4.2. REGISTRO DE LA CANCELACIÓN BLOQUEADA
    # --------------------------------------------------------

    # Almacena una traza que representa
    # el bloqueo de la cancelación ficticia.
    #
    # Tanto el mensaje de bloqueo
    # como la observación son valores simulados.
    registrar_traza(
        session_id="demo-alto-riesgo",
        entrada="Cancela la solicitud ficticia SOL-12345.",
        resultado={
            "output": "Cancelación bloqueada por falta de aprobación.",
            "intermediate_steps": [
                (cancelacion, {"estado": "bloqueada"}),
            ],
        },
        ruta_archivo=ruta,
    )

    # ========================================================
    # 5. ANÁLISIS DE TRAZAS
    # ========================================================

    # --------------------------------------------------------
    # 5.1. DETECCIÓN DE REPETICIONES
    # --------------------------------------------------------

    # Analiza las trazas registradas para identificar
    # llamadas consecutivas repetidas a herramientas.
    #
    # Se utiliza el umbral predeterminado
    # definido en marcar_repeticiones_sospechosas().
    #
    # Como cada traza contiene una sola acción,
    # no se espera encontrar repeticiones.
    alertas = marcar_repeticiones_sospechosas(ruta)

    # ========================================================
    # 6. PRESENTACIÓN DE RESULTADOS
    # ========================================================

    # --------------------------------------------------------
    # 6.1. RUTA DE EVIDENCIA
    # --------------------------------------------------------

    # Informa la ubicación del archivo generado.
    print(f"Evidencia generada: {ruta}")

    # --------------------------------------------------------
    # 6.2. CANTIDAD DE EJECUCIONES
    # --------------------------------------------------------

    # Muestra la cantidad de escenarios
    # que el script está diseñado para registrar.
    print("Ejecuciones registradas: 2")

    # --------------------------------------------------------
    # 6.3. ALERTAS DETECTADAS
    # --------------------------------------------------------

    # Informa la cantidad de alertas encontradas
    # durante el análisis de las trazas.
    print(f"Alertas por repeticiones: {len(alertas)}")


# ============================================================
# 7. PUNTO DE ENTRADA
# ============================================================

# Ejecuta main() únicamente cuando el script
# se inicia directamente.
#
# Si otro módulo importa este archivo,
# no se generan evidencias automáticamente.
if __name__ == "__main__":
    main()
