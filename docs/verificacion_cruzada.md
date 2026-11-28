
# Verificación cruzada del despliegue

Revisor: Ricardo Alexis Alarcón Castro (autor del proyecto)
Repositorio revisado: VyOps (rama main)
Commit revisado: dc014d6
Fecha: 2026-11-27

Modalidad: autoverificación en un segundo equipo.

Debido a la falta de disponibilidad de otro participante,
se realizó una validación alternativa en un servidor casero,
con sistema operativo Ubuntu.

Se utilizó README.md como guía de despliegue, con
adaptaciones necesarias para el entorno del servidor.

## Entorno de validación

- Equipo: Servidor casero.
- Docker: 29.1.3.
- Docker Compose: 2.40.3.
- Git: 2.43.0.
- Python del servidor: 3.12.3.
- Python de los contenedores: 3.13.10.
- Memoria disponible inicial: 10 GiB.
- Almacenamiento disponible inicial: 404 GB.

## Resultado por criterio

- VC-1 (clon limpio): PASA.
  Se clonó el repositorio desde GitHub en un directorio
  temporal independiente, sin archivos .env ni .venv
  preexistentes.

- VC-2 (configuración documentada): PASA con adaptación.
  Se utilizó .env.example y se modificaron temporalmente
  los puertos publicados para evitar conflictos con
  Nginx Proxy Manager.

- VC-3 (arranque con un comando): PASA.
  Docker Compose construyó e inició ambos servicios
  correctamente.

- VC-4 (servicios sanos y alcanzables): PASA.
  Ambos contenedores alcanzaron el estado healthy.
  Los endpoints de salud devolvieron HTTP 200.

- VC-5 (comportamiento verificable): PASA.
  La consulta documental simulada devolvió el horario
  correcto, la fuente documental y un trace_id.
  La consulta inválida devolvió HTTP 422.
  Los 14 casos del contrato HTTP fueron aprobados.

- VC-6 (sin secretos y apagado limpio): PASA.
  El detector de secretos aprobó 5 de 5 comprobaciones.
  Se eliminaron los contenedores, la red, las imágenes
  creadas y el directorio temporal.

## Hallazgos

- Hallazgo 1: El puerto 8080 estaba ocupado por
  Nginx Proxy Manager.
  Decisión: Aceptado.
  Se utilizaron temporalmente los puertos 18000 y 18080,
  sin modificar el repositorio original.

- Hallazgo 2: El servidor no disponía de httpx2 ni
  del componente ensurepip necesario para crear
  un entorno virtual.
  Decisión: Aceptado.
  Se ejecutaron los casos HTTP desde el contenedor
  de la API y las comprobaciones de Docker Compose
  directamente desde el servidor.

- Hallazgo 3: El detector de secretos requería
  python-dotenv, no instalado en el servidor.
  Decisión: Aceptado.
  Se recuperó temporalmente la dependencia desde
  la imagen de VyOps mediante docker cp y PYTHONPATH,
  sin instalar paquetes globales.

## Resultados

| Comprobación | Resultado |
|---|---|
| Clon limpio | PASA |
| Construcción de imágenes | 2/2 |
| Contenedores saludables | 2/2 |
| Consulta documental simulada | HTTP 200 |
| Consulta inválida | HTTP 422 |
| Casos HTTP | 14/14 |
| Detector de secretos | 5/5 |
| Apagado limpio | PASA |
| Servicios originales operativos | 11/11 |

## Alcance y limitaciones

La validación confirma la reproducibilidad técnica
de VyOps en Windows y Linux.

Las consultas documentales fueron simuladas, sin
consumir Gemini ni utilizar credenciales reales.

El verificador automático completo obtuvo 7/7
en Windows. En Linux sus criterios se comprobaron
por separado debido a las restricciones del entorno.

El detector de secretos no constituye una auditoría
exhaustiva de seguridad.

No se modificaron los servicios existentes del servidor.
La caché de construcción de Docker puede permanecer.

## Conclusión

Validación técnica alternativa: PASA.

La implementación presenta evidencia de reproducibilidad
en dos equipos con sistemas operativos diferentes.

## Autorrevisión desde un clon limpio

Revisor: Ricardo Alexis Alarcón Castro (autor del proyecto).
Repositorio revisado: VyOps, rama main.
Commit revisado: ae9b7bf.
Fecha: 2026-11-28.
Modalidad: autorrevisión desde una terminal nueva.
Se utilizó README.md como guía de ejecución durante
la revisión inicial, con seguimiento de los resultados
mediante asistencia técnica.

### Entorno de validación

- Sistema operativo: Windows.
- Git: 2.52.0.
- Docker: 29.9.2.
- Docker Compose: 5.6.1.
- Python: 3.13.10.

### Resultado por criterio

- VC-1 (clon limpio): PASA.
  Repositorio clonado desde GitHub, sin cambios locales.

- VC-2 (configuración documentada): PASA.
  Archivo .env creado desde .env.example y configuración
  de Docker Compose validada.

- VC-3 (arranque con un comando): PASA.
  Ambas imágenes construidas y servicios iniciados.

- VC-4 (servicios sanos y alcanzables): PASA.
  Ambos contenedores saludables y endpoints de salud
  accesibles en los puertos 8000 y 8080.

- VC-5 (comportamiento verificable): PASA.
  Consulta documental simulada con respuesta correcta,
  fuente documental y trace_id.
  Consulta inválida rechazada correctamente.

- VC-6 (sin secretos y apagado limpio): PASA.
  Detector de secretos aprobado con 5/5 comprobaciones.
  Contenedores y red eliminados correctamente.

### Hallazgos

Hallazgo 1: El verificador del stack no pudo ejecutarse
inicialmente debido a la ausencia de httpx2 en el entorno
Python del clon.

Decisión: Aceptado y resuelto.

Corrección: Incorporar instrucciones explícitas para preparar
el entorno virtual e instalar las dependencias en la sección
de despliegue con Docker del README.

Validación posterior: Tras instalar las dependencias,
el verificador del stack obtuvo 7/7 comprobaciones y
14/14 casos del contrato HTTP, con código de salida 0.

### Resultados consolidados

| Comprobación | Resultado |
|---|---|
| Criterios funcionales de revisión | 6/6 |
| Dockerfile API | 7/7 |
| Dockerfile interfaz | 7/7 |
| Verificador del stack | 7/7 |
| Contrato HTTP | 14/14 |
| Detector de secretos | 5/5 |
| Verificador de entrega | 7/7 |
| Apagado limpio | PASA |

### Limitaciones

- La revisión fue realizada por el autor del proyecto.
- se respetó el intervalo mínimo de un día establecido
  para la modalidad de autorrevisión.
- Docker reutilizó la caché de construcción.
- Las consultas documentales fueron simuladas.
- La resolución del hallazgo se realizó posteriormente
  con asistencia técnica.

### Conclusión

Validación técnica: PASA.

El despliegue es reproducible desde un clon limpio,
con las dependencias locales correctamente instaladas.

El cumplimiento formal de la modalidad de autorrevisión
queda sujeto al criterio del evaluador.

## Revisión final — 28 de noviembre de 2026

Se realizó una nueva revisión desde un clon limpio
del repositorio, utilizando la documentación actualizada.

No se detectaron nuevos problemas durante la ejecución.
Los hallazgos técnicos anteriores se encuentran resueltos.

Resultado técnico informado: PASA.