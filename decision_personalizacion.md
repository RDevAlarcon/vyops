# Decisión de personalización

## 1. El problema
VyOps necesita responder consultas ciudadanas con información municipal actualizada, verificable y respaldada por fuentes.

## 2. Resultado del método de decisión
- RAG: 5 puntos
- PEFT: 1 puntos
- Fine-tuning completo: 0 puntos

## 3. Técnica elegida y por qué
Se elige RAG (Retrieval-Augmented Generation) como estrategia principal de personalización de VyOps.

El método de decisión entregó 5 puntos a RAG, 1 a PEFT y 0 al fine-tuning completo, sin empates.

RAG responde mejor a la necesidad principal del proyecto: consultar información municipal actualizada y verificable sin tener que reentrenar el modelo cada vez que cambien los documentos, procedimientos o estados de solicitudes.

VyOps ya incorpora mecanismos de recuperación de información, validación de citas y medición de latencia y costos del flujo RAG, desarrollados en bloques anteriores.

PEFT podría considerarse posteriormente si se identifican problemas persistentes de formato, tono o comportamiento. Sin embargo, el dataset actual de 12 ejemplos del Bloque 29 es educativo y no constituye evidencia suficiente para justificar un entrenamiento de producción.

La elección de RAG también implica mantener y actualizar las fuentes documentales y el índice de recuperación. Por sí sola, esta técnica no garantiza que todas las respuestas sean correctas: será necesario verificar su correspondencia con las fuentes recuperadas.

## 4. Qué necesitarías para ejecutarla
VyOps ya cuenta con una implementación inicial de RAG, recuperación de información, validación de citas y registro de métricas. Para utilizar esta estrategia con información municipal real, se necesita completar y validar el corpus documental.

Plan inicial propuesto:

Corpus documental: reunir 30 documentos municipales oficiales, vigentes y autorizados para su utilización. La meta es contar con 30 documentos validados; todavía no se ha realizado un inventario que permita determinar cuántos faltan.

Actualización: registrar para cada documento su fuente, fecha de publicación o actualización y fecha de última verificación.

Evaluación: preparar 20 consultas ciudadanas de prueba, con respuestas de referencia y fuentes que permitan comprobar su exactitud.

Verificación: comprobar que las respuestas recuperan información relevante, presentan citas válidas y no afirman hechos que las fuentes no respaldan.

Observabilidad: medir precisión, cobertura y F1 de recuperación, latencia y costo estimado por consulta, utilizando los componentes desarrollados anteriormente.

Mantenimiento: establecer una revisión mensual del corpus y actualizar los documentos cuando se detecten modificaciones oficiales.

Recursos estimados: 30 documentos oficiales y 20 consultas de evaluación como metas iniciales de validación, sujetas a revisión según los resultados.

No se requiere entrenar un modelo nuevo ni preparar un dataset etiquetado para fine-tuning en esta etapa. Sin embargo, sí se necesita mantener actualizado el índice de recuperación y verificar la calidad de las fuentes.

La estrategia se considerará preparada para una evaluación piloto cuando el corpus esté validado y las pruebas demuestren que las respuestas son correctas y están respaldadas por documentación verificable.