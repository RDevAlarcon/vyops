# VyOps — Agente de IA para Gestión Operativa

**Proyecto académico | Especialización en Desarrollo con IA Generativa — Accenture / SkillNest**

## 1. Descripción del proyecto

VyOps es un proyecto de agente de inteligencia artificial orientado a apoyar la gestión operativa de organizaciones y pequeñas y medianas empresas.

Su objetivo es permitir que los usuarios consulten información, obtengan respuestas contextualizadas y, progresivamente, puedan ejecutar tareas mediante herramientas e integraciones con APIs.

La arquitectura prevista es modular y multiempresa (*multi-tenant*), con separación de información por organización.

El proyecto se desarrolla de manera incremental durante el programa SkillNest.

## 2. Objetivo

Construir una solución capaz de:

- Interpretar solicitudes mediante lenguaje natural.
- Consumir modelos de inteligencia artificial mediante APIs.
- Procesar respuestas estructuradas.
- Validar datos y manejar errores.
- Evaluar modelos y prompts.
- Integrar fuentes documentales mediante RAG en etapas posteriores.
- Incorporar herramientas, controles de acceso y observabilidad progresivamente.

Las funcionalidades futuras se implementarán durante las siguientes unidades.

## 3. Estado actual — Unidad 1 / Gate 1

La primera unidad incluye:

- Entorno virtual Python y dependencias reproducibles.
- Configuración segura de credenciales.
- Consumo funcional de Google Gemini mediante API REST.
- Procesamiento de respuestas y métricas de tokens.
- Manejo de errores HTTP y reintentos ante fallos transitorios.
- Evaluación comparativa de modelos.
- Banco de tres prompts con instrucciones de sistema.
- Validación de respuestas JSON estructuradas.
- Evaluación de consistencia con nueve ejecuciones.
- Documentación técnica y control de versiones.

**Modelo seleccionado para las pruebas actuales:** `gemini-3.5-flash-lite`.

## 4. Tecnologías

| Tecnología | Propósito |
|---|---|
| Python 3.13 | Lenguaje principal |
| Google Gemini API | Proveedor de inteligencia artificial |
| requests | Cliente HTTP |
| python-dotenv | Variables de entorno |
| google-genai | SDK de Gemini disponible en el entorno |
| tzdata | Soporte de zonas horarias |
| Git y GitHub | Control de versiones |
| Postman | Pruebas de API |
| venv | Aislamiento de dependencias |

## 5. Estructura del repositorio

```text
vyops/
├── src/
│   ├── main.py
│   ├── cliente_api.py
│   ├── consumir_gemini.py
│   └── comparar_modelos.py
├── tests/
│   ├── test_cliente_gemini.py
│   └── test_cliente_modular.py
├── prompts/
│   ├── banco.py
│   ├── test_consistencia.py
│   ├── registro_resultados.json
│   ├── registro_resultados_anterior.json
│   └── registro_resultados_con_errores.json
├── resultados/
├── docs/
│   ├── evaluacion_modelos.md
│   ├── evaluacion_prompts.md
│   └── decision-arquitectura.md
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```
Los archivos `.env` y `.venv/` son locales y no se incluyen en Git.

## 6. Instalación desde cero — Windows PowerShell

### 6.1. Requisitos previos

- Python 3.13 instalado.
- Git instalado.
- Conexión a internet.
- Clave API de Gemini obtenida desde Google AI Studio.

### 6.2. Clonar el repositorio

```powershell
git clone https://github.com/RDevAlarcon/vyops.git
cd vyops
```

### 6.3. Crear el entorno virtual

```powershell
python -m venv .venv
```

### 6.4. Activar el entorno virtual

```powershell
.\.venv\Scripts\Activate.ps1
```

### 6.5. Instalar dependencias

```powershell
python -m pip install -r requirements.txt
```

Verificar dependencias:

```powershell
python -m pip check
```

### 6.6. Configurar credenciales

Copiar la plantilla:

```powershell
Copy-Item .env.example .env
```

