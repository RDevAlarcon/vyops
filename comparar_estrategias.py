def recomendar_estrategia(respuestas):
    puntos = {
        "RAG": 0,
        "Fine-tuning completo": 0,
        "PEFT": 0,
    }

    if respuestas["informacion_cambia_seguido"]:
        puntos["RAG"] += 3

    if respuestas["problema_de_formato_o_tono"]:
        puntos["PEFT"] += 2
        puntos["Fine-tuning completo"] += 1

    if respuestas["dataset_grande_y_de_calidad"]:
        puntos["Fine-tuning completo"] += 2
        puntos["PEFT"] += 1

    if respuestas["presupuesto_limitado_o_iterar_rapido"]:
        puntos["RAG"] += 2
        puntos["PEFT"] += 1

    if respuestas["necesita_multiples_variantes"]:
        puntos["PEFT"] += 2

    maximo = max(puntos.values())
    ganadoras = [
        tecnica
        for tecnica, puntuacion in puntos.items()
        if puntuacion == maximo
    ]

    return puntos, ganadoras

def generar_esqueleto_decision(problema, puntos, ganadoras):
    empate = len(ganadoras) > 1
    lineas = []

    lineas.append("# Decisión de personalización")
    lineas.append("")
    lineas.append("## 1. El problema")
    lineas.append(problema)
    lineas.append("")

    lineas.append("## 2. Resultado del método de decisión")

    for tecnica, puntuacion in sorted(
        puntos.items(),
        key=lambda x: -x[1],
    ):
        unidad = "punto" if puntuacion == 1 else "puntos"
        lineas.append(f"- {tecnica}: {puntuacion} {unidad}")

    if empate:
        lineas.append("")
        lineas.append(
            f"**Empate entre: {', '.join(ganadoras)}**"
        )

    lineas.append("")
    lineas.append("## 3. Técnica elegida y por qué")

    if empate:
        lineas.append(
            "[COMPLETAR: justificar cómo se resuelve el empate]"
        )
    else:
        lineas.append(
            f"[COMPLETAR: justificar por qué {ganadoras[0]} "
            "responde mejor a este caso]"
        )

    lineas.append("")
    lineas.append("## 4. Qué necesitarías para ejecutarla")
    lineas.append(
        "[COMPLETAR: corpus faltante o cantidad de ejemplos "
        "etiquetados necesarios]"
    )

    return "\n".join(lineas)


if __name__ == "__main__":
    respuestas_caso2 = {
        "informacion_cambia_seguido": False,
        "problema_de_formato_o_tono": True,
        "dataset_grande_y_de_calidad": True,
        "presupuesto_limitado_o_iterar_rapido": False,
        "necesita_multiples_variantes": False,
    }

    puntos, ganadoras = recomendar_estrategia(respuestas_caso2)

    print("Caso 2:", puntos)
    print("Candidatas empatadas:", ganadoras)



    print("\nAnálisis de sensibilidad:")

    for clave in respuestas_caso2:
        variante = dict(respuestas_caso2)
        variante[clave] = not variante[clave]

        puntos_variante, ganadoras_variante = recomendar_estrategia(
            variante
        )

        cambio = (
            "CAMBIA"
            if set(ganadoras_variante) != set(ganadoras)
            else "igual"
        )

        print(
            f"{clave} -> {variante[clave]}: "
            f"{ganadoras_variante} [{cambio}]"
        )




    print("\nCaso 1 — Información cambiante:")

    respuestas_caso1 = {
        "informacion_cambia_seguido": True,
        "problema_de_formato_o_tono": False,
        "dataset_grande_y_de_calidad": False,
        "presupuesto_limitado_o_iterar_rapido": True,
        "necesita_multiples_variantes": False,
    }

    puntos_caso1, ganadoras_caso1 = recomendar_estrategia(
        respuestas_caso1
    )

    print("Puntuaciones:", puntos_caso1)
    print("Estrategia recomendada:", ganadoras_caso1)




    print("\nEvaluación real — VyOps:")

    respuestas_vyops = {
        "informacion_cambia_seguido": True,
        "problema_de_formato_o_tono": False,
        "dataset_grande_y_de_calidad": False,
        "presupuesto_limitado_o_iterar_rapido": True,
        "necesita_multiples_variantes": False,
    }

    puntos_vyops, ganadoras_vyops = recomendar_estrategia(
        respuestas_vyops
    )

    print("Puntuaciones:", puntos_vyops)
    print("Estrategia recomendada:", ganadoras_vyops)



    problema_vyops = (
        "VyOps necesita responder consultas ciudadanas con información "
        "municipal actualizada, verificable y respaldada por fuentes."
    )

    esqueleto = generar_esqueleto_decision(
        problema_vyops,
        puntos_vyops,
        ganadoras_vyops,
    )

    print("\nDocumento generado:")
    print(esqueleto)

    print("\nSensibilidad de la decisión de VyOps:")

    respuestas_vyops_alternativas = dict(respuestas_vyops)
    respuestas_vyops_alternativas["informacion_cambia_seguido"] = False

    puntos_alternativos, ganadoras_alternativas = recomendar_estrategia(
        respuestas_vyops_alternativas
    )

    print("Puntuaciones originales:", puntos_vyops)
    print("Puntuaciones alternativas:", puntos_alternativos)
    print("Recomendación original:", ganadoras_vyops)
    print("Recomendación alternativa:", ganadoras_alternativas)

    from pathlib import Path

    ruta_documento = Path("decision_personalizacion.md")

    if ruta_documento.exists():
        print("Documento existente conservado; no se sobrescribe.")
    else:
        ruta_documento.write_text(esqueleto, encoding="utf-8")
        print("Documento creado correctamente.")