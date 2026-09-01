import requests
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://telefonista-api.duckdns.org"

def evolution_payload(text: str, remitente: str = "+34600112233"):
    return {
        "event": "messages.upsert",
        "data": {
            "key": {
                "remoteJid": f"{remitente.lstrip('+')}@s.whatsapp.net",
                "fromMe": False
            },
            "message": {
                "conversation": text
            }
        }
    }

r = requests.post(
    f"{BASE_URL}/api/v1/whatsapp/evolution-webhook/cliente_demo_inmo",
    json=evolution_payload("Hola, ¿qué pisos o chalet tienes disponibles en alquiler o venta?"),
    timeout=30
)
print("STATUS:", r.status_code)
print("RESPUESTA:", r.json())
