
# VyOps — Límites de autonomía del agente

## 1. Objetivo

Definir los límites de autonomía del agente municipal VyOps,
los mecanismos de supervisión humana y los procedimientos
de auditoría de sus decisiones.

El sistema es un prototipo educativo. No opera sobre
registros municipales reales.

## 2. Clasificación de riesgos

| Nivel | Descripción | Política |
|---|---|---|
| Bajo | Consultas de solo lectura | Ejecución autónoma |
| Medio | Modificaciones reversibles | Requieren controles adicionales |
| Alto | Operaciones irreversibles o de impacto económico | Aprobación humana obligatoria |

### Herramientas actuales

| Herramienta | Riesgo | Aprobación |
|---|---|---|
| calcular_metricas | Bajo | No |
| consultar_documentacion | Bajo | No |
| analizar_datos | Bajo | No |
| consultar_estado_solicitud | Bajo | No |
| cancelar_solicitud_simulada | Alto | Sí |

No existen herramientas operativas de riesgo medio
en esta versión.

Las herramientas desconocidas se consideran restringidas
hasta que se clasifiquen explícitamente.

## 3. Supervisión humana

La cancelación simulada solo se habilita cuando se
configura un supervisor externo al agente.

El flujo de autorización es:

1. El agente solicita ejecutar la herramienta.
2. El supervisor solicita una decisión externa.
3. Una aprobación explícita permite continuar.
4. Un rechazo, error o vencimiento bloquea la operación.
5. La autorización se vincula a una herramienta y solicitud.
6. La autorización se consume una sola vez.

El agente no recibe el identificador de autorización
como argumento de la herramienta.

El prototipo permite solicitar autorización humana
interactiva mediante la consola de PowerShell.

El operador puede aprobar escribiendo `s` o rechazar
escribiendo `n`.

Se validaron ambos escenarios durante ejecuciones
reales del agente con Gemini.

La decisión es proporcionada por un operador humano,
pero todavía no existe autenticación de su identidad.

## 4. Límites técnicos

El agente tiene configurados límites de iteraciones
y tiempo de ejecución.

La autorización tiene un tiempo de vigencia limitado.

Las operaciones de alto riesgo no deben ejecutarse
cuando la autorización es inexistente, inválida,
reutilizada o vencida.

La cancelación implementada es exclusivamente simulada.
No modifica bases de datos ni sistemas externos.

## 5. Auditoría de decisiones

El módulo `src/trazas_agente.py` permite registrar
ejecuciones en formato JSONL.

Cada registro incluye:

- Fecha y hora UTC.
- Identificador de sesión.
- Entrada recibida.
- Herramientas utilizadas.
- Argumentos de las herramientas.
- Observaciones obtenidas.
- Respuesta final del agente.

La evidencia de demostración se encuentra en:

`evidencias/trazas_bloque_23.jsonl`

Contiene dos escenarios sintéticos:

1. Consulta de solicitud de bajo riesgo.
2. Cancelación ficticia de alto riesgo bloqueada.

Estas trazas no constituyen evidencia de una ejecución
real del agente. Las pruebas automatizadas verifican
por separado el comportamiento de autorización.

### Evidencia de ejecución con Gemini

`evidencias/trazas_gemini_bloque_23.jsonl`

Contiene tres ejecuciones con Gemini utilizando
decisiones de autorización programadas.

### Evidencia con supervisión humana interactiva

`evidencias/trazas_gemini_manual_bloque_23.jsonl`

Contiene tres ejecuciones reales con Gemini:

1. Consulta de bajo riesgo sin autorización.
2. Cancelación ficticia rechazada por el operador (`n`).
3. Cancelación ficticia aprobada por el operador (`s`).

En los dos escenarios de riesgo alto, el supervisor
solicitó una decisión mediante PowerShell.

Las trazas registran las herramientas, argumentos,
observaciones y respuestas finales.

