import json
import logging
import math
import sys

from traza_contexto import trace_id_var
from configuracion_modelos import MODELO_GENERACION, MODELO_EMBEDDING


EVENTOS_PERMITIDOS = frozenset({
    "consulta_iniciada",
    "documentos_recuperados",
    "documentos_filtrados",
    "sin_documentos_seguros",
    "generacion_iniciada",
    "consumo registrado",
    "generacion_finalizada",
})

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

VALORES_TEXTO = {
    "modelo": frozenset({
        MODELO_GENERACION,
        MODELO_EMBEDDING,
    }),
    "evento": frozenset({"consumo_llm"}),
    "accion": frozenset({"generacion_bloqueada"}),
}


class JsonFormatter(logging.Formatter):
    def format(self, record):
        mensaje = record.getMessage()

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

        datos = getattr(record, "extra_data", None)

        if isinstance(datos, dict):
            for clave, valor in datos.items():
                if (
                    clave in CAMPOS_NUMERICOS
                    and type(valor) in (int, float)
                    and math.isfinite(valor)
                ):
                    payload[clave] = valor

                elif (
                    clave in VALORES_TEXTO
                    and isinstance(valor, str)
                    and valor in VALORES_TEXTO[clave]
                ):
                    payload[clave] = valor

        return json.dumps(payload, ensure_ascii=False)


logger = logging.getLogger("rag_pipeline")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())

logger.handlers = [handler]
logger.propagate = False


if __name__ == "__main__":
    logger.info(
        "consulta_iniciada",
        extra={"extra_data": {"pregunta_len": 42, "k": 3}},
    )