Abrir `.env` y reemplazar el valor de ejemplo por la clave API real:

```dotenv
GEMINI_API_KEY=tu_clave_real
```

Nunca publicar la clave ni incluir `.env` en Git.

## 7. Ejecución de la aplicación

Desde la raíz del proyecto, con el entorno virtual activado y `.env` configurado:

```powershell
python src/main.py
```

También es posible ejecutar directamente el módulo de consumo de Gemini:

```powershell
python src/consumir_gemini.py
```

### 7.1. Pruebas funcionales

El archivo `src/main.py` ejecuta tres pruebas.

**Prueba 1 — Consulta a Gemini**

Realiza una petición al modelo y muestra:

- Respuesta generada.
- Tokens utilizados.
- Tiempo de respuesta.
- Costo estimado de la consulta.

**Prueba 2 — Instrucción de sistema**

Envía una consulta utilizando `system_instruction` para configurar el comportamiento de Gemini como asistente de orientación municipal.

**Prueba 3 — Validación de entrada**

Envía una entrada inválida y comprueba que el sistema la rechace mediante una excepción `ValueError` controlada.

### 7.2. Resultado de verificación

El 22 de octubre de 2026 se ejecutó `src/main.py` correctamente.

| Prueba | Resultado |
|---|---|
| Consulta a Gemini | Correcta |
| Instrucción de sistema | Correcta |
| Validación de entrada | Correcta |

Las dos primeras pruebas requieren conexión a internet y disponibilidad de la API de Gemini. Consumen cuota del proveedor y pueden generar costos.

### 7.3. Otros componentes

Los módulos de evaluación comparativa de modelos y consistencia de prompts se mantienen independientes del punto de entrada principal.

Sus procedimientos de ejecución se describen en las siguientes secciones.

## 8. Evaluación de modelos

Se implementó una comparación de modelos de Gemini considerando:

- Respuestas correctas.
- Tiempo de respuesta.
- Consumo de tokens.
- Costo estimado.
- Errores de API.

Script:

```powershell
python src/comparar_modelos.py
```

Documentación:

- `docs/evaluacion_modelos.md`
- `docs/decision-arquitectura.md`

Los resultados históricos se conservan en `resultados/`.

## 9. Banco de prompts y validación JSON

El banco contiene tres prompts:

1. `clasificar_solicitud`
2. `extraer_datos_cliente`
3. `priorizar_solicitud`

Cada prompt define instrucciones de sistema, entrada de ejemplo, esquema JSON y claves obligatorias.

La evaluación se ejecuta mediante:

```powershell
python prompts/test_consistencia.py
```

Este comando realiza nueve consultas reales a Gemini y actualiza `prompts/registro_resultados.json`. Por lo tanto, consume cuota de API y puede generar costos.

**Resultado registrado el 20 de octubre de 2026:** 9 de 9 pruebas exitosas, con un 100 % de cumplimiento estructural para los ejemplos evaluados.

La evidencia histórica y el análisis se encuentran en:

- `prompts/registro_resultados.json`
- `prompts/registro_resultados_anterior.json`
- `prompts/registro_resultados_con_errores.json`
- `docs/evaluacion_prompts.md`

## 10. Seguridad y buenas prácticas

- Las credenciales se cargan desde `.env`.
- `.env` está excluido mediante `.gitignore`.
- `.env.example` contiene únicamente valores de ejemplo.
- Las dependencias se registran en `requirements.txt`.
- Las peticiones HTTP incorporan manejo de errores.
- Los errores transitorios pueden activar reintentos controlados.
- Las respuestas JSON se validan antes de procesarlas.
- El historial de cambios se mantiene en GitHub.

## 11. Evidencia técnica de la Unidad 1

### Primera petición autenticada

El 9 de octubre de 2026 se realizó una petición HTTP autenticada a Gemini mediante Postman.

- Modelo utilizado inicialmente: `gemini-2.5-flash`.
- Resultado HTTP: `200 OK`.
- Evidencia: [Primera petición autenticada](docs/evidencia_petición_autenticada.png).

