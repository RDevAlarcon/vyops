
"""Evaluación inicial de modelos Gemini para VyOps.

Ejecuta cinco pruebas secuenciales y guarda las métricas
para una futura comparación de costos, latencia y calidad.
"""

import csv
import json
import time
from datetime import datetime
from pathlib import Path

from consumir_gemini import (
    MODELO,
    PRECIO_ENTRADA_MILLON,
    PRECIO_SALIDA_MILLON,
    armar_peticion,
    enviar_peticion,
    extraer_texto,
    extraer_uso_tokens,
    calcular_costo,
)


# Casos de prueba representativos de las funciones de VyOps.
PREGUNTAS = [
    {
        "id": 1,
        "categoria": "Atención al cliente",
        "pregunta": (
            "Un cliente pregunta por el horario de una empresa, "
            "pero no tenemos ese dato. ¿Cómo responderías? "
            "Redacta una respuesta breve para el cliente."
        ),
    },
    {
        "id": 2,
        "categoria": "Clasificación",
        "pregunta": (
            'Clasifica "Necesito cambiar mi reserva de mañana" '
            "como ventas, soporte o reservas. "
            'Devuelve solo JSON con la clave "categoria".'
        ),
    },
    {
        "id": 3,
        "categoria": "Extracción de datos",
        "pregunta": (
            'Extrae nombre, servicio y fecha de: '
            '"Soy Ana, necesito una limpieza el 20 de octubre". '
            "Devuelve solo JSON. No inventes el año."
        ),
    },
    {
        "id": 4,
        "categoria": "Selección de herramientas",
        "pregunta": (
            "Un usuario solicita consultar el estado de su "
            "pedido 1234. ¿Qué herramienta necesitarías y "
            "qué harías antes de responder? "
            "No inventes el estado del pedido."
        ),
    },
    {
        "id": 5,
        "categoria": "Operaciones empresariales",
        "pregunta": (
            "Una pyme recibe pedidos por WhatsApp y los copia "
            "manualmente a Excel. Propón tres mejoras "
            "priorizadas y explica brevemente sus beneficios."
        ),
    },
]


# Carpeta de resultados dentro del repositorio.
CARPETA_RESULTADOS = (
    Path(__file__).resolve().parent.parent / "resultados"
)


def cargar_resultados() -> list[dict]:
    """Recupera los resultados existentes del modelo activo.

    Si todavía no existe un archivo, devuelve una lista vacía.
    """
    ruta_json = CARPETA_RESULTADOS / f"{MODELO}_pruebas.json"

    if not ruta_json.exists():
        return []

    with ruta_json.open("r", encoding="utf-8") as archivo:
        resultados = json.load(archivo)

    if not isinstance(resultados, list):
        raise ValueError("El archivo de resultados no contiene una lista.")

    return resultados

def ejecutar_prueba(caso: dict) -> dict:
    """Ejecuta una consulta y registra sus métricas reales."""

    resultado = {
        "fecha": datetime.now().astimezone().isoformat(),
        "modelo": MODELO,
        "id_pregunta": caso["id"],
        "categoria": caso["categoria"],
        "pregunta": caso["pregunta"],
        "estado": "error",
        "respuesta": "",
        "tiempo_segundos": None,
        "tokens_entrada": None,
        "tokens_salida": None,
        "tokens_razonamiento": None,
        "tokens_totales": None,
        "costo_estimado_usd": None,
        "error": "",
    }

    try:
        # Construimos la petición utilizando el cliente existente.
        url, encabezados, cuerpo = armar_peticion(caso["pregunta"])

        # Medimos exclusivamente la comunicación con Gemini.
        inicio = time.perf_counter()

        try:
            datos = enviar_peticion(url, encabezados, cuerpo)
        finally:
            resultado["tiempo_segundos"] = round(
                time.perf_counter() - inicio, 3
            )

        # Extraemos la respuesta y el consumo informado.
        respuesta = extraer_texto(datos)
        uso = extraer_uso_tokens(datos)

        costo = calcular_costo(
            datos,
            PRECIO_ENTRADA_MILLON,
            PRECIO_SALIDA_MILLON,
        )

        resultado.update(
            {
                "estado": "exito",
                "respuesta": respuesta,
                "tokens_entrada": uso["tokens_entrada"],
                "tokens_salida": uso["tokens_salida"],
                "tokens_razonamiento": uso["tokens_razonamiento"],
                "tokens_totales": uso["tokens_totales"],
                "costo_estimado_usd": costo,
            }
        )

    except (ValueError, RuntimeError) as error:
        resultado["error"] = str(error)

    return resultado


