"""Ejecuta la evaluación del Bloque 17 de SkillNest.

Reutiliza resultados del Bloque 16 y genera únicamente
las respuestas pendientes mediante Gemini.

Los resultados se almacenan en un archivo independiente,
permitiendo reanudar una ejecución interrumpida.
"""

from pathlib import Path

from src.casos_evaluacion_bloque_17 import (
    CASOS_EVALUACION_BLOQUE_17,
)
from src.evaluacion_bloque_17 import (
    cargar_resultados_anteriores,
    evaluar_casos_pendientes,
    obtener_casos_pendientes,
)


def ejecutar_bloque_17() -> None:
    """Ejecuta o reanuda la evaluación completa del Bloque 17.

    Recupera los resultados disponibles, identifica los casos
    pendientes y solicita a Gemini únicamente las respuestas
    que todavía no se han registrado.

    Nota:
        Esta función realiza llamadas reales a Gemini
        cuando existen consultas pendientes.
    """

    # Conservamos intacto el archivo original del Bloque 16.
    ruta_bloque_16 = (
        Path("resultados") / "resultados_metricas.json"
    )

    # Utilizamos un archivo independiente para el Bloque 17.
    ruta_bloque_17 = (
        Path("resultados") / "resultados_bloque_17.json"
    )

    # Recuperamos los resultados del Bloque 17 si ya existe
    # una ejecución anterior o una ejecución interrumpida.
    resultados = cargar_resultados_anteriores(ruta_bloque_17)

    # Si todavía no existe el archivo del Bloque 17,
    # recuperamos las tres respuestas del Bloque 16.
    if not ruta_bloque_17.exists():
        resultados = cargar_resultados_anteriores(ruta_bloque_16)

        # Exigimos las tres respuestas originales para
        # evitar repetir consultas ya realizadas.
        if len(resultados) != 3:
            raise ValueError(
                "Se esperaban tres respuestas del Bloque 16. "
                "Verifica resultados/resultados_metricas.json."
            )

    # Identificamos las consultas todavía pendientes.
    pendientes = obtener_casos_pendientes(
        CASOS_EVALUACION_BLOQUE_17,
        resultados,
    )

    print("\nBLOQUE 17 — EVALUACIÓN DE RESPUESTAS")
    print(f"Casos configurados: {len(CASOS_EVALUACION_BLOQUE_17)}")
    print(f"Respuestas recuperadas: {len(resultados)}")
    print(f"Consultas pendientes: {len(pendientes)}")

    # Si ya tenemos todos los resultados, no consultamos Gemini.
    if not pendientes:
        print("La evaluación ya está completa.")
        return

    # Evaluamos los casos pendientes y guardamos cada
    # respuesta inmediatamente en el JSON del Bloque 17.
    resultados = evaluar_casos_pendientes(
        casos_pendientes=pendientes,
        ruta_archivo=ruta_bloque_17,
        resultados_existentes=resultados,
    )

    print("\nEVALUACIÓN FINALIZADA")
    print(f"Respuestas acumuladas: {len(resultados)}")
    print(f"Archivo: {ruta_bloque_17}")


if __name__ == "__main__":
    try:
        ejecutar_bloque_17()

    except (ValueError, RuntimeError) as error:
        # Informamos el problema sin eliminar resultados.
        # Una nueva ejecución permitirá continuar.
        print(f"\nEvaluación interrumpida: {error}")