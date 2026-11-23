"""Ejecuta y mide el pipeline RAG municipal de VyOps.

Este módulo coordina las etapas principales de una consulta RAG:

1. Generación del identificador de trazabilidad.
2. Recuperación semántica de documentos.
3. Filtrado de documentos con instrucciones sospechosas.
4. Construcción del prompt documental.
5. Generación de la respuesta mediante Gemini.
6. Extracción y registro del consumo de tokens.
7. Estimación de costos de generación y embeddings.
8. Validación de citas y aplicación de abstención segura.
9. Devolución de métricas y resultados estructurados.

Las latencias se registran por etapa para facilitar
la observabilidad y evaluación del sistema.

La función principal puede consumir la API de Gemini.
La ejecución directa también guarda un registro JSONL.
"""
import time

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from latencia_rag import medir
from recuperacion import (
    BASE_DIR,
    recuperar_documentos,
    construir_prompt,
    validar_citas,
)
from tokens_embedding import contar_tokens_embedding
from configuracion_modelos import (
    MODELO_GENERACION,
    MODELO_EMBEDDING,
)
from costos_rag import calcular_costo_rag
from persistencia_rag import guardar_registro_jsonl
from traza_contexto import generar_trace_id, trace_id_var
from logs_json import logger

from inyeccion_prompt import filtrar_documentos_langchain

def extraer_consumo(respuesta_modelo):
    """Normaliza los metadatos de consumo de una respuesta LangChain.

    Extrae los tokens de entrada, salida y totales reportados
    por el proveedor, junto con los desgloses disponibles
    de razonamiento y lectura desde caché.

    Args:
        respuesta_modelo: Respuesta de LangChain que contiene
            el atributo usage_metadata.

    Returns:
        dict: Consumo normalizado con los campos:
            - tokens_entrada: Tokens de entrada reportados.
            - tokens_salida: Tokens de salida reportados.
            - tokens_totales: Consumo total reportado.
            - tokens_razonamiento: Desglose de razonamiento.
            - tokens_cache: Tokens leídos desde caché.
            - razonamiento_reportado: Indica si existe ese desglose.
            - uso_original: Copia de los metadatos recibidos.

    Notes:
        Los valores pueden ser None cuando el proveedor no
        informa una métrica.

        Los tokens de razonamiento son un desglose del consumo
        de salida y no se suman nuevamente al total.
    """

    uso = respuesta_modelo.usage_metadata or {}

    entrada = uso.get("input_tokens")
    salida = uso.get("output_tokens")
    total = uso.get("total_tokens")

    detalles_entrada = uso.get("input_token_details") or {}
    detalles_salida = uso.get("output_token_details") or {}

    razonamiento = detalles_salida.get("reasoning")
    cache = detalles_entrada.get("cache_read")

    # El razonamiento es un desglose, no un consumo
    # adicional que debamos sumar a output_tokens.

    return {
        "tokens_entrada": entrada,
        "tokens_salida": salida,
        "tokens_totales": total,
        "tokens_razonamiento": razonamiento,
        "tokens_cache": cache,
        "razonamiento_reportado": razonamiento is not None,
        "uso_original": dict(uso),
    }

def registrar_consumo(respuesta):
    """Registra el consumo de tokens reportado por el modelo.

    Obtiene los metadatos de uso de la respuesta y emite
    un evento mediante el logger estructurado de VyOps.

    El evento contiene los tokens de entrada, salida y
    totales, asociados al evento lógico consumo_llm.

    Args:
        respuesta: Respuesta de LangChain con metadatos
            de consumo opcionales.

    Notes:
        La función no calcula costos ni devuelve métricas.
        Su responsabilidad es registrar el consumo reportado.

        El tratamiento y formato final de los eventos
        depende de la configuración de logs_json.py.
    """
    uso = respuesta.usage_metadata or {}

    logger.info(
        "consumo registrado",
        extra={
            "extra_data": {
                "evento": "consumo_llm",
                "input_tokens": uso.get("input_tokens"),
                "output_tokens": uso.get("output_tokens"),
                "total_tokens": uso.get("total_tokens"),
            }
        },
    )