def guardar_resultados(resultados: list[dict]) -> None:
    """Guarda las mediciones en JSON y CSV separados por modelo."""

    CARPETA_RESULTADOS.mkdir(parents=True, exist_ok=True)

    ruta_json = CARPETA_RESULTADOS / f"{MODELO}_pruebas.json"
    ruta_csv = CARPETA_RESULTADOS / f"{MODELO}_pruebas.csv"

    # JSON conserva las respuestas completas para evaluar calidad.
    with ruta_json.open("w", encoding="utf-8") as archivo:
        json.dump(resultados, archivo, ensure_ascii=False, indent=2)

    # CSV facilita la comparación posterior de métricas.
    with ruta_csv.open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(
            archivo,
            fieldnames=list(resultados[0].keys()),
        )
        escritor.writeheader()
        escritor.writerows(resultados)

    print(f"\nJSON guardado: {ruta_json}")
    print(f"CSV guardado:  {ruta_csv}")

def main() -> None:
    """Reanuda las pruebas pendientes sin repetir las exitosas."""

    # Recuperamos las ejecuciones anteriores del modelo activo.
    resultados = cargar_resultados()

    # Identificamos las preguntas que ya fueron completadas.
    preguntas_exitosas = {
        resultado["id_pregunta"]
        for resultado in resultados
        if resultado.get("modelo") == MODELO
        and resultado.get("estado") == "exito"
    }

    print(f"\nModelo evaluado: {MODELO}")
    print(f"Preguntas configuradas: {len(PREGUNTAS)}")
    print(f"Preguntas ya completadas: {len(preguntas_exitosas)}")

    for caso in PREGUNTAS:
        # No repetimos las preguntas que ya respondieron correctamente.
        if caso["id"] in preguntas_exitosas:
            print(
                f"\nPrueba {caso['id']}: "
                "ya completada, se omite."
            )
            continue

        print(
            f"\nPrueba {caso['id']}/{len(PREGUNTAS)}: "
            f"{caso['categoria']}"
        )

        resultado = ejecutar_prueba(caso)

        # Conservamos el historial, incluso si hubo un error.
        resultados.append(resultado)

        print(f"Estado: {resultado['estado']}")
        print(f"Tiempo: {resultado['tiempo_segundos']} s")
        print(f"Tokens totales: {resultado['tokens_totales']}")
        print(
            "Costo estimado: "
            f"USD {resultado['costo_estimado_usd']}"
        )

        if resultado["error"]:
            print(f"Error: {resultado['error']}")

        # Guardamos todas las ejecuciones anteriores y la nueva.
        guardar_resultados(resultados)

        if resultado["estado"] == "error":
            print("\nPruebas detenidas para revisar el error.")
            break

        preguntas_exitosas.add(caso["id"])

    # El resumen considera únicamente las preguntas exitosas.
    exitosas = [
        resultado
        for resultado in resultados
        if resultado.get("modelo") == MODELO
        and resultado.get("estado") == "exito"
    ]

    tiempos = [
        resultado["tiempo_segundos"]
        for resultado in exitosas
        if resultado.get("tiempo_segundos") is not None
    ]

    costo_total = sum(
        resultado["costo_estimado_usd"]
        for resultado in exitosas
        if resultado.get("costo_estimado_usd") is not None
    )

    print("\n--- Resumen del modelo ---")
    print(f"Preguntas completadas: {len(preguntas_exitosas)}/{len(PREGUNTAS)}")

    if tiempos:
        print(
            f"Latencia promedio: "
            f"{sum(tiempos) / len(tiempos):.3f} segundos"
        )

    print(f"Costo estimado acumulado: USD {costo_total:.8f}")



if __name__ == "__main__":
    main()