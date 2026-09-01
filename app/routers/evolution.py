from fastapi import APIRouter, Request, HTTPException
import logging
from app.services.ai_brain import procesar_mensaje_ia

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/evolution-webhook/{cliente_id}")
async def webhook_evolution_multi_tenant(cliente_id: str, request: Request):
    """
    Webhook multi-cliente de Evolution API.
    Identifica la empresa por la URL: /api/v1/whatsapp/evolution-webhook/clinica_sonrisas
    """
    try:
        data = await request.json()
        logger.info(f"[Evolution Webhook ({cliente_id})]: {data}")

        event = data.get("event")
        
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
                    conversacion = [{"role": "user", "content": text}]
                    # Pasar cliente_id al motor de IA
                    respuesta_ia = procesar_mensaje_ia(conversacion, canal="whatsapp", cliente_id=cliente_id)
                    
                    return {
                        "status": "success",
                        "number": remote_jid,
                        "reply": respuesta_ia
                    }

    except Exception as e:
        logger.error(f"Error procesando webhook de Evolution API para cliente {cliente_id}: {e}")

    return {"status": "ignored"}