Posteriormente se implementó el cliente Python y se evaluaron otros modelos para seleccionar una alternativa apropiada para VyOps.

### Arquitectura

El diseño técnico y su evolución se documentan en `docs/`, incluyendo el diagrama de arquitectura y las decisiones de selección del modelo.
El diagrama de arquitectura de la Unidad 1 está disponible en:
[Diagrama de arquitectura de VyOps](docs/Diagrama_arquitectura.png).

### Prueba funcional del cliente Python

El 20 de octubre de 2026 se comprobó la ejecución de `src/consumir_gemini.py`:

- Respuesta generada correctamente.
- 45 tokens totales.
- Tiempo de respuesta: 10,606 segundos.
- Costo estimado: USD 0,00008390.


## Unidad 2 — Bloque 12: Cliente de API modular

### Objetivo

Implementar una interfaz reutilizable para consultar la API de
Google Gemini, separando el consumo del modelo de la lógica
de las aplicaciones que utilizarán el cliente.

El módulo reutiliza las funciones desarrolladas durante Gate 1
y mantiene un manejo centralizado de errores y reintentos.

### Implementación

**Archivo principal:** `src/cliente_api.py`

La función pública `consultar_modelo()` coordina tres operaciones:

1. `armar_peticion()`: valida los parámetros y construye
   la solicitud HTTP.
2. `enviar_peticion()`: realiza la solicitud a Gemini,
   controla los errores y gestiona los reintentos.
3. `extraer_texto()`: obtiene el texto generado desde
   la respuesta JSON.

Las tres funciones reutilizadas se encuentran en
`src/consumir_gemini.py`.

### Ejecución del cliente

Desde la raíz del proyecto, con el entorno virtual activado
y la API key configurada:

```powershell
python -m src.cliente_api
```

Este comando ejecuta una consulta de demostración a Gemini
y muestra la respuesta o un error controlado en consola.

La consulta utiliza la API real, requiere conexión a internet
y puede consumir cuota o generar costos.

### Manejo de errores y reintentos

El cliente contempla:

- HTTP 400: solicitud rechazada, incluyendo posibles problemas
  con la API key o los parámetros enviados.
- HTTP 401 y 403: problemas de autenticación o acceso.
- HTTP 404: modelo o recurso no disponible.
- HTTP 429: límite de solicitudes.
- HTTP 500 y 502: errores temporales del proveedor.
- HTTP 503: servicio temporalmente no disponible.
- Timeout: tiempo de espera agotado.
- Errores de conexión y respuestas JSON inválidas.

Los errores HTTP 429, 500, 502 y 503, así como los timeout,
permiten hasta tres intentos en total.

Los reintentos utilizan pausas exponenciales de 2 y 4 segundos.
Cuando corresponde, se considera el encabezado `Retry-After`,
con un límite de espera de 60 segundos.

### Pruebas automatizadas

Los archivos de pruebas son:

- `tests/test_cliente_gemini.py`: validación de errores HTTP,
  timeout, reintentos y encabezado `Retry-After`.
- `tests/test_cliente_modular.py`: validación de la interfaz
  pública y propagación de errores.

Para ejecutar las pruebas desde la raíz del proyecto:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

**Resultado local del 23 de octubre de 2026:**

- 11 pruebas ejecutadas.
- 11 pruebas aprobadas.
- 0 errores.

Las pruebas automatizadas utilizan mocks y no realizan
solicitudes reales a Gemini.

### Alcance

Este bloque implementa un cliente modular reutilizable.
No incorpora todavía recuperación documental RAG,
herramientas externas ni funcionalidades multiempresa.

Estas capacidades se abordarán progresivamente
en las siguientes etapas del proyecto.

## Unidad 2 — Bloque 13: Reintentos avanzados y control de costos

### Objetivo

Mejorar la resiliencia del cliente Gemini y permitir el seguimiento
de costos estimados por operación y por sesión.

### Backoff exponencial con jitter

El cliente HTTP incorpora reintentos ante errores transitorios:

