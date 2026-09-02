import httpx
import logging
from app.config import settings

logger = logging.getLogger(__name__)

EVOLUTION_API_BASE = settings.EVOLUTION_API_BASE
EVOLUTION_GLOBAL_KEY = settings.EVOLUTION_API_KEY

async def crear_instancia_evolution_y_conectar_webhook(cliente_id: str, webhook_base_url: str) -> dict:
    url_crear = f"{EVOLUTION_API_BASE}/instance/create"
    headers = {
        "apikey": EVOLUTION_GLOBAL_KEY,
        "Content-Type": "application/json"
    }
    
    webhook_target = f"{webhook_base_url}/api/v1/whatsapp/evolution-webhook/{cliente_id}?token={settings.WEBHOOK_SECRET}"

    payload = {
        "instanceName": cliente_id,
        "token": f"token_{cliente_id}",
        "qrcode": True,
        "integration": "WHATSAPP-BAILEYS",
        "webhook": webhook_target,
        "webhook_by_events": False,
        "events": [
            "MESSAGES_UPSERT"
        ]
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url_crear, json=payload, headers=headers, timeout=10)
            if response.status_code in [200, 201]:
                data = response.json()
                logger.info(f"[Evolution Auto-Connect] Instancia '{cliente_id}' creada con éxito.")
                return {
                    "status": "success",
                    "instance": cliente_id,
                    "qrcode": data.get("qrcode", {}).get("base64"),
                    "pairingCode": data.get("pairingCode")
                }
            else:
                logger.warning(f"[Evolution Auto-Connect] Respuesta {response.status_code}: {response.text}")
                return {"status": "exists_or_error", "detail": response.text}
    except Exception as e:
        logger.error(f"[Evolution Auto-Connect] Error conectando a Evolution API: {e}")
        return {"status": "offline", "detail": str(e)}

async def obtener_qr_instancia_evolution(cliente_id: str) -> dict:
    url_qr = f"{EVOLUTION_API_BASE}/instance/connect/{cliente_id}"
    headers = {"apikey": EVOLUTION_GLOBAL_KEY}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url_qr, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        logger.error(f"Error obteniendo QR para {cliente_id}: {e}")
    
    return {"status": "error"}
