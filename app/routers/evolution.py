from fastapi import APIRouter, Request, HTTPException
import httpx
import logging
from app.services.ai_brain import procesar_mensaje_ia
from app.database import obtener_historial_conversacion, guardar_mensaje_historial
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

EVOLUTION_API_BASE = settings.EVOLUTION_API_BASE
EVOLUTION_GLOBAL_KEY = settings.EVOLUTION_API_KEY

@router.post("/evolution-webhook/{cliente_id}")
async def webhook_evolution_whatsapp(cliente_id: str, request: Request):
    """
    Webhook para recibir mensajes de WhatsApp desde Evolution API,
    procesar con historial conversacional de Firestore y ENVIAR RESPUESTA VÍA HTTP.
    """
    try:
        data = await request.json()
        logger.info(f"[Evolution Webhook ({cliente_id})]: {data}")

        event = data.get("event")
        instance = data.get("instance") or cliente_id
        
        if event == "messages.upsert":
            message_data = data.get("data", {})
            key = message_data.get("key", {})
            from_me = key.get("fromMe", False)

            if not from_me:
                remote_jid = key.get("remoteJid", "")
                text = (
                    message_data.get("message", {}).get("conversation") or
                    message_data.get("message", {}).get("extendedTextMessage", {}).get("text", "")
                )

                if text and remote_jid:
                    # 1. Guardar mensaje del usuario en el historial conversacional en Firestore
                    guardar_mensaje_historial(cliente_id, remote_jid, "user", text)

                    # 2. Recuperar historial reciente para mantener contexto conversacional
                    historial = obtener_historial_conversacion(cliente_id, remote_jid, limite=8)
                    if not historial:
                        historial = [{"role": "user", "content": text}]

                    # 3. Procesar con DeepSeek IA
                    respuesta_ia = procesar_mensaje_ia(historial, canal="whatsapp", cliente_id=cliente_id)

                    # 4. Guardar respuesta IA en el historial conversacional
                    guardar_mensaje_historial(cliente_id, remote_jid, "assistant", respuesta_ia)
                    
                    # 5. ENVIAR LA RESPUESTA DE VUELTA AL USUARIO DE WHATSAPP MEDIANTE HTTP A EVOLUTION API
                    await enviar_mensaje_evolution_api(instance, remote_jid, respuesta_ia)

                    return {
                        "status": "success",
                        "number": remote_jid,
                        "reply": respuesta_ia
                    }

    except Exception as e:
        logger.error(f"Error procesando webhook de Evolution API para cliente {cliente_id}: {e}")

    return {"status": "ignored"}

async def enviar_mensaje_evolution_api(instance_name: str, remote_jid: str, text: str):
    """
    Realiza la llamada HTTP POST a Evolution API (/message/sendText/{instance}) para enviar el mensaje real a WhatsApp.
    """
    # Extraer el número puro si viene con @s.whatsapp.net
    number = remote_jid.split("@")[0]
    url = f"{EVOLUTION_API_BASE}/message/sendText/{instance_name}"
    headers = {
        "apikey": EVOLUTION_GLOBAL_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "number": number,
        "text": text,
        "options": {
            "delay": 1200,
            "presence": "composing",
            "linkPreview": True
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code >= 400:
                logger.error(f"[Evolution API Outgoing HTTP {response.status_code}] error: {response.text}")
            else:
                logger.info(f"[Evolution API Outgoing HTTP {response.status_code}] enviada a {number}")
    except Exception as e:
        logger.error(f"[Evolution API Outgoing Error] No se pudo enviar el mensaje HTTP: {e}")