- HTTP 429, 500, 502 y 503.
- Timeout de la solicitud.
- Máximo de tres intentos en total.
- Esperas exponenciales de 2 y 4 segundos.
- Jitter aleatorio de hasta un 10 % de la espera base.
- Respeto del encabezado `Retry-After` como espera mínima.
- Límite configurado de 60 segundos para las esperas.

La implementación se encuentra en `src/consumir_gemini.py`.

### Cálculo de costos por operación

Se reutiliza la función `calcular_costo()` para estimar el costo
de cada respuesta a partir de los tokens informados por Gemini.

El modelo configurado es `gemini-3.5-flash-lite`.

Las tarifas configuradas son:

| Concepto | Precio por millón de tokens |
|---|---:|
| Entrada | USD 0,30 |
| Salida | USD 2,50 |

Los tokens de razonamiento se consideran dentro del cálculo
de salida, según la información de uso disponible.

Los costos son estimaciones y no reemplazan la facturación
oficial del proveedor.

### Registro de costos por sesión

El archivo `src/registro_costos.py` implementa
`RegistroCostosSesion`.

Permite:

- Registrar el costo estimado de cada operación exitosa.
- Consultar el historial de operaciones.
- Obtener el costo total acumulado.
- Mantener registros independientes entre instancias.
- Rechazar costos negativos, infinitos o inválidos.

El registro funciona en memoria. No incorpora persistencia
en base de datos ni recuperación después de reiniciar el proceso.

### Integración con el cliente modular

El archivo `src/cliente_api.py` incorpora
`consultar_modelo_con_costos()`.

Esta función consulta Gemini, extrae el texto, calcula el costo
estimado y lo registra en la sesión proporcionada.

La función original `consultar_modelo()` se mantiene disponible
sin cambios en su interfaz pública.

Los reintentos internos no generan registros adicionales por sí
mismos. El registro se realiza una vez después de procesar
correctamente la respuesta.

Si falla el envío, la extracción o el cálculo del costo,
no se registra una nueva operación.

Esto describe el registro local: una solicitud enviada al
proveedor podría consumir cuota o generar cargos incluso si
posteriormente falla su procesamiento.

### Pruebas automatizadas

Se utilizan los siguientes archivos:

- `tests/test_cliente_gemini.py`
- `tests/test_cliente_modular.py`
- `tests/test_registro_costos.py`

Para ejecutar todas las pruebas:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

**Resultado local del 24 de octubre de 2026:**

- 22 pruebas ejecutadas.
- 22 pruebas aprobadas.
- 0 errores.

Las pruebas utilizan simulaciones y no requieren llamadas
reales a Gemini.

## Unidad 2 — Bloque 14: Pruebas unitarias con pytest y mocks

### Objetivo

Validar el funcionamiento del cliente de Google Gemini mediante pruebas automatizadas, sin realizar solicitudes reales al proveedor.

Se utiliza `pytest` como ejecutor de pruebas, manteniendo la compatibilidad con las pruebas existentes desarrolladas con `unittest`.

### Escenarios verificados

- Respuestas HTTP 400, 401 y 403 sin reintentos.
- Reintentos ante errores HTTP 429, 500, 502 y 503.
- Agotamiento de reintentos y propagación de errores.
- Manejo de timeouts, espera exponencial, jitter y `Retry-After`.
- Ejecución de consultas mediante la API modular.
- Registro y acumulación de costos por sesión.
- Prevención del registro de costos cuando falla una consulta o su procesamiento.
- Validación de costos inválidos e independencia entre sesiones.
- Cálculo exacto del costo estimado a partir de tokens de entrada, salida y razonamiento.

### Archivos de pruebas

- `tests/test_cliente_gemini.py`
- `tests/test_cliente_modular.py`
- `tests/test_registro_costos.py`
- `tests/test_calculo_costos.py`

Las pruebas utilizan `unittest.mock` para simular respuestas y errores, evitando conexiones reales a Gemini.

### Ejecución

Con el entorno virtual activado:

```powershell
python -m pytest tests/ -v
```

