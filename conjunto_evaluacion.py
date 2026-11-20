
CASOS_EVALUACION = [
    {
        "pregunta": "¿Cómo se registra una solicitud municipal?",
        "relevantes": {"atencion_ciudadana/ingreso_solicitudes.md"},
    },
    {
        "pregunta": "¿Cuáles son los estados de una solicitud?",
        "relevantes": {"gestion_solicitudes/estados_transiciones.md"},
    },
    {
        "pregunta": "¿Qué necesito para consultar una solicitud?",
        "relevantes": {"atencion_ciudadana/seguimiento_solicitudes.md"},
    },
    {
        "pregunta": "¿Puedo cancelar una solicitud sin autorización humana?",
        "relevantes": {"gestion_solicitudes/cancelacion_solicitudes.md"},
    },
    {
        "pregunta": "¿Para qué se registran las decisiones del asistente?",
        "relevantes": {"procedimientos_internos/auditoria_trazabilidad.md"},
    },
]


if __name__ == "__main__":
    print(f"Casos de evaluación: {len(CASOS_EVALUACION)}")

    for numero, caso in enumerate(CASOS_EVALUACION, start=1):
        print(f"\nCaso {numero}: {caso['pregunta']}")
        print(f"Documentos relevantes: {caso['relevantes']}")
