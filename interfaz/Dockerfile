
FROM python:3.13.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py interfaz/main.py

RUN useradd --create-home --uid 10001 vyops

USER vyops

EXPOSE 8000

HEALTHCHECK --interval=5s --timeout=3s --retries=3 --start-period=10s \
    CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/salud', timeout=2).close()"

CMD ["uvicorn", "interfaz.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
