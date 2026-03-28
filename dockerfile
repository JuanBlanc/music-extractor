FROM python:3.12-slim

# Evitar archivos pyc y usar logs sin buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar ffmpeg y dependencias básicas
RUN apt-get update && apt-get install -y ffmpeg curl && rm -rf /var/lib/apt/lists/*

# Crear carpeta de trabajo
WORKDIR /app

# Copiar requirements e instalarlos
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir --upgrade yt-dlp

# Copiar el resto del proyecto
COPY . .

# Exponer puerto de Django
EXPOSE 8000

# Comando de arranque con Uvicorn (ASGI)
# CMD ["uvicorn", "musicExtractor.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
