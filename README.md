# Telefonista IA - Asistente Unificado de Voz y WhatsApp

Este proyecto proporciona un backend centralizado en **FastAPI** para atender tanto **llamadas telefónicas por IA** (Vapi/Retell) como **mensajes de WhatsApp** (Meta Cloud API).

## 🚀 Características
- **Lógica de IA Unificada:** Comparte la misma base de conocimiento y funciones (Function Calling) entre voz y texto.
- **WhatsApp Cloud API Integrada:** Verificación automática de Webhook y respuestas en tiempo real.
- **Voz en Tiempo Real:** Endpoints listos para conectarse con plataformas como Vapi.ai o Retell AI.

## 🛠️ Instalación y Uso

1. Clonar o navegar al repositorio:
   ```bash
   cd "c:\dev\telefonista ia"
   ```

2. Crear y activar entorno virtual:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Copiar variables de entorno:
   ```bash
   copy .env.example .env
   ```

5. Levantar el servidor de desarrollo:
   ```bash
   uvicorn app.main:app --reload
   ```
