import httpx
import logging
from app.config import settings

logger = logging.getLogger(__name__)

VAPI_API_BASE = "https://api.vapi.ai"

async def crear_o_vincular_asistente_vapi(cliente_id: str, nombre_empresa: str, webhook_base_url: str, vapi_api_key: str = None) -> dict:
    """
    Crea automáticamente un Asistente de Voz en Vapi.ai apuntando su Server URL 
    al webhook dinámico del cliente (/api/v1/voice/webhook/{cliente_id}).
    """
    key = vapi_api_key or getattr(settings, "VAPI_API_KEY", "")
    if not key:
        logger.error(f"[Vapi] VAPI_API_KEY no configurada. No se puede crear asistente para {cliente_id}")
        return {"status": "error", "detail": "VAPI_API_KEY no configurada en .env"}

    url = f"{VAPI_API_BASE}/assistant"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

    server_url = f"{webhook_base_url}/api/v1/voice/webhook/{cliente_id}"

    payload = {
        "name": f"Telefonista IA - {nombre_empresa}",
        "model": {
            "provider": "openai",
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "system",
                    "content": f"Eres el asistente telefónico oficial de {nombre_empresa}. Responde en frases cortas en el idioma del usuario."
                }
            ]
        },
        "voice": {
            "provider": "openai",
            "voiceId": "shimmer"
        },
        "serverUrl": server_url
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code in [200, 201]:
                data = response.json()
                logger.info(f"[Vapi Auto-Connect] Asistente Vapi creado ID: {data.get('id')}")
                return {
                    "status": "success",
                    "vapi_assistant_id": data.get("id"),
                    "server_url": server_url
                }
            else:
                logger.warning(f"[Vapi Auto-Connect] Error {response.status_code}: {response.text}")
                return {"status": "error", "detail": response.text}
    except Exception as e:
        logger.error(f"[Vapi Auto-Connect] Error de conexión con Vapi API: {e}")
        return {"status": "error", "detail": str(e)}
