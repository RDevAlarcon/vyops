
"""Valida VyOps con Gemini y registra trazas de auditoría.

Script de validación manual correspondiente al Bloque 23
del curso SkillNest.

Su objetivo es comprobar el comportamiento del agente
municipal VyOps mediante tres escenarios ficticios,
utilizando Gemini y las herramientas disponibles.

Escenarios definidos:

    1. Consulta de una solicitud municipal:
        Solicita consultar el estado de SOL-12345
        utilizando una herramienta del agente.

    2. Intento de cancelación con rechazo humano:
        Solicita utilizar la herramienta de cancelación
        simulada, permitiendo que el operador rechace
        manualmente la autorización.

    3. Intento de cancelación con aprobación humana:
        Solicita utilizar la herramienta de cancelación
        simulada, permitiendo que el operador apruebe
        manualmente la autorización.

Responsabilidades principales:

    - Cargar variables de entorno desde .env.
    - Construir un agente para cada escenario.
    - Incorporar supervisión humana cuando corresponde.
    - Ejecutar el agente mediante su interfaz segura.
    - Registrar las trazas de ejecución en formato JSONL.
    - Mostrar las herramientas utilizadas.
    - Mostrar la respuesta final de cada escenario.
    - Conservar evidencia para revisión posterior.

Archivo de evidencia:

    evidencias/trazas_gemini_manual_bloque_23.jsonl

Protección de evidencia:

    Si el archivo ya existe antes de comenzar,
    el script genera FileExistsError.

    Esta validación evita sobrescribir una evidencia
    previamente registrada.

Consideraciones:

    Los escenarios utilizan identificadores ficticios.

    Las decisiones humanas se solicitan mediante
    la consola durante la ejecución.

    Los nombres de los escenarios describen
    el resultado esperado, pero no fuerzan
    automáticamente una aprobación o un rechazo.

    La ejecución puede generar solicitudes reales
    al proveedor Gemini y consumir recursos de API.

IMPORTANTE:
    Este script es una herramienta de validación manual.

    No debe interpretarse como una prueba automatizada
    que garantiza el resultado de los tres escenarios.

    La ejecución debe realizarse de manera controlada
    y con autorización del operador responsable.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Path permite trabajar con la ruta del archivo
# donde se almacenarán las evidencias de auditoría.
from pathlib import Path

# load_dotenv carga variables de entorno desde .env.
#
# Estas variables pueden incluir la configuración
# necesaria para utilizar Gemini.
from dotenv import load_dotenv

# Componentes del agente municipal VyOps.
#
# construir_agente_municipal:
#     Construye el agente con sus herramientas
#     y la supervisión humana correspondiente.
#
# ejecutar_agente_seguro:
#     Ejecuta el agente mediante la interfaz
#     segura definida por el proyecto.
from src.agente_con_herramientas import (
    construir_agente_municipal,
    ejecutar_agente_seguro,
)

# registrar_traza almacena la ejecución del agente
# en un archivo de auditoría con formato JSONL.
from src.trazas_agente import registrar_traza


# ============================================================
# 2. SUPERVISIÓN HUMANA MEDIANTE CONSOLA
# ============================================================

def solicitar_aprobacion_manual() -> bool:
    """Solicita autorización explícita al operador.

    Presenta en la consola una solicitud de aprobación
    para cancelar ficticiamente la solicitud SOL-12345.

    Returns:
        bool:
            True cuando el operador introduce
            la letra "s", sin distinguir mayúsculas.

            False para cualquier otra respuesta.

    Flujo:
        1. Mostrar el encabezado de supervisión.
        2. Identificar la operación simulada.
        3. Solicitar una respuesta al operador.
        4. Eliminar espacios al inicio y al final.
        5. Convertir la respuesta a minúsculas.
        6. Devolver la decisión booleana.

    Esta función no ejecuta la cancelación.

    Únicamente proporciona la decisión humana
    que utilizará el componente de supervisión.

    La entrada se obtiene mediante input(),
    por lo que requiere interacción con la consola.
    """

    # --------------------------------------------------------
    # 2.1. PRESENTACIÓN DE LA OPERACIÓN
    # --------------------------------------------------------

    # Muestra un encabezado para distinguir
    # la intervención humana de la salida del agente.
    print("\n--- SUPERVISIÓN HUMANA ---")

    # Informa la operación ficticia
    # que requiere autorización.
    print("Operación: cancelación ficticia de SOL-12345")

    # --------------------------------------------------------
    # 2.2. CAPTURA DE LA DECISIÓN
    # --------------------------------------------------------

    # Solicita una respuesta al operador.
    #
    # strip() elimina espacios sobrantes.
    # lower() permite aceptar "s" y "S".
    respuesta = input(
        "¿Autorizar esta operación? (s/n): "
    ).strip().lower()

    # --------------------------------------------------------
    # 2.3. DEVOLUCIÓN DE LA DECISIÓN
    # --------------------------------------------------------

    # Solo la respuesta "s" representa aprobación.
    #
    # Cualquier otra entrada devuelve False.
    return respuesta == "s"


# ============================================================
# 3. EJECUCIÓN DE LOS ESCENARIOS DE VALIDACIÓN
# ============================================================

def main() -> None:
    """Ejecuta tres escenarios ficticios con Gemini.

    Prepara el entorno, construye los agentes
    y ejecuta las pruebas manuales del Bloque 23.

    Escenarios:
        gemini-consulta:
            Consulta del estado de SOL-12345.

        gemini-rechazo:
            Intento de cancelación con intervención
            del supervisor humano.

        gemini-aprobacion:
            Intento de cancelación con intervención
            del supervisor humano.

    La diferencia entre los escenarios de rechazo
    y aprobación depende de la respuesta
    proporcionada por el operador.

    Resultados:
        Cada ejecución registra:

            - Identificador de sesión.
            - Entrada enviada al agente.
            - Herramientas ejecutadas.
            - Argumentos y observaciones.
            - Respuesta final.

    Raises:
        FileExistsError:
            Cuando el archivo de evidencia
            ya existe antes de comenzar.

    La función no devuelve ningún valor.

    Los resultados se presentan en la consola
    y se almacenan en el archivo JSONL.
    """

    # --------------------------------------------------------
    # 3.1. CARGA DE CONFIGURACIÓN
    # --------------------------------------------------------

    # Carga las variables definidas en .env.
    #
    # La configuración será utilizada
    # por los componentes del agente y Gemini.
    load_dotenv(dotenv_path=".env")

    # --------------------------------------------------------
    # 3.2. DEFINICIÓN DE LA RUTA DE EVIDENCIA
    # --------------------------------------------------------

    # Establece la ubicación del archivo JSONL
    # que almacenará las trazas de los escenarios.
    ruta = Path("evidencias/trazas_gemini_manual_bloque_23.jsonl")

    # --------------------------------------------------------
    # 3.3. PROTECCIÓN CONTRA SOBRESCRITURA
    # --------------------------------------------------------

    # Comprueba si existe una evidencia previa.
    #
    # El script se detiene para evitar
    # sobrescribir o anexar datos a ese archivo
    # al iniciar una nueva validación.
    if ruta.exists():
        raise FileExistsError(
            "La evidencia ya existe. No se sobrescribirá."
        )

    # --------------------------------------------------------
    # 3.4. DEFINICIÓN DE ESCENARIOS
    # --------------------------------------------------------

    # Cada escenario contiene tres elementos:
    #
    # 1. Identificador de sesión.
    # 2. Instrucción enviada al agente.
    # 3. Función de supervisión humana o None.
    #
    # Los escenarios son ficticios
    # y utilizan la solicitud SOL-12345.
    escenarios = [
        (
            # Consulta mediante una herramienta del agente.
            "gemini-consulta",
            "Consulta el estado de SOL-12345 usando la herramienta.",

            # No se proporciona supervisor humano
            # para este escenario de consulta.
            None,
        ),
        (
            # Escenario destinado a comprobar
            # el rechazo de una cancelación.
            "gemini-rechazo",
            "Utiliza cancelar_solicitud_simulada para intentar "
            "cancelar SOL-12345. Informa el resultado real.",

            # La decisión dependerá del operador.
            solicitar_aprobacion_manual,
        ),
        (
            # Escenario destinado a comprobar
            # la aprobación de una cancelación simulada.
            "gemini-aprobacion",
            "Utiliza cancelar_solicitud_simulada para simular "
            "la cancelación de SOL-12345. Informa el resultado real.",

            # La decisión dependerá del operador.
            solicitar_aprobacion_manual,
        ),
    ]

    # --------------------------------------------------------
    # 3.5. RECORRIDO DE LOS ESCENARIOS
    # --------------------------------------------------------

    # Ejecuta los escenarios en el orden definido.
    #
    # Cada iteración dispone de su identificador,
    # instrucción y función de supervisión.
    for sesion, entrada, supervisor in escenarios:

        # ----------------------------------------------------
        # 3.6. CONSTRUCCIÓN DEL AGENTE
        # ----------------------------------------------------

        # Construye un agente municipal
        # con la configuración de supervisión
        # correspondiente al escenario actual.
        #
        # Cuando supervisor es None,
        # no se proporciona una función
        # de aprobación manual.
        agente = construir_agente_municipal(
            solicitar_aprobacion_cancelacion=supervisor,
        )

        # ----------------------------------------------------
        # 3.7. EJECUCIÓN SEGURA DEL AGENTE
        # ----------------------------------------------------

        # Envía la instrucción al agente
        # y recupera el resultado de ejecución.
        #
        # Esta llamada puede interactuar con Gemini
        # y ejecutar herramientas simuladas.
        resultado = ejecutar_agente_seguro(agente, entrada)

        # ----------------------------------------------------
        # 3.8. REGISTRO DE LA TRAZA
        # ----------------------------------------------------

        # Guarda la evidencia del escenario actual.
        #
        # registrar_traza() almacena la entrada,
        # los pasos intermedios y la respuesta final.
        #
        # El archivo JSONL se crea durante
        # el primer registro.
        registrar_traza(
            session_id=sesion,
            entrada=entrada,
            resultado=resultado,
            ruta_archivo=ruta,
        )

        # ----------------------------------------------------
        # 3.9. EXTRACCIÓN DE HERRAMIENTAS UTILIZADAS
        # ----------------------------------------------------

        # Recupera únicamente los nombres
        # de las herramientas ejecutadas.
        #
        # Cada paso intermedio contiene
        # una acción y su observación.
        herramientas = [
            accion.tool
            for accion, _ in resultado.get("intermediate_steps", [])
        ]

        # ----------------------------------------------------
        # 3.10. PRESENTACIÓN DE RESULTADOS
        # ----------------------------------------------------

        # Muestra el identificador del escenario.
        print(f"\nEscenario: {sesion}")

        # Muestra la lista de herramientas utilizadas.
        print(f"Herramientas: {herramientas}")

        # Muestra la respuesta final devuelta por el agente.
        print(f"Respuesta: {resultado.get('output')}")

    # --------------------------------------------------------
    # 3.11. CONFIRMACIÓN DE LA RUTA DE EVIDENCIA
    # --------------------------------------------------------

    # Una vez completados los escenarios,
    # informa la ubicación del archivo JSONL.
    print(f"\nEvidencia registrada en: {ruta}")


# ============================================================
# 4. PUNTO DE ENTRADA DEL SCRIPT
# ============================================================

# Ejecuta main() únicamente cuando el archivo
# se inicia directamente como programa.
#
# Si otro módulo importa este script,
# los escenarios no se ejecutan automáticamente.
if __name__ == "__main__":
    main()
