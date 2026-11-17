import contextvars
import uuid


trace_id_var = contextvars.ContextVar("trace_id", default=None)

def generar_trace_id():
    """Genera un identificador único para una ejecución."""
    return "trace-" + uuid.uuid4().hex

def procesar(pregunta):
    token = trace_id_var.set(generar_trace_id())

    try:
        print("trace_id activo:", trace_id_var.get())
        sub_paso()
    finally:
        trace_id_var.reset(token)


def sub_paso():
    print(
        "dentro de sub_paso, mismo trace_id sin pasarlo como argumento:",
        trace_id_var.get(),
    )


if __name__ == "__main__":
    procesar("cual es la politica de devoluciones")
    print("fuera del contexto:", trace_id_var.get())