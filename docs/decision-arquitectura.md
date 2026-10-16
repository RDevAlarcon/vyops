# VyOps — Decisión de arquitectura: elección del modelo de IA

**Proyecto:** VyOps  
**Curso:** SkillNest  
**Fecha:** 16 de octubre de 2026

## 1. Modelo elegido

**Gemini 3.5 Flash-Lite (`gemini-3.5-flash-lite`)**

Se selecciona como modelo principal de la miniaplicación VyOps para la siguiente etapa de desarrollo.

VyOps está orientado a tareas empresariales como atención al cliente, clasificación de solicitudes, extracción de información y apoyo a procesos operativos.

La selección es provisional y se fundamenta en las mediciones obtenidas durante la evaluación inicial de dos modelos Gemini.

## 2. Diagrama de arquitectura

El diagrama desarrollado durante el Bloque 8 se encuentra en:

[Ver diagrama de arquitectura](Diagrama_arquitectura.png)

El diagrama representa el flujo de la aplicación, las solicitudes a la API de Gemini, el manejo de credenciales, las respuestas, las excepciones y el registro de tokens y costos.

La elección de Gemini 3.5 Flash-Lite no requiere modificar la estructura general del diagrama, ya que el modelo se configura mediante una constante en el cliente de Python.

## 3. Comparación de candidatos

Se ejecutaron cinco preguntas idénticas para ambos modelos, correspondientes a atención al cliente, clasificación, extracción de datos, selección de herramientas y operaciones empresariales.

| Criterio | Gemini 3.5 Flash-Lite | Gemini 3.6 Flash |
|---|---:|---:|
| Precio entrada (USD/1M tokens) | 0,30 | 0,75 |
| Precio salida (USD/1M tokens) | 2,50 | 3,75 |
| Respuestas exitosas | 5/5 | 5/5 |
| Latencia promedio | 10,892 s | 6,717 s |
| Tokens totales | 1.416 | 4.559 |
| Costo total de las cinco respuestas | USD 0,00319460 | USD 0,01662525 |
| Costo promedio por respuesta | USD 0,00063892 | USD 0,00332505 |
| Calidad preliminar (escala 1–5) | 4,2/5 | 4,0/5 |
| Errores HTTP 503 observados | 0 | 2 |

Las cifras corresponden a pruebas reales realizadas el 16 de octubre de 2026. La evaluación de calidad fue manual y se basó en cinco respuestas por modelo.

## 4. Justificación de la elección

El criterio de mayor peso para VyOps es el **costo por solicitud**, siempre que el modelo mantenga una calidad adecuada para las tareas previstas.

Gemini 3.5 Flash-Lite presentó un costo aproximadamente **80,8 % menor** que Gemini 3.6 Flash durante las cinco pruebas, con una calidad preliminar comparable.

En las tareas de extracción de datos y clasificación, Flash-Lite produjo resultados correctos. También identificó la necesidad de consultar sistemas externos antes de informar el estado de un pedido, evitando inventar información.

Su principal desventaja fue la latencia: obtuvo un promedio de 10,892 segundos, frente a los 6,717 segundos de Gemini 3.6 Flash. Una de sus respuestas tardó 25,059 segundos, por lo que se requieren nuevas pruebas para determinar la estabilidad de su rendimiento.

Para la etapa actual de VyOps, se prioriza el menor costo observado y la capacidad de resolver las tareas de la miniaplicación. La decisión deberá revisarse si las futuras pruebas muestran latencias incompatibles con la experiencia esperada.

## 5. Alternativa descartada y por qué

**Gemini 3.6 Flash (`gemini-3.6-flash`)**

No se seleccionó como modelo principal porque su costo total observado fue aproximadamente 5,2 veces el de Gemini 3.5 Flash-Lite, sin demostrar una ventaja significativa de calidad en los cinco casos evaluados.

Aunque obtuvo menor latencia promedio, también presentó dos errores HTTP 503 durante las pruebas.

No se descarta definitivamente su uso. Se mantiene como alternativa para futuras tareas que puedan requerir mayor capacidad de razonamiento o menor latencia.

Adicionalmente, se intentó evaluar Gemini 3.1 Flash-Lite, pero no fue posible completar sus pruebas debido a respuestas HTTP 503 del proveedor.

---

**Conclusión:** Gemini 3.5 Flash-Lite es el modelo seleccionado para continuar el desarrollo y las pruebas de VyOps. La decisión está respaldada por mediciones reales de costo, latencia y calidad, y permanece sujeta a validaciones adicionales.

**Evidencia complementaria:** [Evaluación técnica completa](evaluacion_modelos.md).