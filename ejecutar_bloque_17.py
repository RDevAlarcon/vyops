
"""Ejecuta y permite reanudar la evaluación del Bloque 17 de SkillNest.

Este módulo coordina la evaluación de respuestas generadas
por Gemini, reutilizando los resultados existentes del
Bloque 16 y procesando únicamente los casos pendientes.

El flujo contempla dos escenarios principales:

    1. Primera ejecución:
       Recupera las tres respuestas registradas durante
       el Bloque 16 y las utiliza como punto de partida.

    2. Ejecución posterior:
       Recupera los resultados acumulados del Bloque 17
       y continúa evaluando únicamente las consultas
       que todavía no tienen una respuesta registrada.

Los resultados del Bloque 17 se almacenan en un archivo
JSON independiente, conservando intacto el archivo
original del Bloque 16.

La persistencia incremental permite recuperar el avance
después de una interrupción, siempre que las respuestas
anteriores se hayan guardado correctamente.

Este módulo actúa como coordinador del proceso.

La lógica para cargar resultados, identificar consultas
pendientes y ejecutar las evaluaciones se encuentra
en src.evaluacion_bloque_17.

La ejecución puede realizar llamadas reales a Gemini
cuando existen consultas pendientes.

Importar este módulo no inicia automáticamente
la evaluación.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Permite construir rutas de archivos independientes
# del sistema operativo.
from pathlib import Path

# Conjunto de preguntas y referencias configuradas
# para la evaluación del Bloque 17.
from src.casos_evaluacion_bloque_17 import (
    CASOS_EVALUACION_BLOQUE_17,
)

# Funciones responsables de recuperar resultados,
# detectar consultas pendientes y continuar la evaluación.
from src.evaluacion_bloque_17 import (
    cargar_resultados_anteriores,
    evaluar_casos_pendientes,
    obtener_casos_pendientes,
)


# ============================================================
# 2. EJECUCIÓN Y REANUDACIÓN DE LA EVALUACIÓN
# ============================================================

def ejecutar_bloque_17() -> None:
    """Ejecuta o reanuda la evaluación completa del Bloque 17.

    Recupera los resultados disponibles, identifica
    los casos pendientes y solicita a Gemini únicamente
    las respuestas que todavía no están registradas.

    El comportamiento depende de la existencia
    del archivo de resultados del Bloque 17.

    Primera ejecución:
        Recupera los resultados del Bloque 16.

        Exige que existan exactamente tres respuestas
        antes de continuar con los casos adicionales.

    Ejecuciones posteriores:
        Recupera los resultados existentes del Bloque 17.

        Identifica los casos que todavía no han sido
        evaluados y continúa desde ese punto.

    Returns:
        None: Presenta el estado de la evaluación
        y la ubicación del archivo de resultados
        mediante mensajes en la terminal.

    Raises:
        ValueError:
            Si durante la primera ejecución no se recuperan
            exactamente tres respuestas del Bloque 16.

            También pueden propagarse errores de validación
            de las funciones utilizadas.

        RuntimeError:
            Si alguna dependencia informa un problema
            de ejecución o comunicación con Gemini.

    Notes:
        Esta función puede realizar llamadas reales
        a Gemini cuando existen consultas pendientes.

        Si todos los casos están evaluados, finaliza
        sin generar nuevas solicitudes.

        Los resultados se almacenan en:
            resultados/resultados_bloque_17.json

        Las rutas son relativas al directorio de trabajo
        desde el cual se ejecuta el programa.

        La función delega el guardado incremental
        a evaluar_casos_pendientes().
    """

    # --------------------------------------------------------
    # 2.1. CONFIGURACIÓN DE ARCHIVOS
    # --------------------------------------------------------

    # Archivo original que contiene los resultados
    # obtenidos durante la evaluación del Bloque 16.
    #
    # Se utiliza como fuente inicial de información
    # y no como destino de los nuevos resultados.
    ruta_bloque_16 = (
        Path("resultados") / "resultados_metricas.json"
    )

    # Archivo independiente que almacena los resultados
    # acumulados durante la evaluación del Bloque 17.
    ruta_bloque_17 = (
        Path("resultados") / "resultados_bloque_17.json"
    )

    # --------------------------------------------------------
    # 2.2. RECUPERACIÓN DE RESULTADOS EXISTENTES
    # --------------------------------------------------------

    # Intenta recuperar los resultados registrados
    # en una ejecución anterior del Bloque 17.
    #
    # Esto permite continuar después de una interrupción.
    resultados = cargar_resultados_anteriores(ruta_bloque_17)

    # Si todavía no existe el archivo del Bloque 17,
    # se considera que debe utilizarse la evaluación
    # anterior como punto de partida.
    if not ruta_bloque_17.exists():

        # Recupera las respuestas originales del Bloque 16.
        resultados = cargar_resultados_anteriores(ruta_bloque_16)

        # Comprueba que se hayan recuperado las tres
        # respuestas requeridas por el flujo original.
        #
        # Esta condición evita continuar con una base
        # incompleta de resultados previos.
        if len(resultados) != 3:
            raise ValueError(
                "Se esperaban tres respuestas del Bloque 16. "
                "Verifica resultados/resultados_metricas.json."
            )

    # --------------------------------------------------------
    # 2.3. IDENTIFICACIÓN DE CONSULTAS PENDIENTES
    # --------------------------------------------------------

    # Compara los casos configurados para el Bloque 17
    # con las respuestas previamente recuperadas.
    #
    # La función devuelve los casos que todavía
    # requieren una evaluación.
    pendientes = obtener_casos_pendientes(
        CASOS_EVALUACION_BLOQUE_17,
        resultados,
    )

    # --------------------------------------------------------
    # 2.4. PRESENTACIÓN DEL ESTADO ACTUAL
    # --------------------------------------------------------

    # Informa la cantidad de casos configurados,
    # las respuestas recuperadas y las consultas pendientes.
    print("\nBLOQUE 17 — EVALUACIÓN DE RESPUESTAS")
    print(f"Casos configurados: {len(CASOS_EVALUACION_BLOQUE_17)}")
    print(f"Respuestas recuperadas: {len(resultados)}")
    print(f"Consultas pendientes: {len(pendientes)}")

    # --------------------------------------------------------
    # 2.5. FINALIZACIÓN SIN CONSULTAS PENDIENTES
    # --------------------------------------------------------

    # Si todos los casos ya tienen resultados,
    # termina sin invocar nuevamente Gemini.
    if not pendientes:
        print("La evaluación ya está completa.")
        return

    # --------------------------------------------------------
    # 2.6. EVALUACIÓN INCREMENTAL
    # --------------------------------------------------------

    # Procesa únicamente las consultas pendientes.
    #
    # Entrega los resultados existentes para conservar
    # el avance acumulado.
    #
    # La función utilizada guarda cada nueva respuesta
    # en el archivo JSON del Bloque 17.
    resultados = evaluar_casos_pendientes(
        casos_pendientes=pendientes,
        ruta_archivo=ruta_bloque_17,
        resultados_existentes=resultados,
    )

    # --------------------------------------------------------
    # 2.7. PRESENTACIÓN DEL RESULTADO FINAL
    # --------------------------------------------------------

    # Informa la cantidad total de respuestas acumuladas
    # y el archivo utilizado para su almacenamiento.
    print("\nEVALUACIÓN FINALIZADA")
    print(f"Respuestas acumuladas: {len(resultados)}")
    print(f"Archivo: {ruta_bloque_17}")


# ============================================================
# 3. PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    # Ejecuta la evaluación únicamente cuando este archivo
    # se inicia directamente desde la terminal.
    #
    # Importar el módulo desde otro archivo no activa
    # las consultas a Gemini.

    try:
        # Inicia una evaluación nueva o reanuda
        # el progreso previamente almacenado.
        ejecutar_bloque_17()

    except (ValueError, RuntimeError) as error:
        # Informa los errores de validación o ejecución
        # contemplados por este punto de entrada.
        #
        # No elimina los resultados anteriores.
        # Una ejecución posterior puede continuar
        # utilizando los registros disponibles.
        print(f"\nEvaluación interrumpida: {error}")
