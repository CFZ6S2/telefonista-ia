#!/bin/bash

echo "🚀 Iniciando despliegue rápido en VPS..."

# 1. Comprobar si Docker está instalado
if ! command -v docker &> /dev/null
then
    echo "Docker no detectado. Instalando Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

# 2. Comprobar .env
if [ ! -f .env ]; then
    echo "Creando archivo .env desde .env.example..."
    cp .env.example .env
    echo "⚠️ RECUERDA: Edita el archivo .env con tus claves reales usando: nano .env"
fi

# 3. Arrancar Docker Compose
echo "📦 Construyendo y levantando contenedores..."
docker compose up -d --build

echo "✅ Telefonista IA desplegado con éxito en http://localhost:8000"
echo "📌 Revisa el estado del contenedor con: docker compose ps"
