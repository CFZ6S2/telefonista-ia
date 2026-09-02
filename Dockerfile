FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Evitar escritura de archivos .pyc en disco y buffer de salida
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY . .

# Exponer el puerto (Cloud Run usa PORT=8080, VPS usa 8000)
EXPOSE 8080

# Comando para arrancar el servidor en producción
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