def ejecutar_rag_medido(pregunta, k=5):
    """Ejecuta una consulta RAG con métricas y trazabilidad.

    Genera un identificador de traza independiente y lo establece
    en el contexto de ejecución para asociar los eventos del pipeline.

    Etapas principales:
        1. Recupera documentos mediante búsqueda vectorial.
        2. Filtra los documentos con instrucciones sospechosas.
        3. Construye el prompt con los documentos aceptados.
        4. Genera una respuesta mediante Gemini.
        5. Extrae y registra el consumo reportado por el modelo.
        6. Cuenta los tokens de la consulta para estimar embeddings.
        7. Calcula los costos estimados de generación y embeddings.
        8. Valida la numeración de las citas documentales.
        9. Aplica abstención segura cuando corresponde.
        10. Devuelve la respuesta y las métricas de ejecución.

    Args:
        pregunta (str): Consulta textual que debe procesar el RAG.
        k (int): Cantidad de fragmentos solicitados al recuperador.

    Returns:
        dict: Resultado estructurado con los siguientes datos:
            - trace_id: Identificador único de la consulta.
            - pregunta: Consulta original.
            - respuesta: Texto generado o mensaje de abstención.
            - fuentes: Fuentes de los documentos aceptados.
            - estado: respuesta_generada o abstencion_segura.
            - tiempos: Latencias medidas por etapa.
            - tokens: Consumo reportado y desgloses disponibles.
            - costos: Estimaciones en dólares estadounidenses.
            - validacion_citas: Resultado de la revisión de citas.
            - modelos: Identificadores de generación y embeddings.

    Raises:
        ValueError: Si no quedan documentos seguros después
            del filtrado o si el modelo utilizado no coincide
            con el configurado.
        Exception: Propaga los errores producidos por la
            recuperación, generación y demás dependencias.

    Notes:
        Esta función puede consumir la API de Gemini.

        Si todos los documentos son descartados por el filtro,
        se bloquea la generación y se produce un ValueError.
        En ese caso, no se devuelve el resultado habitual
        de abstención segura.

        La abstención segura se aplica cuando Gemini devuelve
        ABSTENCION_SIN_EVIDENCIA o cuando las citas no cumplen
        la validación numérica.

        El contexto de trazabilidad se restablece mediante
        finally, incluso cuando ocurre una excepción.

        La función no guarda automáticamente registros JSONL.
    """
    # Cada consulta utiliza su propio identificador de traza.
    # El token permite restaurar el contexto anterior al finalizar.
    trace_id = generar_trace_id()
    token_contexto = trace_id_var.set(trace_id)

    try:
        load_dotenv(dotenv_path=BASE_DIR / ".env")
        logger.info(
            "consulta_iniciada",
            extra={
                "trace_id": trace_id,
                "extra_data": {
                    "pregunta_len": len(pregunta),
                    "k": k,
                },
            },
        )

        # Registra la duración de cada etapa del pipeline.
        # perf_counter utiliza un reloj apropiado para medir
        # intervalos de tiempo, no fechas del calendario.
        tiempos = {}
        inicio_total = time.perf_counter()

        # Etapa 1: embedding de consulta + búsqueda vectorial
        with medir(tiempos, "recuperacion"):
            documentos = recuperar_documentos(pregunta, k=k)

        logger.info(
            "documentos_recuperados",
            extra={
                "trace_id": trace_id,
                "extra_data": {
                    "n_documentos": len(documentos),
                    "latencia_ms": round(
                        tiempos["recuperacion"] * 1000, 2
                    ),
                },
            },
        )

        # Filtrar documentos sospechosos antes de construir el prompt
        with medir(tiempos, "filtrado_seguridad"):
            documentos_originales = documentos
            documentos = filtrar_documentos_langchain(documentos_originales)

        logger.info(
            "documentos_filtrados",
            extra={
                "trace_id": trace_id,
                "extra_data": {
                    "n_originales": len(documentos_originales),
                    "n_aceptados": len(documentos),
                    "n_descartados": len(documentos_originales) - len(documentos),
                },
            },
        )

        # Si el filtro descarta todos los documentos, se detiene
        # el pipeline antes de enviar información al modelo.
        if not documentos:
            logger.warning(
                "sin_documentos_seguros",
                extra={
                    "trace_id": trace_id,
                    "extra_data": {
                        "n_originales": len(documentos_originales),
                        "n_descartados": len(documentos_originales),
                        "accion": "generacion_bloqueada",
                    },
                },
            )

            raise ValueError(
                "No hay documentos seguros disponibles para responder."
            )

        # Etapa 2: construcción del prompt
        with medir(tiempos, "prompt"):
            prompt = construir_prompt(pregunta, documentos)

        # Etapa 3: generación con Gemini
        logger.info(
            "generacion_iniciada",
            extra={
                "trace_id": trace_id,
                "extra_data": {
                    "modelo": MODELO_GENERACION,
                    "n_documentos": len(documentos),
                },
            },
        )

        modelo = ChatGoogleGenerativeAI(model=MODELO_GENERACION)

        with medir(tiempos, "generacion"):
            respuesta_modelo = modelo.invoke(prompt)

        registrar_consumo(respuesta_modelo)

        # Tiempo acumulado hasta finalizar la generación.
        # Todavía no incluye las etapas posteriores de
        # conteo de tokens, costos y validación de citas.
        tiempos["total_rag"] = time.perf_counter() - inicio_total

        textos = [
            bloque["text"]
            for bloque in respuesta_modelo.content_blocks
            if bloque.get("type") == "text"
        ]

        respuesta = "\n".join(textos)

        consumo = extraer_consumo(respuesta_modelo)
        modelo_real = respuesta_modelo.response_metadata.get("model_name")
        logger.info(
            "generacion_finalizada",
            extra={
                "trace_id": trace_id,
                "extra_data": {
                    "modelo": modelo_real,
                    "latencia_ms": round(
                        tiempos["generacion"] * 1000, 2
                    ),
                    "tokens_entrada": consumo["tokens_entrada"],
                    "tokens_salida": consumo["tokens_salida"],
                    "tokens_totales": consumo["tokens_totales"],
                },
            },
        )

        # Comprueba que el proveedor haya utilizado el modelo
        # esperado antes de calcular los costos de la consulta.
        if modelo_real != MODELO_GENERACION:
            raise ValueError(
                f"Modelo inesperado: {modelo_real}. "
                f"Configurado: {MODELO_GENERACION}"
            )
        tokens_entrada = consumo["tokens_entrada"]
        tokens_salida = consumo["tokens_salida"]
        tokens_cache = consumo["tokens_cache"]

        # Conteo adicional de tokens, sin generar otro embedding.
        with medir(tiempos, "conteo_tokens_embedding"):
            tokens_embedding = contar_tokens_embedding(pregunta)

        # Estima el costo utilizando los tokens reportados
        # y las tarifas configuradas para ambos modelos.
        # Este cálculo no equivale a una factura del proveedor.
        costos = calcular_costo_rag(
            modelo_generacion=modelo_real,
            modelo_embedding=MODELO_EMBEDDING,
            tokens_entrada=tokens_entrada,
            tokens_salida=tokens_salida,
            tokens_embedding=tokens_embedding,
            tokens_cache=tokens_cache,
        )

        costo_generacion = costos["generacion_usd"]
        costo_embedding = costos["embedding_usd"]
        costo_total = costos["total_usd"]


        with medir(tiempos, "validacion_citas"):
            resultado_citas = validar_citas(respuesta, documentos)

        MARCADOR_ABSTENCION = "ABSTENCION_SIN_EVIDENCIA"

        RESPUESTA_ABSTENCION = (
            "No dispongo de información suficiente y verificada "
            "en los documentos disponibles para responder esta consulta."
        )

        # Una respuesta sin evidencia o con citas inválidas
        # no se entrega como respuesta documental válida.
        if respuesta.strip() == MARCADOR_ABSTENCION:
            estado = "abstencion_segura"
            respuesta = RESPUESTA_ABSTENCION

        elif resultado_citas["numeracion_valida"]:
            estado = "respuesta_generada"

        else:
            # La respuesta generada no cumple el contrato de citas.
            # No se entrega al usuario; se aplica abstencion segura.
            estado = "abstencion_segura"
            respuesta = RESPUESTA_ABSTENCION

        # Duración completa del procesamiento, incluidas
        # las comprobaciones posteriores a la generación.
        tiempos["total_completo"] = time.perf_counter() - inicio_total
        tiempos["total"] = tiempos["total_completo"]

        return {
            "trace_id": trace_id,
            "pregunta": pregunta,
            "respuesta": respuesta,
            "fuentes": [
                doc.metadata.get("fuente", "desconocida")
                for doc in documentos
            ],
            "estado": estado,
            "tokens_razonamiento": consumo["tokens_razonamiento"],
            "tokens_cache": consumo["tokens_cache"],
            "razonamiento_reportado": consumo["razonamiento_reportado"],
            "uso_original": consumo["uso_original"],
            "tiempos": tiempos,
            "tokens_entrada": consumo["tokens_entrada"],
            "tokens_salida": consumo["tokens_salida"],
            "tokens_totales": consumo["tokens_totales"],
            "validacion_citas": resultado_citas,
            "tokens_embedding": tokens_embedding,
            "costo_generacion_usd": costo_generacion,
            "costo_embedding_usd": costo_embedding,
            "costo_total_usd": costo_total,
            "modelo_generacion": modelo_real,
            "modelo_embedding": MODELO_EMBEDDING,
        }
    finally:
        trace_id_var.reset(token_contexto)

