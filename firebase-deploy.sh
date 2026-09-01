#!/bin/bash

echo "🚀 Iniciando despliegue de Telefonista IA a Firebase..."

# 1. Comprobar si firebase-tools está instalado
if ! command -v firebase &> /dev/null
then
    echo "Firebase CLI no detectado. Instalando..."
    npm install -g firebase-tools
fi

# 2. Desplegar Funciones y Reglas de Firestore
echo "📦 Desplegando Cloud Functions y Firestore Rules..."
firebase deploy --only functions,firestore:rules

echo "✅ Despliegue en Firebase completado con éxito."
