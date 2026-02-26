FROM python:3.12-slim

#esto es solo para mejorar los logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

#primero copiamos dependencias para que no se reinstalen si cambiamos codigo
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#copiamos resto del codigo
COPY . .

# Puerto típico de FastAPI
EXPOSE 8000

# Arranque de la API
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]