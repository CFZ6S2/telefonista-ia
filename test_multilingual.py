import requests
import json
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://telefonista-api.duckdns.org"
CLIENTE_ID = "cliente_demo_inmo"

def evolution_payload(text: str, remitente: str = "+34699887766"):
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

def probar_idioma(mensaje: str, idioma_nombre: str):
    print(f"\n--- PROBANDO MULTILENGUAJE: {idioma_nombre} ---")
    url = f"{BASE_URL}/api/v1/whatsapp/evolution-webhook/{CLIENTE_ID}"

    try:
        response = requests.post(url, json=evolution_payload(mensaje), timeout=30)
        if response.status_code == 200:
            data = response.json()
            print("Respuesta de la IA:")
            print(data.get("reply", data))
        else:
            print("Error en respuesta:", response.text)
    except Exception as e:
        print(f"Error conectando al servidor: {e}")

if __name__ == "__main__":
    probar_idioma("Hello! Do you have any apartments for rent available right now?", "INGLES")
    probar_idioma("Bonjour, avez-vous des maisons ou des appartements disponibles ?", "FRANCES")
    probar_idioma("Hallo, haben Sie Wohnungen zur Miete?", "ALEMAN")
