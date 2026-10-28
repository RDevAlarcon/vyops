
# Bloque 17 — Interpretación cualitativa y límites del pipeline

## 1. Qué mide

El pipeline de VyOps compara respuestas generadas por Gemini con textos de referencia mediante limpieza, tokenización y conteo de coincidencias.

Calcula tres métricas:

- **Precisión:** proporción de tokens de la respuesta que coinciden con la referencia.
- **Cobertura:** proporción de tokens de la referencia encontrados en la respuesta.
- **F1:** media armónica de precisión y cobertura.

Las coincidencias consideran la frecuencia de los tokens, por lo que una palabra repetida no equivale automáticamente a varias coincidencias.

Estas métricas evalúan similitud léxica. No comprueban directamente la veracidad de una afirmación, su significado ni su calidad de redacción.

## 2. Modos de falla conocidos

### 2.1. Respuestas extensas con F1 bajo

Gemini puede entregar una explicación correcta y detallada que obtenga un F1 muy bajo cuando la referencia es breve.

Ejemplos observados:

| Pregunta | F1 | Resultado cualitativo |
|---|---:|---|
| ¿Qué es el aprendizaje supervisado? | 2,52 % | Explicación correcta y completa |
| ¿Qué es una lista en Python? | 3,81 % | Explicación correcta y completa |
| ¿Qué es Python? | 4,03 % | Explicación correcta y completa |
| ¿Qué representa un booleano en Python? | 4,92 % | Explicación correcta y completa |

La extensión de las respuestas aumenta la cantidad de tokens que no aparecen en las referencias, reduciendo la precisión y el F1.

**Conclusión:** un F1 bajo no demuestra que una respuesta sea incorrecta.

### 2.2. Coincidencia léxica alta

Las operaciones matemáticas obtuvieron F1 del 100 %:

- 100 dividido por 4 = 25.
- 15 multiplicado por 8 = 120.

En ambos casos, las respuestas fueron correctas y prácticamente idénticas a las referencias.

Sin embargo, una coincidencia léxica alta no garantiza por sí sola la corrección factual en otros contextos.

### 2.3. Errores y ambigüedades no detectados

En la respuesta sobre Python apareció la errata "Multiplatormforma".

En la respuesta sobre diccionarios se utilizó una formulación confusa sobre su orden, aunque posteriormente se aclaró que desde Python 3.7 se conserva el orden de inserción.

Las métricas no identificaron estos problemas como errores de redacción o precisión conceptual.

### 2.4. Sinónimos y paráfrasis

Dos respuestas pueden expresar correctamente una misma idea utilizando palabras diferentes.

Como el pipeline compara tokens, puede asignar puntuaciones bajas a respuestas semánticamente equivalentes.

Esta limitación se relaciona con la comparación léxica y no constituye una medición directa de equivalencia semántica.

### 2.5. Fechas, cifras y negaciones

Las métricas no verifican que los números, fechas o nombres mencionados sean correctos.

Tampoco interpretan de manera fiable el significado de una negación.

Por ejemplo, las afirmaciones "El Sol es una estrella" y "El Sol no es una estrella" comparten gran parte de su vocabulario, pero expresan significados opuestos.

Este ejemplo ilustra una limitación del método; no corresponde a una contradicción observada en la muestra manual.

## 3. Muestra revisada

Se configuraron 23 casos de evaluación:

- 3 respuestas recuperadas del Bloque 16.
- 20 respuestas nuevas generadas con Gemini durante el Bloque 17.

Se seleccionaron 10 respuestas para revisión cualitativa:

- Las 5 con menor F1.
- Las 5 con mayor F1.

La revisión utilizó tres criterios:

1. Corrección factual: sí, no o parcialmente.
2. Completitud: sí, no o parcialmente.
3. Contradicción con la referencia: sí o no.

Cada caso incluye una nota justificativa.

### Resultados de la revisión

| Criterio | Resultado |
|---|---|
| Casos revisados | 10 |
| Corrección factual: sí | 9 |
| Corrección factual: parcialmente | 1 |
| Corrección factual: no | 0 |
| Completitud: sí | 10 |
| Contradicciones explícitas | 0 |

La muestra fue seleccionada por sus valores extremos de F1, no de manera aleatoria. Por tanto, estos resultados no permiten estimar la tasa general de errores de Gemini.

Los juicios completos están disponibles en:

`resultados/revision_manual_bloque_17.json`

Las respuestas originales y sus métricas están disponibles en:

`resultados/resultados_bloque_17.json`

## 4. Recomendación de uso

Las métricas de precisión, cobertura y F1 son útiles para:

- Comparar coincidencias de vocabulario entre respuestas y referencias.
- Identificar respuestas que merecen revisión.
- Analizar cambios en la extensión y formulación de las respuestas.
- Complementar evaluaciones automáticas de modelos de lenguaje.

No deben utilizarse como única medida de:

- Corrección factual.
- Equivalencia semántica.
- Ausencia de contradicciones.
- Calidad general de una respuesta.
- Exactitud de cifras, fechas o nombres.

Para evaluaciones más confiables se recomienda combinar las métricas léxicas con revisión humana y, cuando corresponda, comprobaciones específicas de datos verificables.

## 5. Conclusión

El Bloque 17 demostró que las métricas léxicas y la calidad factual de una respuesta no son equivalentes.

Se observaron respuestas conceptualmente correctas con F1 inferior al 5 %, mientras que respuestas matemáticas breves alcanzaron el 100 %.

La principal lección es que **una puntuación F1 debe interpretarse como una medida de coincidencia textual y no como una calificación automática de veracidad**.
