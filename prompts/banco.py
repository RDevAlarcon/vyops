
"""Banco de prompts estructurados para VyOps.

Unidad U1.3 — Bloque 10.

Cada prompt define una tarea empresarial, instrucciones de sistema,
un ejemplo de entrada y el esquema JSON de salida esperado.
"""

BANCO_DE_PROMPTS = [
    {
        "nombre": "clasificar_solicitud",
        "system_instruction": (
            "Eres un asistente de clasificación de solicitudes para VyOps. "
            "Clasifica el mensaje del usuario en una de estas categorías: "
            "reservas, ventas, soporte u otros. "
            "Devuelve exclusivamente un objeto JSON con las claves "
            "'categoria' y 'confianza'. "
            "La confianza debe ser un número entero entre 0 y 100, "
            "que represente tu estimación de confianza en la clasificación. "
            "No utilices valores decimales entre 0 y 1. "
            "No incluyas el símbolo % en el valor. "
            "No agregues explicaciones ni campos adicionales."
        ),
        "ejemplo_usuario": (
            "Necesito cambiar la hora de mi reserva para mañana."
        ),
        "claves_esperadas": ["categoria", "confianza"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "categoria": {
                    "type": "STRING",
                    "enum": ["reservas", "ventas", "soporte", "otros"],
                },
                "confianza": {
                    "type": "INTEGER",
                    "minimum": 0,
                    "maximum": 100,
                },
            },
            "required": ["categoria", "confianza"],
        },
    },
    {
        "nombre": "extraer_datos_cliente",
        "system_instruction": (
            "Eres un asistente de extracción de información para VyOps. "
            "Identifica el nombre del cliente, el servicio solicitado "
            "y la fecha mencionada en el mensaje. "
            "Devuelve exclusivamente un objeto JSON con las claves "
            "'nombre', 'servicio' y 'fecha'. "
            "Conserva la fecha tal como aparece en el mensaje. "
            "Si falta algún dato, utiliza una cadena vacía. "
            "No inventes información ni agregues campos adicionales."
        ),
        "ejemplo_usuario": (
            "Soy Camila, necesito una evaluación de kinesiología "
            "para el viernes."
        ),
        "claves_esperadas": ["nombre", "servicio", "fecha"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "nombre": {"type": "STRING"},
                "servicio": {"type": "STRING"},
                "fecha": {"type": "STRING"},
            },
            "required": ["nombre", "servicio", "fecha"],
        },
    },
    {
        "nombre": "priorizar_solicitud",
        "system_instruction": (
            "Eres un asistente de priorización de solicitudes para VyOps. "
            "Analiza la urgencia del mensaje y asigna una prioridad: "
            "alta, media o baja. "
            "Utiliza prioridad alta para incidentes que impiden operar, "
            "media para problemas que permiten seguir trabajando "
            "y baja para consultas sin urgencia. "
            "Devuelve exclusivamente un objeto JSON con las claves "
            "'prioridad' y 'motivo'. "
            "El motivo debe ser breve y estar basado en el mensaje. "
            "No agregues campos adicionales."
        ),
        "ejemplo_usuario": (
            "El sistema de ventas dejó de funcionar "
            "y no podemos atender clientes."
        ),
        "claves_esperadas": ["prioridad", "motivo"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "prioridad": {
                    "type": "STRING",
                    "enum": ["alta", "media", "baja"],
                },
                "motivo": {
                    "type": "STRING",
                },
            },
            "required": ["prioridad", "motivo"],
        },
    },
]
