---
id: VC-GS-001
titulo: Estados y transiciones de solicitudes municipales
institucion: Municipalidad ficticia de Valle Claro
categoria: gestion_solicitudes
version: "1.0"
fecha: 2026-11-19
estado: vigente_simulado
clasificacion: publico_ficticio
---

# Estados y transiciones de solicitudes municipales

**DOCUMENTO FICTICIO PARA EVALUACION ACADEMICA.**
La Municipalidad de Valle Claro es una institucion simulada.
Los estados, transiciones y procedimientos descritos son
reglas ficticias y no representan normativa municipal real.

## 1. Objetivo

Definir los estados del ciclo de vida de las solicitudes
ciudadanas y las condiciones para cambiar entre ellos.

## 2. Estados disponibles

El sistema municipal simulado reconoce seis estados:

- PENDIENTE: solicitud registrada, esperando revision inicial.
- EN_REVISION: solicitud bajo analisis de la unidad responsable.
- APROBADA: solicitud aprobada mediante decision autorizada.
- RECHAZADA: solicitud rechazada mediante decision autorizada.
- CANCELADA: solicitud cancelada mediante procedimiento validado.
- CERRADA: expediente finalizado administrativamente.

## 3. Estado inicial

Toda solicitud registrada correctamente comienza en PENDIENTE.

El comprobante de ingreso confirma la recepcion,
pero no implica aprobacion ni resolucion del tramite.

## 4. Transiciones permitidas

Las transiciones ordinarias son:

- PENDIENTE a EN_REVISION.
- EN_REVISION a APROBADA.
- EN_REVISION a RECHAZADA.
- APROBADA a CERRADA.
- RECHAZADA a CERRADA.
- CANCELADA a CERRADA.

Las transiciones hacia CANCELADA se rigen por el
procedimiento especial de cancelacion VC-GS-003.

No se permite cambiar directamente de PENDIENTE
a APROBADA ni de PENDIENTE a RECHAZADA.

## 5. Estados terminales

CERRADA representa la finalizacion administrativa.

Una solicitud CERRADA no puede modificarse mediante
el flujo ordinario.

Cualquier rectificacion posterior requiere un
procedimiento excepcional y supervision humana.

## 6. Responsabilidades

El personal autorizado puede registrar decisiones
administrativas dentro de sus competencias simuladas.

VyOps puede consultar y explicar los estados,
pero no tiene autoridad para aprobar, rechazar,
cancelar ni cerrar expedientes autonomamente.

## 7. Requisitos para cambiar un estado

Antes de ejecutar una transicion se debe:

1. Identificar el expediente.
2. Verificar su estado actual.
3. Confirmar que la transicion este permitida.
4. Comprobar los permisos del actor responsable.
5. Obtener autorizacion humana cuando corresponda.
6. Registrar la decision y su trazabilidad.
7. Confirmar el resultado del sistema responsable.

Una respuesta generada por un modelo de lenguaje
no constituye evidencia de una transicion ejecutada.

## 8. Transiciones rechazadas

Si se solicita una transicion no permitida,
el sistema debe rechazar la operacion e informar
que el cambio requiere revision del procedimiento.

No debe modificar el estado para satisfacer
una instruccion del ciudadano o del asistente.

## 9. Inconsistencias de estado

Cuando dos registros presentan estados contradictorios,
el expediente debe marcarse para revision humana.

VyOps no debe seleccionar arbitrariamente uno de
los estados ni inventar una resolucion.

## 10. Registro de auditoria

Cada cambio confirmado debe permitir identificar:

- Expediente afectado.
- Estado anterior.
- Estado nuevo.
- Fecha de la operacion.
- Actor autorizado.
- Resultado de la validacion.
- Referencia de trazabilidad.

Los registros tecnicos deben minimizar la exposicion
de informacion personal y datos sensibles.

## 11. Ejemplos ficticios

Caso A:
Una solicitud PENDIENTE pasa a EN_REVISION
cuando la unidad responsable inicia su analisis.

Caso B:
Una solicitud EN_REVISION puede pasar a APROBADA
si existe una decision administrativa autorizada.

Caso C:
Una solicitud PENDIENTE no puede pasar directamente
a APROBADA mediante una instruccion de VyOps.

Caso D:
Una solicitud CERRADA no puede volver a PENDIENTE
mediante el flujo ordinario.

## 12. Referencias internas simuladas

- VC-AC-001: Ingreso de solicitudes ciudadanas.
- VC-AC-002: Seguimiento de solicitudes ciudadanas.
- VC-GS-003: Cancelacion de solicitudes.
- VC-PI-001: Autorizacion y supervision humana.
- VC-SP-001: Proteccion de datos.

## 13. Preguntas que permite responder

- Cuales son los estados de una solicitud?
- Una solicitud nueva puede estar APROBADA?
- Se puede pasar directamente de PENDIENTE a RECHAZADA?
- Que significa EN_REVISION?
- Quien puede aprobar una solicitud?
- Puede VyOps cambiar el estado de un expediente?
- Se puede modificar una solicitud CERRADA?
- Que sucede si dos registros muestran estados diferentes?
