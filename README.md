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

## Derechos de autor y propiedad intelectual

**Copyright © 2026 Ricardo Alarcón. Todos los derechos reservados.**

VyOps es un proyecto de desarrollo de software cuya autoría corresponde a Ricardo Alarcón.

El código fuente, la documentación y los materiales originales están protegidos por derechos de autor. Su publicación en GitHub no constituye una autorización general para copiarlos, modificarlos, distribuirlos o utilizarlos comercialmente.

Para más información, consulta el archivo [LICENSE](LICENSE).

Este proyecto se desarrolla en el contexto académico del programa SkillNest, sin perjuicio de las condiciones de propiedad intelectual aplicables al programa.
