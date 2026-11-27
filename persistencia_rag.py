
"""Persistencia y sanitización de métricas del pipeline RAG de VyOps.

Este módulo permite guardar información de observabilidad
sobre las ejecuciones del sistema RAG municipal.

Sus responsabilidades principales son:
    - Sanitizar los metadatos originales de consumo de tokens.
    - Sustituir los nombres de fuentes por identificadores opacos.
    - Registrar latencias, modelos, tokens y costos estimados.
    - Asociar los registros con un identificador de trazabilidad.
    - Persistir los resultados en formato JSON Lines (JSONL).

El registro evita almacenar directamente el texto de las
preguntas, las respuestas generadas y los nombres originales
de las fuentes documentales.

Los archivos JSONL contienen un objeto JSON por línea,
lo que permite incorporar registros sucesivos sin reescribir
el contenido anterior.

Este módulo no ejecuta consultas a Gemini ni modifica
el índice vectorial de ChromaDB.
"""
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from recuperacion import BASE_DIR
from traza_contexto import trace_id_var


def sanitizar_uso_original(uso):
    """Conserva únicamente contadores de tokens autorizados.

    Filtra los metadatos originales de consumo para impedir
    que se incorporen al registro campos no contemplados
    por la política de persistencia.

    Args:
        uso (dict): Metadatos de consumo recibidos
            desde la respuesta del modelo.

    Returns:
        dict: Diccionario que contiene exclusivamente
            los siguientes campos, cuando son válidos:
                - input_tokens
                - output_tokens
                - total_tokens

            Cada valor conservado debe ser un entero
            no negativo de tipo int exacto.

            Si uso no es un diccionario, devuelve {}.

    Notes:
        Los campos desconocidos se descartan.

        Se utiliza type(valor) is int para excluir
        valores booleanos, aunque bool sea una
        subclase de int en Python.

        No se modifican los metadatos originales.
    """

    # Lista explícita de métricas autorizadas para persistencia.
    campos_permitidos = (
        "input_tokens",
        "output_tokens",
        "total_tokens",
    )

    if not isinstance(uso, dict):
        return {}

    # La comprobación de tipo exacto evita aceptar True o False
    # como contadores numéricos de tokens.
    return {
        campo: uso[campo]
        for campo in campos_permitidos
        if type(uso.get(campo)) is int and uso[campo] >= 0
    }


def sanitizar_fuentes(fuentes):
    """Sustituye los nombres de fuentes por identificadores opacos.

    Genera un identificador determinista a partir del hash
    SHA-256 de cada nombre de fuente recibido.

    El identificador resultante utiliza los primeros
    16 caracteres hexadecimales del hash.

    Args:
        fuentes (list): Lista de nombres de fuentes documentales.

    Returns:
        list: Identificadores con el formato:
            fuente-<16 caracteres hexadecimales>

            Si el argumento no es una lista, devuelve [].

            Los elementos que no son cadenas de texto
            se omiten del resultado.

    Notes:
        La misma cadena de entrada produce siempre
        el mismo identificador.

        El proceso no modifica la lista original.

        El uso de SHA-256 evita almacenar directamente
        los nombres, pero no constituye anonimización
        irreversible: un nombre predecible podría
        identificarse mediante comparación de hashes.

        Se conserva el orden de las fuentes válidas.
    """

    if not isinstance(fuentes, list):
        return []

    resultado = []

    for fuente in fuentes:
        if not isinstance(fuente, str):
            continue

        # Genera un identificador estable sin conservar
        # el nombre original en el registro persistido.
        identificador = hashlib.sha256(
            fuente.encode("utf-8")
        ).hexdigest()[:16]

        resultado.append(f"fuente-{identificador}")

    return resultado

def obtener_ruta_registro(ruta=None) -> Path:
    """Resuelve la ubicación del archivo de registros RAG.

    Prioriza una ruta explícita, seguida del directorio
    configurado mediante VYOPS_REGISTROS_DIR.

    Si no existe una configuración personalizada,
    conserva la ubicación original del proyecto.

    Las rutas relativas configuradas mediante la variable
    de entorno se interpretan desde BASE_DIR.

    Esta función no crea directorios ni archivos.
    """

    # Respeta la ruta proporcionada por el llamador.
    if ruta is not None:
        return Path(ruta)

    # Permite configurar el almacenamiento externamente.
    directorio_configurado = os.environ.get(
        "VYOPS_REGISTROS_DIR", ""
    ).strip()

    if directorio_configurado:
        directorio = Path(
            directorio_configurado
        ).expanduser()

        if not directorio.is_absolute():
            directorio = BASE_DIR / directorio

        return directorio / "resultados_rag.jsonl"

    # Conserva la compatibilidad con el entorno local.
    return BASE_DIR / "resultados_rag.jsonl"

