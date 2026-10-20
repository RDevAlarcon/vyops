# Evaluación de consistencia de prompts — VyOps

## 1. Objetivo

Evaluar la consistencia de tres prompts empresariales de VyOps mediante respuestas JSON estructuradas generadas por Google Gemini.

## 2. Modelo utilizado

- Proveedor: Google Gemini
- Modelo: `gemini-3.5-flash-lite`
- Método: API REST
- Formato de salida: `application/json`
- Validación: JSON válido, claves obligatorias, tipos de datos, valores enumerados y límites numéricos.

## 3. Metodología

Se diseñaron tres prompts con instrucciones de sistema, ejemplos de entrada y esquemas JSON.

Cada prompt se ejecutó tres veces utilizando exactamente la misma entrada, para un total de nueve solicitudes.

Las respuestas se procesaron mediante `parsear_respuesta_json()` y `validar_estructura()`.

El cliente HTTP incorpora reintentos ante errores transitorios HTTP 429/503 y tiempos de espera agotados. El script de evaluación también incluye pausas entre consultas.

## 4. Resultados finales

- Fecha de ejecución (Chile): 20 de octubre de 2026, 15:12 horas.
- Modelo: `gemini-3.5-flash-lite`
- Total de pruebas: 9

| Prompt | Pruebas exitosas | Consistencia estructural |
|---|---:|---:|
| `clasificar_solicitud` | 3/3 | 100% |
| `extraer_datos_cliente` | 3/3 | 100% |
| `priorizar_solicitud` | 3/3 | 100% |
| **Total** | **9/9** | **100%** |

No se registraron errores de API, JSON inválido ni incumplimientos de los esquemas durante las nueve ejecuciones finales.

En evaluaciones anteriores se observaron errores transitorios de disponibilidad y tiempos de espera, que motivaron la incorporación de reintentos y pausas entre consultas.

## 5. Análisis de consistencia

### Clasificación de solicitudes

Las tres respuestas identificaron la categoría `reservas` con confianza `100`.

El campo `confianza` utiliza valores enteros entre 0 y 100. Esta puntuación representa una estimación del modelo y no una probabilidad estadísticamente calibrada.

### Extracción de datos

Las tres respuestas extrajeron los mismos valores:

- Nombre: Camila
- Servicio: evaluación de kinesiología
- Fecha: el viernes

### Priorización de solicitudes

Las tres respuestas asignaron prioridad `alta`.

Se observaron variaciones en la redacción del campo `motivo` entre las tres ejecuciones, sin modificar la clasificación de urgencia.

## 6. Conclusiones

Los tres prompts alcanzaron una consistencia estructural del 100% en los casos evaluados.

Se comprobó que el uso de instrucciones de sistema y esquemas JSON permite obtener respuestas con una estructura predecible para los ejemplos utilizados.

También se observó que los campos de texto libre pueden presentar variaciones de redacción entre ejecuciones, aunque mantengan el mismo significado general.

Los resultados corresponden a una evaluación inicial con un ejemplo por prompt y no constituyen una garantía de consistencia ante todas las entradas posibles.

## 7. Evidencia

- Banco de prompts: `prompts/banco.py`
- Script de pruebas: `prompts/test_consistencia.py`
- Registro de ejecuciones: `prompts/registro_resultados.json`
- Cliente HTTP: `src/consumir_gemini.py`