### Resultados de validación

**Ejecución local del 25 de octubre de 2026:**

- 24 pruebas principales aprobadas.
- 5 subpruebas aprobadas.
- 0 errores.
- Tiempo de ejecución: 0,20 segundos.

La suite completa se ejecutó correctamente con Python 3.13.10 y pytest 9.1.1.

### Compatibilidad

Se conservan las pruebas existentes de `unittest`, ejecutables tanto con `unittest` como con `pytest`. No fue necesario reemplazar la arquitectura modular de VyOps.

## Unidad 2 — Bloque 15: Pipeline de texto y evaluación de respuestas

### Objetivo

Implementar un pipeline de procesamiento de texto para normalizar, tokenizar y vectorizar respuestas generadas por inteligencia artificial.

Evaluar la coincidencia de vocabulario entre respuestas de Google Gemini y textos de referencia, comparando los resultados antes y después de la normalización.

### Implementación

**Archivo principal:** `src/pipeline_texto.py`

Se implementaron cinco funciones:

- `limpiar_texto()`: convierte el texto a minúsculas, elimina signos de puntuación y normaliza espacios.
- `tokenizar()`: separa el texto en palabras, conservando su orden y repeticiones.
- `procesar_texto()`: integra las etapas de limpieza y tokenización.
- `vectorizar()`: utiliza `collections.Counter` para contar la frecuencia de las palabras.
- `calcular_coincidencia()`: calcula la proporción de palabras únicas de referencia presentes en una respuesta, con o sin normalización.

El pipeline utiliza únicamente componentes de la biblioteca estándar de Python.

### Evaluación de respuestas reales

**Script:** `evaluar_respuestas.py`

Se realizaron tres consultas reales a Gemini mediante la función `consultar_modelo()` del cliente modular existente.

Para cada consulta se comparó la respuesta generada con un texto de referencia.

**Resultados del 27 de octubre de 2026:**

| Caso | Sin normalización | Con normalización |
|---|---:|---:|
| Capital de Chile | 83,33 % | 100,00 % |
| Multiplicación de 5 por 4 | 50,00 % | 50,00 % |
| Función `print()` | 57,14 % | 85,71 % |
| **Promedio** | **63,49 %** | **78,57 %** |

La normalización aumentó la coincidencia promedio en aproximadamente 15,08 puntos porcentuales.

### Limitaciones de la métrica

La coincidencia de vocabulario no equivale a una evaluación de exactitud factual o similitud semántica.

Entre sus limitaciones:

- No reconoce automáticamente que `20` y `veinte` representan el mismo valor.
- No considera el orden de las palabras.
- No considera la frecuencia de las palabras repetidas.
- No penaliza directamente las palabras adicionales de una respuesta.
- Una coincidencia alta no garantiza que la información sea correcta.

Por lo tanto, esta métrica constituye una primera aproximación a la evaluación automática de respuestas.

### Ejecución de la evaluación

Desde la raíz del proyecto, con el entorno virtual activado y la clave API configurada:

```powershell
python evaluar_respuestas.py
```

Este comando realiza tres consultas reales a Gemini y puede consumir cuota de API o generar costos.

### Pruebas automatizadas

**Archivo:** `tests/test_pipeline_texto.py`

Se incorporaron nueve pruebas para validar:

- Limpieza de mayúsculas, puntuación y espacios.
- Tokenización y conservación de palabras repetidas.
- Integración del pipeline.
- Procesamiento de textos vacíos.
- Conteo de frecuencias.
- Vectorización de listas vacías.
- Comparación con y sin normalización.
- Manejo de referencias vacías.

Para ejecutar todas las pruebas del proyecto:

```powershell
python -m pytest tests/ -v
```

**Resultado local del 27 de octubre de 2026:**

- 33 pruebas principales aprobadas.
- 5 subpruebas aprobadas.
- 0 errores.
- Tiempo de ejecución: 0,21 segundos.

Las pruebas automatizadas no realizan consultas reales a Gemini.

### Alcance