def guardar_registro_jsonl(
    resultado: dict,
    ruta: str | Path | None = None,
) -> Path:
    """Guarda las métricas de una ejecución RAG en formato JSONL.

    Construye un registro estructurado con información
    de trazabilidad, latencias, consumo de tokens,
    costos estimados y validación de citas.

    Antes de persistirlo, sanitiza los nombres de
    fuentes y los metadatos originales de consumo.

    Args:
        resultado (dict): Resultado estructurado de una
            ejecución RAG que contiene las métricas
            necesarias para construir el registro.

        ruta (str | Path | None): Ruta explícita del archivo JSONL.
            Si es None, se utiliza el directorio configurado
            mediante VYOPS_REGISTROS_DIR.

            Si la variable no está definida o está vacía,
            se utiliza resultados_rag.jsonl dentro del
            directorio base del proyecto.

    Returns:
        Path: Ruta del archivo donde se escribió
            el registro de ejecución.

    Raises:
        KeyError: Si faltan campos obligatorios
            dentro del diccionario resultado.
        OSError: Si ocurre un problema de acceso,
            creación de directorios o escritura.
        TypeError: Si algún valor no puede
            serializarse mediante json.dumps().

    Notes:
        El directorio de destino se crea automáticamente
        cuando no existe.

        El archivo se abre en modo anexado ("a"),
        por lo que los registros existentes se conservan.

        Cada ejecución agrega una línea JSON independiente.

        La fecha se registra en UTC mediante ISO 8601.

        Se utiliza el trace_id incluido en resultado.
        Si no está disponible o es falsy, se consulta
        el identificador del contexto de trazabilidad.

        No se almacena el texto completo de la pregunta
        ni de la respuesta, aunque sí la longitud
        de la pregunta y otras métricas.

        El diccionario de latencias y la validación
        de citas se incorporan sin sanitización adicional.
    """

    # Resuelve la ubicación del registro respetando
    # la configuración externa y la compatibilidad local.
    ruta = obtener_ruta_registro(ruta)

    tiempos = resultado["tiempos"]

    # Construye el registro con métricas y metadatos.
    # Los nombres de fuentes y los metadatos de consumo
    # se filtran antes de su serialización.
    registro = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trace_id": resultado.get("trace_id") or trace_id_var.get(),
        "modelo_generacion": resultado["modelo_generacion"],
        "modelo_embedding": resultado["modelo_embedding"],
        "pregunta_longitud": len(resultado["pregunta"]),
        "fuentes": sanitizar_fuentes(resultado["fuentes"]),
        "latencia_rag_segundos": tiempos["total_rag"],
        "latencia_completa_segundos": tiempos["total_completo"],
        "latencia_por_etapa": tiempos,
        "tokens_entrada": resultado["tokens_entrada"],
        "tokens_salida": resultado["tokens_salida"],
        "tokens_totales": resultado["tokens_totales"],
        "tokens_razonamiento": resultado["tokens_razonamiento"],
        "tokens_cache": resultado["tokens_cache"],
        "tokens_embedding": resultado["tokens_embedding"],
        "uso_original": sanitizar_uso_original(
            resultado["uso_original"]
        ),
        "costo_generacion_usd": resultado["costo_generacion_usd"],
        "costo_embedding_usd": resultado["costo_embedding_usd"],
        "costo_total_usd": resultado["costo_total_usd"],
        "validacion_citas": resultado["validacion_citas"],
    }

    # Prepara el directorio de destino cuando todavía
    # no existe, sin modificar los permisos existentes.
    ruta.parent.mkdir(parents=True, exist_ok=True)
    # Agrega una línea JSON sin sobrescribir los registros
    # existentes. ensure_ascii=False conserva caracteres
    # Unicode legibles dentro del archivo UTF-8.
    with ruta.open("a", encoding="utf-8") as archivo:
        archivo.write(
            json.dumps(registro, ensure_ascii=False) + "\n"
        )

    return ruta
