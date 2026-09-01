from fastapi import APIRouter, Request, HTTPException
import logging
from app.services.ai_brain import procesar_mensaje_ia
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/evolution-webhook")
async def webhook_evolution_whatsapp(request: Request):
    """
    Webhook para recibir mensajes de WhatsApp desde Evolution API (Gratis vía QR).
    No colisiona con ningún proceso del VPS.
    """
    try:
        data = await request.json()
        logger.info(f"[Evolution Webhook Payload]: {data}")

        event = data.get("event")
        
        # Procesar únicamente eventos de mensajes entrantes (MESSAGES_UPSERT)
        if event == "messages.upsert":
            message_data = data.get("data", {})
            key = message_data.get("key", {})
            from_me = key.get("fromMe", False)

            # Ignorar mensajes enviados por el propio bot
            if not from_me:
                remote_jid = key.get("remoteJid", "")
                text = (
                    message_data.get("message", {}).get("conversation") or
                    message_data.get("message", {}).get("extendedTextMessage", {}).get("text", "")
                )

                if text and remote_jid:
                    conversacion = [{"role": "user", "content": text}]
                    respuesta_ia = procesar_mensaje_ia(conversacion, canal="whatsapp")
                    
                    logger.info(f"[Evolution API Response to {remote_jid}]: {respuesta_ia}")
                    # Retornamos la respuesta para que la instancia de Evolution la envíe
                    return {
                        "status": "success",
                        "number": remote_jid,
                        "reply": respuesta_ia
                    }

    except Exception as e:
        logger.error(f"Error procesando webhook de Evolution API: {e}")

    return {"status": "ignored"}