Este bloque incorpora herramientas básicas de procesamiento y evaluación textual, reutilizando la arquitectura modular existente de VyOps.

No incluye todavía métricas semánticas avanzadas, embeddings ni evaluación mediante modelos jueces.

## Unidad 2 — Bloque 16: Métricas de precisión, cobertura y F1

### Objetivo

Implementar métricas cuantitativas para evaluar respuestas generadas por Google Gemini mediante comparación de tokens con textos de referencia.

Ampliar el pipeline desarrollado en el Bloque 15, incorporando precisión, cobertura (*recall*) y F1, con registro de resultados en formato JSON.

### Implementación

**Archivo principal:** `src/pipeline_texto.py`

Se incorporaron tres funciones:

- `contar_coincidencias()`: calcula las coincidencias entre tokens, considerando su frecuencia y evitando contabilizar repeticiones en exceso.
- `calcular_precision_cobertura_f1()`: calcula precisión, cobertura y F1 a partir de dos listas de tokens.
- `calcular_metricas()`: integra la normalización, tokenización y evaluación de dos textos.

Las métricas se calculan mediante las siguientes fórmulas:

**Precisión:**

`precision = coincidencias / tokens_respuesta`

**Cobertura:**

`cobertura = coincidencias / tokens_referencia`

**F1:**

`F1 = 2 × (precision × cobertura) / (precision + cobertura)`

Se contemplan casos de listas vacías y divisiones por cero.

### Evaluación automatizada de Gemini

**Script:** `evaluar_respuestas.py`

Se incorporaron las siguientes funciones:

- `evaluar_casos_bloque_16()`: consulta Gemini y calcula las métricas para cada caso.
- `guardar_resultados_metricas()`: guarda las evaluaciones en JSON.
- `resumir_metricas()`: calcula los promedios de las métricas.
- `obtener_peores_casos()`: identifica los casos con menor F1.
- `ejecutar_evaluacion_bloque_16()`: coordina la evaluación completa.

Para ejecutar exclusivamente el Bloque 16:

```powershell
python evaluar_respuestas.py --bloque-16
```

La evaluación original del Bloque 15 permanece disponible:

```powershell
python evaluar_respuestas.py
```

Ambos comandos realizan consultas reales a Gemini y pueden consumir cuota de API o generar costos.

### Resultados de la evaluación real

**Fecha:** 28 de octubre de 2026.

Se evaluaron tres consultas utilizando referencias breves.

| Consulta | Precisión | Cobertura | F1 |
|---|---:|---:|---:|
| ¿Qué es Python? | 2,06 % | 100,00 % | 4,03 % |
| ¿Cuándo se creó Python? | 10,00 % | 100,00 % | 18,18 % |
| ¿Qué es una lista en Python? | 1,95 % | 87,50 % | 3,81 % |
| **Promedio** | **4,67 %** | **95,83 %** | **8,68 %** |

Los resultados se almacenaron en:

`resultados/resultados_metricas.json`

### Interpretación de resultados

La cobertura promedio elevada indica que las respuestas de Gemini incluyeron la mayoría de los tokens presentes en los textos de referencia.

La precisión promedio fue baja porque las respuestas generadas contenían considerablemente más información que las referencias utilizadas.

En consecuencia, el F1 promedio de 8,68 % representa una coincidencia léxica limitada bajo esta metodología, no una calificación general de la calidad del modelo.

### Limitaciones identificadas

- Las métricas no evalúan directamente la exactitud factual.
- No identifican automáticamente sinónimos o expresiones semánticamente equivalentes.
- Pueden asignar valores elevados a respuestas que contienen datos incorrectos.
- No interpretan adecuadamente las negaciones.
- Las respuestas extensas pueden obtener una precisión baja frente a referencias breves.
- No detectan de manera fiable errores ortográficos o de redacción.

Estas limitaciones deberán considerarse al incorporar evaluaciones semánticas en etapas posteriores.

### Pruebas automatizadas

**Archivos:**

- `tests/test_pipeline_texto.py`
- `tests/test_evaluacion_bloque_16.py`

