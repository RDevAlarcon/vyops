# VyOps — Evaluación técnica y decisión de modelos de IA

**Proyecto:** VyOps
**Curso:** SkillNest
**Fecha:** 16 de octubre de 2026
**Estado:** Comparación inicial completada — decisión provisional

## 1. Objetivo

Evaluar modelos de inteligencia artificial generativa para determinar cuál ofrece un equilibrio adecuado entre calidad, latencia y costo para VyOps, un asistente orientado a procesos empresariales.

Los criterios evaluados son:

- **Calidad:** precisión, cumplimiento de instrucciones, utilidad y ausencia de información inventada.
- **Latencia:** tiempo transcurrido durante las solicitudes a la API.
- **Costo:** consumo de tokens y costo estimado según las tarifas de referencia.
- **Disponibilidad observada:** registro de errores de comunicación con el proveedor.

## 2. Modelos evaluados

| Modelo                | Entrada (USD/1M tokens) | Salida (USD/1M tokens) |
| --------------------- | ----------------------: | ---------------------: |
| Gemini 3.6 Flash      |                    0,75 |                   3,75 |
| Gemini 3.5 Flash-Lite |                    0,30 |                   2,50 |

Las tarifas corresponden a la modalidad Estándar utilizada como referencia en octubre de 2026. El costo de salida incluye los tokens de razonamiento cuando el proveedor los informa.

También se intentó evaluar Gemini 3.1 Flash-Lite, pero las solicitudes devolvieron HTTP 503. Por ello, no se incorporó a la comparación cuantitativa.

## 3. Metodología

Se utilizaron cinco preguntas representativas de las funcionalidades previstas para VyOps:

1. Atención al cliente cuando falta información.
2. Clasificación de solicitudes.
3. Extracción estructurada de datos.
4. Selección de herramientas para consultar pedidos.
5. Recomendaciones de automatización empresarial.

Las preguntas fueron idénticas para ambos modelos.

Las solicitudes se ejecutaron secuencialmente mediante Python y la API de Gemini.

Se registraron:

- Fecha, modelo y caso evaluado.
- Respuesta generada y estado de ejecución.
- Latencia en segundos.
- Tokens de entrada, salida, razonamiento y total.
- Costo estimado en USD.
- Errores devueltos por el proveedor.

Los resultados se almacenaron en JSON y CSV, separados por modelo.

La primera ronda contiene cinco respuestas exitosas por modelo. Los resultados constituyen una comparación exploratoria y no una evaluación estadísticamente concluyente.

## 4. Resultados cuantitativos

| Indicador                    | Gemini 3.6 Flash | Gemini 3.5 Flash-Lite |
| ---------------------------- | ---------------: | --------------------: |
| Preguntas completadas        |              5/5 |                   5/5 |
| Latencia promedio exitosa    |          6,717 s |              10,892 s |
| Tokens totales exitosos      |            4.559 |                 1.416 |
| Costo total estimado         |   USD 0,01662525 |        USD 0,00319460 |
| Costo promedio por respuesta |   USD 0,00332505 |        USD 0,00063892 |
| Errores HTTP 503 registrados |                2 |                     0 |

### 4.1. Latencia por pregunta

| Caso                      | Gemini 3.6 Flash | Gemini 3.5 Flash-Lite |
| ------------------------- | ---------------: | --------------------: |
| Atención al cliente       |          6,520 s |               7,187 s |
| Clasificación             |          3,363 s |              25,059 s |
| Extracción de datos       |          3,221 s |               5,201 s |
| Selección de herramientas |          8,143 s |               7,151 s |
| Operaciones empresariales |         12,337 s |               9,863 s |

Gemini 3.6 Flash obtuvo menor latencia promedio.

La solicitud de clasificación de Flash-Lite tardó 25,059 segundos. Este valor requiere nuevas mediciones para determinar si representa un comportamiento recurrente.

### 4.2. Costos

Gemini 3.5 Flash-Lite presentó un costo total aproximadamente **80,8 % inferior** al de Gemini 3.6 Flash en las cinco preguntas evaluadas.

Esta diferencia depende tanto de las tarifas como del consumo de tokens de cada respuesta. No representa una garantía de ahorro idéntico en producción.

### 4.3. Disponibilidad

Gemini 3.6 Flash registró dos errores HTTP 503 antes de completar las cinco preguntas.

Gemini 3.5 Flash-Lite completó las cinco preguntas sin errores durante la ronda registrada.

Estos resultados describen únicamente las solicitudes observadas. No permiten establecer una tasa de disponibilidad general de ninguno de los modelos.

## 5. Evaluación cualitativa

Se utilizó una escala manual de 1 a 5, considerando precisión, cumplimiento de instrucciones y utilidad.

