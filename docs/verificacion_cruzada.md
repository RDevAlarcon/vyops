
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
