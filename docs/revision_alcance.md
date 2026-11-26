# Revisión del alcance

Revisor: Ricardo Alarcón (autorrevisión asistida)
Fecha: 2026-11-26

## Modalidad de revisión

Autorrevisión crítica de las cinco secciones de la ficha
de diseño funcional, realizada con asistencia de inteligencia
artificial.

## Hallazgos y decisiones

- Hallazgo 1 (criterio 3): La arquitectura no explicitaba la restricción de concurrencia del mecanismo existente de captura de registros operacionales, lo que podría generar interferencias entre consultas simultáneas.
  Decisión: aceptado. Cambio: se incorporó en la sección 3 el procesamiento serializado de consultas durante el MVP, dejando la concurrencia segura como mejora posterior.

- Hallazgo 2 (criterio 4): La metodología de evaluación no definía explícitamente las condiciones que debe satisfacer una respuesta válida para contabilizarse en la prueba de rendimiento CA-06.
  Decisión: aceptado. Cambio: se incorporaron las condiciones de validez HTTP, estructura JSON, estado de respuesta, contenido documental y límite temporal en la sección 4.

- Hallazgo 3 (criterio 5): Las funcionalidades deseables del hito H5 disponen de comprobaciones de regresión, pero todavía no cuentan con criterios específicos para verificar su funcionamiento.
  Decisión: aplazado. Se vuelve a evaluar después de completar el alcance imprescindible y antes de iniciar la implementación de RF-06 o RF-07.

## Fortaleza identificada

La ficha presenta una trazabilidad coherente entre los
requerimientos obligatorios, los diez criterios de aceptación,
los veintidós escenarios de evaluación y los seis hitos
de construcción.

El presupuesto respeta las horas disponibles, mantiene
las reservas de validación y contempla un margen de
imprevistos sin comprometer el alcance imprescindible.

## Resultado de la revisión

Se identificaron tres hallazgos:

- Dos aceptados, con modificaciones documentales aplicadas.
- Uno aplazado, asociado a funcionalidades deseables.

Las correcciones mantienen el alcance original del MVP
y no modifican las estimaciones de construcción.

La revisión corresponde al diseño funcional y no constituye
una certificación de cumplimiento funcional del Gate 3.