# Demostración manual del pipeline RAG medido.
# Este bloque solo se ejecuta al iniciar directamente
# registro_rag.py, no cuando se importa como módulo.
# Realiza una consulta con Gemini, presenta las métricas
# y guarda el resultado en un archivo JSONL.
# No debe utilizarse para validar cambios documentales,
# porque puede generar consumo real de la API.
if __name__ == "__main__":
    pregunta = (
        "¿Se puede cancelar una solicitud municipal "
        "sin autorización humana?"
    )

    resultado = ejecutar_rag_medido(pregunta)

    print("\n--- RESPUESTA ---")
    print(resultado["respuesta"])

    print("\n--- LATENCIA ---")
    for etapa, segundos in resultado["tiempos"].items():
        print(f"{etapa}: {segundos * 1000:.2f} ms")

    print("\n--- TOKENS ---")
    print(f"Entrada: {resultado['tokens_entrada']}")
    print(f"Salida: {resultado['tokens_salida']}")
    print(f"Total: {resultado['tokens_totales']}")

    print("\n--- CITAS ---")
    print(resultado["validacion_citas"])

    print("\n--- COSTOS ESTIMADOS ---")
    print(f"Tokens embedding: {resultado['tokens_embedding']}")
    print(
        f"Generación: "
        f"${resultado['costo_generacion_usd']:.7f} USD"
    )
    print(
        f"Embedding: "
        f"${resultado['costo_embedding_usd']:.7f} USD"
    )
    print(
        f"Total: "
        f"${resultado['costo_total_usd']:.7f} USD"
    )

    print("\n--- DESGLOSE DE TOKENS ---")

    razonamiento = resultado["tokens_razonamiento"]
    cache = resultado["tokens_cache"]

    print(
        "Razonamiento:",
        razonamiento if razonamiento is not None else "No informado",
    )

    print(
        "Caché:",
        cache if cache is not None else "No informado",
    )

    print(
        "Desglose de razonamiento disponible:",
        resultado["razonamiento_reportado"],
    )

    # Guardar métricas en JSONL
    # Persiste las métricas de esta ejecución manual.
    # La función ejecutar_rag_medido() no realiza
    # este guardado automáticamente.
    ruta_registro = guardar_registro_jsonl(resultado)

    print("\n--- REGISTRO JSONL ---")
    print(f"Guardado en: {ruta_registro}")