# Imagen base oficial de Python
FROM python:3.12-slim

ENV PIP.DISABLE_PIP_VERSION_CHECK 1

ENV PYTHONUNBUFFERED 1

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar el archivo de dependencias primero (cache de Docker)
COPY requirements.txt .

# Instalar las dependencias del proyecto
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código de la aplicación
COPY app/ .

# Exponer el puerto en el que corre la API
EXPOSE 8000

# Comando para iniciar el servidor con Uvicorn
CMD ["uvicorn", "main:velocambio_app", "--host", "0.0.0.0", "--port", "9000", "--reload"]