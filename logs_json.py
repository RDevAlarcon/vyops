import json
import logging
import sys
from traza_contexto import trace_id_var

class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "msg": record.getMessage(),
        }

        payload["trace_id"] = trace_id_var.get()

        if hasattr(record, "extra_data"):
            payload.update(record.extra_data)

        return json.dumps(payload, ensure_ascii=False)


logger = logging.getLogger("rag_pipeline")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())

logger.handlers = [handler]
logger.propagate = False


if __name__ == "__main__":
    logger.info(
        "consulta recibida",
        extra={
            "trace_id": "abc-123",
            "extra_data": {"pregunta_len": 42},
        },
    )

    logger.info(
        "documentos recuperados",
        extra={
            "trace_id": "abc-123",
            "extra_data": {
                "k": 4,
                "fuente_top": "manual.pdf",
            },
        },
    )