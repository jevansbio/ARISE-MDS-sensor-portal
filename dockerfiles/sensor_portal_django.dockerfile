# syntax=docker/dockerfile:1
FROM python:3.10
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY ./sensor_portal /usr/src/sensor_portal
WORKDIR /usr/src/sensor_portal
# Installer nødvendige systempakker og Python build tools
RUN apt-get update && apt-get install -y \
    binutils \
    libproj-dev \
    gdal-bin \
    postgresql-client \
    build-essential \
    libpq-dev \
    gcc \
    ffmpeg \
 && pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r requirements.txt \
 && apt-get remove -y gcc \
 && apt-get autoremove -y
# Set miljøvariabler for GDAL
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal
