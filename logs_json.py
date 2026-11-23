
"""Configura el registro estructurado y sanitizado de eventos RAG.

Este módulo implementa el sistema de logging JSON utilizado
por el pipeline RAG municipal de VyOps.

Su objetivo es proporcionar observabilidad sin registrar
indiscriminadamente información procedente de consultas,
documentos o respuestas generadas.

Responsabilidades principales:
    - Definir los nombres de eventos autorizados.
    - Establecer los campos numéricos permitidos.
    - Restringir los valores textuales registrados.
    - Incorporar el identificador de trazabilidad activo.
    - Serializar cada evento como un objeto JSON.
    - Configurar la salida de los logs hacia stdout.

Los mensajes no autorizados se sustituyen por un nombre
de evento genérico. Los campos adicionales que no cumplen
las reglas de validación se descartan.

El módulo no realiza consultas a Gemini ni modifica
el índice vectorial o los documentos del corpus.
"""

import json
import logging
import math
import sys

from traza_contexto import trace_id_var
from configuracion_modelos import MODELO_GENERACION, MODELO_EMBEDDING


# Lista cerrada de nombres de eventos que pueden aparecer
# directamente en el campo "msg" del registro JSON.
#
# Los mensajes que no pertenecen a esta lista se reemplazan
# por "evento_no_autorizado", evitando registrar texto arbitrario.

EVENTOS_PERMITIDOS = frozenset({
    "consulta_iniciada",
    "documentos_recuperados",
    "documentos_filtrados",
    "sin_documentos_seguros",
    "generacion_iniciada",
    "consumo registrado",
    "generacion_finalizada",
})


# Campos numéricos autorizados dentro de extra_data.
#
# Solo se aceptan valores de tipo int o float exactos
# que sean finitos. Se excluyen valores booleanos,
# infinitos, NaN y tipos numéricos no contemplados.

CAMPOS_NUMERICOS = frozenset({
    "pregunta_len",
    "k",
    "n_documentos",
    "n_originales",
    "n_aceptados",
    "n_descartados",
    "latencia_ms",
    "input_tokens",
    "output_tokens",
    "total_tokens",
    "tokens_entrada",
    "tokens_salida",
    "tokens_totales",
})


# Valores textuales expresamente autorizados.
#
# Cada clave posee su propio conjunto de valores válidos.
# No se permite incorporar cadenas arbitrarias en estos
# campos, incluso cuando el nombre de la clave es conocido.

VALORES_TEXTO = {
    "modelo": frozenset({
        MODELO_GENERACION,
        MODELO_EMBEDDING,
    }),
    "evento": frozenset({"consumo_llm"}),
    "accion": frozenset({"generacion_bloqueada"}),
}


class JsonFormatter(logging.Formatter):
    """Convierte registros de logging en eventos JSON restringidos.

    Implementa un formateador que selecciona explícitamente
    los campos autorizados antes de serializar cada evento.

    El registro resultante incluye:
        - ts: Fecha y hora formateadas por logging.
        - level: Nivel del evento.
        - msg: Nombre autorizado o evento_no_autorizado.
        - trace_id: Identificador del contexto activo.

    También incorpora los campos adicionales de extra_data
    que cumplen las reglas de validación.

    Notes:
        El formateador no serializa automáticamente todos
        los atributos del objeto LogRecord.

        El identificador de traza se obtiene directamente
        desde trace_id_var, no desde extra_data.

        La fecha utiliza el formato configurado en formatTime
        y no incorpora explícitamente un indicador de zona
        horaria en la cadena resultante.
    """

    def format(self, record):
        """Genera una representación JSON de un evento de logging.

        Args:
            record (logging.LogRecord): Registro producido
                por el sistema estándar de logging de Python.

        Returns:
            str: Objeto JSON serializado con los campos
                autorizados y sus valores validados.

        Notes:
            Los mensajes fuera de EVENTOS_PERMITIDOS
            se reemplazan por evento_no_autorizado.

            Los campos adicionales solo se procesan
            cuando extra_data es un diccionario.

            Los valores numéricos deben ser finitos
            y de tipo int o float exacto.

            Los valores textuales deben pertenecer
            al conjunto permitido para su clave.

            ensure_ascii=False permite conservar
            caracteres Unicode en la salida JSON.
        """

        # Obtiene el mensaje final del registro antes de
        # comprobar si su contenido está autorizado.
        mensaje = record.getMessage()

        # Construye exclusivamente los campos base admitidos.
        # El trace_id corresponde al contexto activo.
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "msg": (
                mensaje
                if mensaje in EVENTOS_PERMITIDOS
                else "evento_no_autorizado"
            ),
            "trace_id": trace_id_var.get(),
        }

        # Los datos adicionales son opcionales y solo
        # se examinan cuando tienen estructura de diccionario.
        datos = getattr(record, "extra_data", None)

        if isinstance(datos, dict):
            for clave, valor in datos.items():
                # Se aceptan únicamente los campos numéricos
                # definidos y valores finitos de tipo exacto.
                if (
                    clave in CAMPOS_NUMERICOS
                    and type(valor) in (int, float)
                    and math.isfinite(valor)
                ):
                    payload[clave] = valor

                # Los campos textuales deben coincidir con
                # uno de los valores explícitamente permitidos.
                elif (
                    clave in VALORES_TEXTO
                    and isinstance(valor, str)
                    and valor in VALORES_TEXTO[clave]
                ):
                    payload[clave] = valor

        # Serializa el evento sin incorporar automáticamente
        # los demás atributos del LogRecord original.
        return json.dumps(payload, ensure_ascii=False)


# Logger específico del pipeline RAG de VyOps.
logger = logging.getLogger("rag_pipeline")

# Registra eventos de nivel INFO y superiores.
logger.setLevel(logging.INFO)

# Envía los eventos estructurados a la salida estándar.
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())

# Sustituye los handlers anteriores del logger específico
# para utilizar la configuración definida en este módulo.
logger.handlers = [handler]

# Evita que los eventos se propaguen a loggers superiores
# y se dupliquen mediante otros handlers configurados.
logger.propagate = False


if __name__ == "__main__":
    # Demostración local del formato JSON del logger.
    #
    # Este bloque solo se ejecuta al iniciar directamente
    # logs_json.py y no realiza llamadas a servicios externos.

    logger.info(
        "consulta_iniciada",
        extra={"extra_data": {"pregunta_len": 42, "k": 3}},
    )
