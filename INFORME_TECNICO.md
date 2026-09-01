# INFORME TÉCNICO DE ARQUITECTURA Y ESTADO DEL PROYECTO: TELEFONISTA IA

**Fecha de entrega:** 1 de Septiembre de 2026  
**Repositorio GitHub:** [https://github.com/CFZ6S2/telefonista-ia](https://github.com/CFZ6S2/telefonista-ia)  
**Dashboard Web en Producción:** [https://telefonista-web-app.web.app/dashboard](https://telefonista-web-app.web.app/dashboard)  
**Servidor VPS Producción:** `http://telefonista-api.duckdns.org` (IP: `178.156.186.149`)  

---

## 1. Visión General del Sistema

**Telefonista IA** es una plataforma unificada y **Multi-Tenant (SaaS)** diseñada para automatizar la atención comercial de anuncios y negocios a través de **Llamadas de Voz en tiempo real** (Vapi.ai / LiveKit) y **Mensajes de WhatsApp** (Evolution API / Meta Cloud API) respaldada por un motor de Inteligencia Artificial en tiempo real con **Function Calling** impulsado por **DeepSeek API** (`deepseek-chat`).

---

## 2. Arquitectura de Infraestructura Híbrida

El sistema utiliza una arquitectura híbrida redundante de alta disponibilidad:

1. **Nube Principal (Google Firebase):**
   - **Firestore DB:** Base de datos NoSQL sin servidor para almacenar catálogos de inventario, conversaciones y citas agendadas por `cliente_id`.
   - **Firebase Hosting:** Aloja la interfaz del Dashboard Web en la CDN global de Google (`telefonista-web-app.web.app`).
   - **Cloud Functions:** Serverless API respaldada por reglas de seguridad en `firestore.rules`.

2. **Servidor de Apoyo (VPS Linux Dockerizado):**
   - Contenedor `telefonista_ia_app` en puerto `8089` (FastAPI + Uvicorn).
   - Contenedor `evolution_api_whatsapp` en puerto `8082` (Gestión gratuita de WhatsApp mediante código QR sin comisiones de Meta).
   - Firewall `ufw` configurado con puerto `8089/tcp` abierto para webhooks.

---

## 3. Estructura del Repositorio y Componentes

```text
c:\dev\telefonista ia\
├── app/
│   ├── main.py                   # Servidor FastAPI principal (Routers & Static Files)
│   ├── config.py                 # Pydantic Settings para DeepSeek, Firebase y Meta
│   ├── database.py               # Conector a Firestore con fallback en memoria local (Sin Mocks)
│   ├── routers/
│   │   ├── voice.py              # Webhook multi-cliente para Vapi.ai (/voice/webhook/{cliente_id})
│   │   ├── whatsapp.py           # Webhook Meta Cloud API (/whatsapp/webhook)
│   │   ├── evolution.py          # Webhook Evolution API Gratis (/whatsapp/evolution-webhook/{cliente_id})
│   │   └── admin_clientes.py     # Endpoint /admin/alta-cliente y /admin/qr-whatsapp/{cliente_id}
│   └── services/
│       ├── ai_brain.py           # Motor DeepSeek con Function Calling multilingüe
│       ├── crm.py                # Servicio de captura de leads y contactos
│       ├── vapi_manager.py       # Auto-conector de asistentes de voz en Vapi.ai
│       └── evolution_manager.py  # Auto-conector de instancias WhatsApp en Evolution API
├── public/
│   └── dashboard.html            # Dashboard Web en Bootstrap 5 (Multi-tenant y Alta instantánea)
├── Dockerfile                    # Imagen ligera Python 3.11 Slim
├── docker-compose.yml            # Orquestador Docker en VPS (Red aislada telefonista_net)
├── firebase.json                 # Configuración de Firebase Hosting & Rewrites
├── .firebaserc                   # Asociación del proyecto Firebase (telefonista-web-app)
├── firestore.rules               # Reglas de seguridad estrictas en Firestore
├── migrate_to_firestore.py       # Script de poblamiento/migración inicial a Firestore
└── firebase-deploy.sh            # Script Bash de despliegue automatizado en Firebase
```

---

## 4. Flujo de Trabajo Multi-Tenant (Alta de Clientes)

Cada cliente dispone de **2 números de teléfono independientes**:
- **Número de Voz (Fijo/Centralita):** Conectado automáticamente a Vapi.ai.
- **Número de WhatsApp (Móvil):** Conectado automáticamente a Evolution API mediante código QR.

### Proceso de Alta de un Cliente Nuevo:
1. Petición al endpoint `POST /api/v1/admin/alta-cliente` (o mediante el botón **`⚡ Alta & Conectar APIs Automático`** en el Dashboard).
2. El sistema envía al backend los parámetros:
   `cliente_id`, `nombre_empresa`, `telefono_voz`, `telefono_whatsapp`, `inventario`.
3. El backend:
   - Crea la entrada en Firestore en `clientes/{cliente_id}`.
   - Llama a Vapi.ai API y configura la `serverUrl` a `http://178.156.186.149:8089/api/v1/voice/webhook/{cliente_id}`.
   - Llama a Evolution API e instruye el webhook a `http://178.156.186.149:8089/api/v1/whatsapp/evolution-webhook/{cliente_id}`.
   - Genera el código QR de WhatsApp para escanearlo en pantalla desde el Dashboard.

---

## 5. Instrucciones para la Siguiente IA / Desarrollador

Si otra IA o desarrollador retoma el proyecto, los comandos principales son:

### Probar en Local
```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Desplegar Cambios al VPS
```bash
git add .
git commit -m "mensajes de cambios"
git push origin master
scp -r app public root@178.156.186.149:/opt/telefonista-ia/
ssh root@178.156.186.149 "cd /opt/telefonista-ia && docker compose restart"
```

### Desplegar Cambios a Firebase
```bash
firebase deploy --only hosting
```
