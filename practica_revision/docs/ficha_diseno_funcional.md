
# Ficha de diseño funcional

## 1. Problema de negocio

El equipo de atención al cliente de una tienda recibe aproximadamente 60 consultas semanales relacionadas con políticas de devolución y estados de pedidos. La búsqueda manual de información genera demoras y respuestas inconsistentes. Se espera reducir los tiempos de atención y mejorar la calidad de las respuestas.

## 2. Requerimientos y alcance (MVP)

### Requerimientos funcionales

- RF-01: Recibir consultas mediante una API HTTP y devolver respuestas en formato JSON.
- RF-02: Responder consultas utilizando el manual de atención al cliente e incluir las fuentes consultadas.
- RF-03: Consultar el estado simulado de un pedido.
- RF-04: Permitir la aprobación humana de solicitudes de devolución.
- RF-05: Proporcionar una interfaz web con historial de consultas.
- RF-06: Integrar el servicio con el sistema real de pedidos.

### Requerimientos no funcionales

- RNF-01: Al menos 9 de 10 consultas deberán responderse en menos de 5 segundos.
- RNF-02: En 10 pruebas de privacidad, los registros deberán presentar 0 exposiciones del contenido completo de las consultas.
- RNF-03: El servicio deberá iniciarse mediante Docker en menos de 10 minutos.

### Alcance

Imprescindible: RF-01, RF-02, RF-03

Deseable: RF-04

Fuera de alcance: RF-05, RF-06

## 3. Arquitectura de la solución

- Modelo: Google Gemini, configurado mediante variables de entorno.
- Almacenamiento vectorial: ChromaDB con persistencia local.
- Orquestación: LangChain y LangGraph para recuperación documental, seguridad y supervisión humana.
- API: FastAPI para recibir consultas y entregar respuestas JSON.
- Contenerización: Docker con un volumen persistente para el índice documental.

Diagrama: docs/diagrama_arquitectura.png


## 4. Criterios de aceptación

- CA-01 (RF-01): La respuesta JSON contiene los campos "respuesta" y "fuentes".
- CA-02 (RF-02): Al consultar el plazo de devolución, la respuesta menciona 30 días e incluye la fuente "manual.pdf".
- CA-03 (RF-02): Al consultar por tarjetas de regalo sin evidencia documental, la respuesta informa que no dispone de información y devuelve 0 fuentes.
- CA-04 (RF-03): Al consultar el pedido 123, la respuesta informa su estado simulado.
- CA-05 (RNF-01): Al menos 9 de 10 consultas responden en menos de 5 segundos.
- CA-06 (RNF-02): Los registros de 10 consultas contienen 0 exposiciones del contenido completo de las preguntas.
- CA-07 (RNF-03): El servicio se inicia mediante Docker en menos de 10 minutos.

## 5. Plan de construcción por hitos

Horas disponibles: 20 h

Margen de imprevistos: 4 h

- H1 (3 h): Implementar la API HTTP. Cubre: RF-01. Se comprueba con: CA-01.
- H2 (2 h): Implementar la recuperación documental. Cubre: RF-02. Se comprueba con: CA-02, CA-03.
- H3 (3 h): Contenerizar el servicio. Cubre: RNF-03. Se comprueba con: CA-07.
- H4 (2 h): Implementar la consulta de pedidos simulados. Cubre: RF-03. Se comprueba con: CA-04.
- H5 (6 h): Ejecutar pruebas y preparar la documentación. Cubre: RNF-01, RNF-02. Se comprueba con: CA-05, CA-06.
