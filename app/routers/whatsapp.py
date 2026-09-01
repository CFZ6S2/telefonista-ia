from fastapi import APIRouter, HTTPException, Query, Request, Response
from pydantic import BaseModel
from typing import Dict, Any, Optional
import httpx
import logging
from app.config import settings
from app.services.ai_brain import procesar_mensaje_ia

logger = logging.getLogger(__name__)

router = APIRouter()

class WhatsAppMessagePayload(BaseModel):
    mensaje: str
    remitente: str
    cliente_id: Optional[str] = "cliente_demo_inmo"

@router.get("/webhook")
def verificar_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    if hub_mode == "subscribe" and hub_verify_token == settings.VERIFY_TOKEN:
        logger.info("[WhatsApp Webhook] Verificación exitosa por Meta.")
        return Response(content=hub_challenge, media_type="text/plain")
    else:
        logger.warning("[WhatsApp Webhook] Token de verificación inválido.")
        raise HTTPException(status_code=403, detail="Verification token mismatch")

@router.post("/webhook")
async def recibir_mensaje_whatsapp(request: Request):
    data = await request.json()
    logger.info(f"[WhatsApp Incoming Payload]: {data}")

    try:
        entry = data.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if messages:
            msg = messages[0]
            from_number = msg.get("from")
            text_body = msg.get("text", {}).get("body", "")

            if text_body:
                conversacion = [{"role": "user", "content": text_body}]
                respuesta_ia = procesar_mensaje_ia(conversacion, canal="whatsapp", cliente_id="default")
                await enviar_mensaje_whatsapp(from_number, respuesta_ia)

    except Exception as e:
        logger.error(f"Error procesando mensaje de WhatsApp: {e}")

    return {"status": "event_received"}

async def enviar_mensaje_whatsapp(to_phone: str, text: str):
    if settings.WHATSAPP_TOKEN == "tu_token_de_meta_whatsapp":
        logger.info(f"[Simulación WhatsApp Send to {to_phone}]: {text}")
        return

    url = f"https://graph.facebook.com/v18.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": text}
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        logger.info(f"[Meta API Status]: {response.status_code} - {response.text}")

@router.post("/simular")
def simular_chat(payload: WhatsAppMessagePayload):
    conversacion = [{"role": "user", "content": payload.mensaje}]
    respuesta_ia = procesar_mensaje_ia(conversacion, canal="whatsapp", cliente_id=payload.cliente_id)
    return {
        "cliente_id": payload.cliente_id,
        "remitente": payload.remitente,
        "pregunta": payload.mensaje,
        "respuesta_ia": respuesta_ia
    }