Se verificaron cálculos de métricas, palabras repetidas, textos vacíos, limitaciones semánticas, almacenamiento JSON, promedios, ordenamiento por F1 e integración completa sin llamadas reales a Gemini.

Para ejecutar todas las pruebas:

```powershell
python -m pytest tests/ -v
```

**Resultado local del 28 de octubre de 2026:**

- 46 pruebas principales aprobadas.
- 5 subpruebas aprobadas.
- 0 errores.
- Tiempo de ejecución: 0,33 segundos.

Las pruebas automatizadas utilizan simulaciones para evitar solicitudes reales a Gemini.

### Alcance

El Bloque 16 incorpora una evaluación cuantitativa reproducible basada en coincidencias léxicas y conserva los resultados obtenidos como evidencia técnica.

No incorpora todavía embeddings, métricas semánticas avanzadas ni evaluación mediante modelos jueces.


## Unidad 2 — Bloque 17: Interpretación cualitativa y límites del pipeline

En este bloque se evaluaron respuestas reales de Gemini para analizar las limitaciones de las métricas de precisión, cobertura y F1.

### Objetivos

- Evaluar al menos 20 respuestas generadas por un modelo de lenguaje.
- Comparar respuestas con referencias mediante métricas léxicas.
- Seleccionar casos con puntuaciones F1 altas y bajas.
- Realizar una revisión cualitativa de al menos 10 respuestas.
- Documentar las limitaciones de las métricas.

### Implementación

Se configuraron 23 casos de evaluación:

- 3 respuestas recuperadas del Bloque 16.
- 20 respuestas nuevas generadas durante el Bloque 17.

El sistema permite guardar los resultados progresivamente y reanudar las consultas pendientes sin repetir las ya registradas.

### Ejecución

Para ejecutar o reanudar la evaluación:

```powershell
python ejecutar_bloque_17.py
```

Para ejecutar las pruebas automatizadas:

```powershell
python -m pytest tests/ -v
```

### Resultados

Se revisaron cualitativamente 10 respuestas:

- 5 con los valores F1 más bajos.
- 5 con los valores F1 más altos.

La revisión mostró que algunas respuestas correctas y extensas obtuvieron puntuaciones F1 inferiores al 5 %.

Las respuestas matemáticas breves alcanzaron F1 del 100 % cuando coincidieron con las referencias.

Esto demuestra que una coincidencia léxica elevada no garantiza por sí sola la corrección factual y que un F1 bajo no implica necesariamente una respuesta incorrecta.

### Archivos principales

| Archivo | Descripción |
|---|---|
| `src/casos_evaluacion_bloque_17.py` | Banco de preguntas y referencias |
| `src/evaluacion_bloque_17.py` | Evaluación y selección de casos |
| `ejecutar_bloque_17.py` | Ejecución y reanudación |
| `tests/test_evaluacion_bloque_17.py` | Pruebas automatizadas |
| `resultados/resultados_bloque_17.json` | Respuestas y métricas |
| `resultados/revision_manual_bloque_17.json` | Evaluaciones cualitativas |
| `docs/limites_metrica.md` | Análisis de limitaciones |

### Conclusión

Las métricas de precisión, cobertura y F1 son útiles para comparar coincidencias textuales, pero deben complementarse con revisión humana cuando se necesita evaluar veracidad, significado o contradicciones.


## Derechos de autor y propiedad intelectual

**Copyright © 2026 Ricardo Alarcón. Todos los derechos reservados.**

VyOps es un proyecto de desarrollo de software cuya autoría corresponde a Ricardo Alarcón.

El código fuente, la documentación y los materiales originales están protegidos por derechos de autor. Su publicación en GitHub no constituye una autorización general para copiarlos, modificarlos, distribuirlos o utilizarlos comercialmente.

Para más información, consulta el archivo [LICENSE](LICENSE).

Este proyecto se desarrolla en el contexto académico del programa SkillNest, sin perjuicio de las condiciones de propiedad intelectual aplicables al programa.