Actualmente no registran explícitamente la decisión
humana (`s` o `n`) ni la identidad del operador.
La evidencia de esas entradas se conserva en
la salida de consola de la demostración.

## 6. Revisión de trazas

Se propone la siguiente frecuencia para una futura
operación supervisada:

- Revisión diaria de alertas de alto riesgo.
- Revisión semanal de patrones repetitivos.
- Revisión inmediata ante un incidente de seguridad.

Estas revisiones son una política propuesta;
todavía no están automatizadas.

## 7. Patrones sospechosos

Se consideran señales para revisión:

- Tres o más llamadas consecutivas a una herramienta.
- Intentos reiterados de operaciones bloqueadas.
- Solicitudes de herramientas desconocidas.
- Reutilización de autorizaciones.
- Operaciones fuera del alcance autorizado.
- Errores repetidos de ejecución.

El detector actual identifica llamadas consecutivas
a la misma herramienta dentro de una ejecución.

Los demás patrones requieren implementación adicional.

Una alerta no demuestra por sí sola un incidente.

## 8. Respuesta ante incidentes

Ante una actividad sospechosa:

1. Registrar el evento y conservar la evidencia.
2. Detener las operaciones de alto riesgo afectadas.
3. Notificar al responsable de supervisión.
4. Revisar trazas y autorizaciones relacionadas.
5. Determinar el alcance y la causa del incidente.
6. Corregir el problema y ejecutar pruebas.
7. Rehabilitar la operación únicamente tras validación.

## 9. Protección de información

El registro actual puede contener información sensible
en entradas, argumentos, observaciones y respuestas.

Por ello, solo debe utilizarse con datos ficticios.

Antes de un despliegue real se requiere:

- Minimización y anonimización de datos.
- Control de acceso a las trazas.
- Política de conservación y eliminación.
- Protección de archivos y respaldos.
- Registro de identidad del supervisor.
- Auditoría de las decisiones de aprobación.

## 10. Limitaciones pendientes

El prototipo todavía no incorpora:

- Autenticación real del supervisor.
- Persistencia segura de autorizaciones.
- Cancelación de tareas externas que continúen
  ejecutándose después de un timeout.
- Protección integral de datos sensibles en trazas.
- Detección de patrones sospechosos entre sesiones.
- Alertas automáticas y monitoreo continuo.

Estas capacidades deben implementarse antes de
utilizar el sistema en un entorno municipal real.

## 11. Validación

Se han desarrollado pruebas automatizadas para:

- Clasificación de riesgos.
- Aprobación, rechazo y vencimiento.
- Autorizaciones vinculadas a una solicitud.
- Prevención de reutilización de autorizaciones.
- Integración del supervisor con el agente.
- Generación y conservación de trazas JSONL.
- Detección básica de llamadas repetitivas.

Las pruebas automatizadas utilizan modelos simulados
y no requieren llamadas reales a Gemini.

Adicionalmente, se realizaron pruebas de integración
con Gemini y supervisión humana interactiva.

### Resultados obtenidos

La batería completa de pruebas automatizadas finalizó con:

- 158 pruebas aprobadas.
- 5 subpruebas aprobadas.
- 0 fallos.
- 4 advertencias de componentes obsoletos de LangChain.

También se ejecutaron tres escenarios con Gemini
y supervisión humana interactiva.

La prueba confirmó que una respuesta `n` bloquea
la cancelación ficticia y una respuesta `s`
permite ejecutar exclusivamente su simulación.

### Limitación del timeout interactivo

El supervisor utiliza un plazo de autorización
de 300 segundos por defecto.

Cuando se utiliza `input()` dentro de un hilo,
el vencimiento del plazo no garantiza que la
lectura de consola se interrumpa automáticamente.

La autorización vencida no debe permitir ejecutar
la operación, pero el hilo de entrada puede
continuar esperando.

Esta limitación debe corregirse antes de utilizar
el mecanismo en producción.