# Ficha de Diseño Funcional

## 1. Problema de negocio

Los funcionarios administrativos de una municipalidad requieren consultar frecuentemente documentos, normativas y procedimientos internos para resolver dudas relacionadas con sus actividades diarias. Actualmente, la búsqueda manual de información en documentos dispersos genera demoras, aumenta la carga administrativa y dificulta la entrega de respuestas consistentes. En un escenario simulado de 50 consultas semanales, con un tiempo promedio estimado de 10 minutos por consulta, esta actividad representa aproximadamente 8 horas y 20 minutos de trabajo semanal. Se espera reducir el tiempo promedio de consulta a un minuto o menos, facilitando el acceso a información confiable, respaldada por fuentes documentales y permitiendo que los funcionarios dediquen más tiempo a otras actividades administrativas.

## 2. Requerimientos y alcance (MVP)

### Requerimientos funcionales

- RF-01: Permitir que un consumidor del servicio envíe consultas documentales mediante una API HTTP y reciba respuestas estructuradas en formato JSON.
- RF-02: Generar respuestas fundamentadas en los documentos del corpus municipal simulado, incluyendo referencias a las fuentes utilizadas.
- RF-03: Informar al usuario cuando la evidencia documental recuperada sea insuficiente para generar una respuesta fundamentada.
- RF-04: Detectar y bloquear intentos identificados de inyección de instrucciones maliciosas en las consultas.
- RF-05: Asignar un identificador único de trazabilidad a cada consulta, permitiendo relacionar su ejecución con los registros operacionales.
- RF-06: Permitir la supervisión humana simulada de consultas que requieran revisión mediante la API.
- RF-07: Presentar un panel gráfico de métricas operacionales, incluyendo latencia, consumo de tokens y costos estimados.
- RF-08: Proporcionar una interfaz web con autenticación de usuarios e historial de consultas.
- RF-09: Integrar el servicio con sistemas de información y fuentes documentales municipales reales.
- RF-10: Permitir la administración de múltiples organizaciones con aislamiento de datos, usuarios, roles y permisos.

### Requerimientos no funcionales

- RNF-01: Al menos 9 de 10 consultas del conjunto de evaluación de rendimiento deberán obtener una respuesta en menos de 30 segundos, con el servicio iniciado y el índice documental disponible.
- RNF-02: Durante un conjunto de 10 pruebas de seguridad y privacidad, los registros operacionales deberán presentar 0 exposiciones de claves de API, consultas completas o contenidos documentales completos.
- RNF-03: El servicio deberá poder iniciarse mediante Docker en un máximo de 15 minutos, utilizando una imagen construida, configuración válida y un índice documental previamente preparado, verificándolo mediante 1 prueba de puesta en funcionamiento.
- RNF-04: Al menos 9 de 10 consultas del conjunto de evaluación documental con evidencia disponible deberán generar respuestas respaldadas por fuentes pertinentes y verificables del corpus.
- RNF-05: El 100 % de un conjunto de 10 consultas independientes deberá disponer de un identificador de trazabilidad único y asociado a sus registros operacionales.

### Alcance

Imprescindible: RF-01, RF-02, RF-03, RF-04, RF-05

Deseable: RF-06, RF-07

Fuera de alcance: RF-08 (La interfaz web y la autenticación se reservan para etapas posteriores), RF-09 (El proyecto académico utiliza exclusivamente documentación simulada o pública), RF-10 (La arquitectura multiempresa se considera una evolución futura del producto).

El MVP utilizará un corpus documental municipal simulado y se desarrollará y validará en un entorno local. La contenerización mediante Docker constituye un requerimiento obligatorio de la entrega.

Las funcionalidades deseables estarán condicionadas a la disponibilidad de tiempo y al cumplimiento previo de los requerimientos imprescindibles. Las funcionalidades excluidas no forman parte de los compromisos de implementación del Gate 3.

## 3. Arquitectura de la solución

La arquitectura de VyOps se basa en una estructura modular que reutiliza los componentes desarrollados durante los módulos anteriores e incorpora una capa de exposición del servicio y un mecanismo de contenerización para el MVP del Gate 3.

### Decisiones de arquitectura

**1. Modelo generativo: Google Gemini**

Se utilizará Google Gemini mediante su API externa para generar respuestas fundamentadas en la evidencia documental recuperada y obtener las representaciones vectoriales necesarias para la recuperación de información. Esta decisión permite reutilizar la integración, el manejo de errores y los mecanismos de medición desarrollados anteriormente.

**2. Almacenamiento vectorial: ChromaDB**

Se utilizará ChromaDB como almacenamiento vectorial integrado al servicio Python. El índice documental se conservará mediante un volumen persistente, permitiendo mantener los datos indexados independientemente del ciclo de vida del contenedor.

**3. Orquestación: LangChain + LangGraph**

Se reutilizarán LangChain y LangGraph para coordinar el flujo de procesamiento de consultas, recuperación documental, generación de respuestas, validaciones de seguridad y trazabilidad operacional.

**4. Exposición del servicio: FastAPI**

Se incorporará FastAPI como capa de exposición del servicio mediante una API HTTP. Esta capa permitirá recibir consultas y entregar respuestas estructuradas en formato JSON, manteniendo separada la lógica de negocio de los mecanismos de comunicación.

**5. Empaquetado: Docker**

Se utilizará Docker para empaquetar el servicio y sus dependencias en un entorno reproducible. FastAPI, la orquestación de VyOps y ChromaDB se ejecutarán dentro del contenedor, mientras que Google Gemini permanecerá como servicio externo.

### Seguridad y configuración

Las credenciales se administrarán mediante variables de entorno. La variable GEMINI_API_KEY se proporcionará desde un archivo .env externo al iniciar el contenedor, evitando incorporar credenciales directamente al código fuente, al repositorio o a la imagen Docker.

### Modularidad y evolución

La separación de responsabilidades facilitará el mantenimiento, las pruebas independientes y la incorporación de nuevas funcionalidades. La arquitectura considera una evolución futura hacia una plataforma multiempresa, aunque dicha funcionalidad queda fuera del alcance del MVP académico.

### Diagrama de arquitectura

El siguiente diagrama representa la arquitectura objetivo del Gate 3, incluyendo los componentes existentes y aquellos planificados para las siguientes etapas de construcción.

Diagrama: docs/diagrama_arquitectura.png

## 4. Criterios de aceptación

[PENDIENTE: se completa en el Bloque 34]

## 5. Plan de construcción por hitos

[PENDIENTE: se completa en el Bloque 34]
