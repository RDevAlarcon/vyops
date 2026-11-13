
CASOS_EVALUACION = [
    {
        "pregunta": "¿Cómo se registra una solicitud municipal?",
        "relevantes": {"solicitudes_registro.md"},
    },
    {
        "pregunta": "¿Cuáles son los estados de una solicitud?",
        "relevantes": {"solicitudes_estados.md"},
    },
    {
        "pregunta": "¿Qué necesito para consultar una solicitud?",
        "relevantes": {"solicitudes_consulta.md"},
    },
    {
        "pregunta": "¿Puedo cancelar una solicitud sin autorización humana?",
        "relevantes": {"solicitudes_cancelacion.md"},
    },
    {
        "pregunta": "¿Para qué se registran las decisiones del asistente?",
        "relevantes": {"solicitudes_auditoria.md"},
    },
]


if __name__ == "__main__":
    print(f"Casos de evaluación: {len(CASOS_EVALUACION)}")

    for numero, caso in enumerate(CASOS_EVALUACION, start=1):
        print(f"\nCaso {numero}: {caso['pregunta']}")
        print(f"Documentos relevantes: {caso['relevantes']}")
