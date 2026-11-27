# Imagen base con la misma version de Python del entorno local.
FROM python:3.13.10-slim

# Configuración del intérprete y del almacenamiento persistente.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VYOPS_VECTORSTORE_DIR=/data/vectorstore \
    VYOPS_REGISTROS_DIR=/data/registros

# Directorio de trabajo de la aplicacion.
WORKDIR /app

# Instala primero las dependencias para reutilizar la cache.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el codigo y los recursos autorizados.
COPY . .

# Crea un usuario sin privilegios y prepara el almacenamiento.
RUN useradd --create-home --uid 10001 vyops \
    && mkdir -p /data/vectorstore /data/registros \
    && chown -R vyops:vyops /data

# Ejecuta la aplicacion sin privilegios de root.
USER vyops

# Documenta el puerto HTTP del servicio.
EXPOSE 8000

# Comprueba periodicamente la disponibilidad de la API.
HEALTHCHECK --interval=5s --timeout=3s --retries=3 --start-period=10s \
    CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/salud', timeout=2).close()"

# Inicia el servicio HTTP.
CMD ["uvicorn", "servicio.main:app", "--host", "0.0.0.0", "--port", "8000"]