| Caso                      | Gemini 3.6 Flash | Gemini 3.5 Flash-Lite |
| ------------------------- | ---------------: | --------------------: |
| Atención al cliente       |              3/5 |                   4/5 |
| Clasificación             |              4/5 |                   4/5 |
| Extracción de datos       |              4/5 |                   5/5 |
| Selección de herramientas |              5/5 |                   5/5 |
| Operaciones empresariales |              4/5 |                   3/5 |
| **Promedio**              |        **4,0/5** |             **4,2/5** |

### Hallazgos de calidad

**Atención al cliente:** ambos modelos evitaron inventar horarios. Flash-Lite entregó una respuesta más breve, aunque asumió que podría consultar con un equipo.

**Clasificación:** ambos identificaron correctamente la categoría `reservas`, pero incluyeron delimitadores Markdown alrededor del JSON.

**Extracción de datos:** ambos extrajeron correctamente nombre, servicio y fecha sin inventar el año. Flash-Lite entregó JSON directamente utilizable.

**Selección de herramientas:** ambos identificaron la necesidad de consultar un sistema real y contemplaron medidas de verificación de identidad.

**Operaciones empresariales:** ambos propusieron mejoras útiles. Flash-Lite incluyó afirmaciones cuantitativas sin respaldo, como una reducción del tiempo del 70 %, mientras que Flash 3.6 también realizó algunas afirmaciones demasiado categóricas.

Las puntuaciones son preliminares.

## 6. Hallazgos de arquitectura

### 6.1. Salidas estructuradas

Solicitar JSON mediante instrucciones de texto no garantiza recibir JSON válido directamente.

Para funciones empresariales que requieren datos estructurados, se deberá evaluar la configuración de salida estructurada y validación mediante esquemas.

### 6.2. Manejo de errores

Los errores HTTP 503 demuestran la necesidad de diseñar una estrategia de recuperación.

Se evaluarán posteriormente reintentos limitados, espera exponencial y tratamiento explícito de errores HTTP 429 y 503.

### 6.3. Control de costos

El cálculo debe considerar los tokens de entrada y salida, incluidos los de razonamiento cuando corresponda.

El consumo debe medirse por tarea y no únicamente por el precio publicado del modelo.

### 6.4. Persistencia de resultados

El comparador conserva los intentos anteriores y permite reanudar pruebas pendientes sin repetir las exitosas.

Esto evita perder evidencia y permite continuar después de errores temporales del proveedor.

## 7. Decisión provisional de arquitectura

**Decisión:** seleccionar Gemini 3.5 Flash-Lite como candidato principal para tareas operativas de VyOps durante la siguiente etapa de evaluación.

**Justificación:**

- Menor costo observado en las cinco tareas.
- Calidad preliminar comparable a Gemini 3.6 Flash.
- Capacidad para completar clasificación, extracción de datos, atención al cliente y recomendaciones operativas.
- Cinco respuestas exitosas sin errores durante la ronda observada.

**Reserva técnica:** su latencia promedio fue mayor y presentó una solicitud de clasificación de 25,059 segundos.

**Alternativa:** mantener Gemini 3.6 Flash como candidato para tareas que puedan requerir razonamiento más complejo o menor latencia, sujeto a validación adicional.

Esta decisión no implica habilitar automáticamente un sistema de cambio de modelos ni desplegar VyOps en producción.

## 8. Limitaciones de la evaluación

- Solo se obtuvo una respuesta exitosa por pregunta y modelo.
- Las pruebas se ejecutaron en momentos diferentes.
- No se controlaron todas las condiciones externas de la API.
- La evaluación de calidad fue manual.
- No se realizaron pruebas de carga ni concurrencia.
- No se midió la latencia bajo múltiples repeticiones.
- No se verificó el desempeño en procesos empresariales reales.

Por estas razones, la selección permanece provisional.

## 9. Próximas actividades

1. Realizar cuatro ejecuciones controladas por pregunta y modelo, conservando todas las mediciones.
2. Analizar promedios, medianas y variabilidad de latencia.
3. Revisar la consistencia de las respuestas.
4. Evaluar validación de JSON mediante esquemas.
5. Diseñar una política de manejo de errores y reintentos.
6. Documentar la decisión final de arquitectura con evidencia ampliada.

## 10. Evidencia técnica

**Código:**

- `src/consumir_gemini.py`
- `src/comparar_modelos.py`

**Resultados:**

- `resultados/gemini-3.6-flash_pruebas.json`
- `resultados/gemini-3.6-flash_pruebas.csv`
- `resultados/gemini-3.5-flash-lite_pruebas.json`
- `resultados/gemini-3.5-flash-lite_pruebas.csv`

**Arquitectura:**

- `docs/Diagrama_arquitectura.png`

Los archivos JSON contienen las respuestas y los intentos registrados. Los CSV permiten analizar las métricas y comparar los modelos.
