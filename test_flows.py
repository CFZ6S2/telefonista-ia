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

def probar_whatsapp():
    print("\n--- PROBANDO FLUJO DE WHATSAPP (DeepSeek + Evolution) ---")
    url = f"{BASE_URL}/api/v1/whatsapp/evolution-webhook/{CLIENTE_ID}"

    try:
        response = requests.post(
            url,
            json=evolution_payload("Hola, estoy buscando un piso centrico en alquiler. ¿Teneis algo disponible y cuanto cuesta?"),
            timeout=30
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("\nRespuesta de la IA:")
            print(data.get("reply", data))
        else:
            print("Error en respuesta:", response.text)
    except Exception as e:
        print(f"Error conectando al servidor: {e}")

def probar_voz():
    print("\n--- PROBANDO FLUJO DE VOZ (Vapi.ai / Tool Calling) ---")
    url = f"{BASE_URL}/api/v1/voice/webhook/{CLIENTE_ID}"

    payload = {
        "message": {
            "type": "tool-calls",
            "toolCalls": [
                {
                    "id": "call_12345",
                    "function": {
                        "name": "consultar_inventario",
                        "arguments": {"consulta": "chalet con piscina"}
                    }
                }
            ]
        }
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("\nResultado devuelto a Vapi.ai (Function Calling):")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print("Error en respuesta:", response.text)
    except Exception as e:
        print(f"Error conectando al servidor: {e}")

def probar_agendamiento_cita():
    print("\n--- PROBANDO AGENDAMIENTO DE CITA EN CRM ---")
    url = f"{BASE_URL}/api/v1/whatsapp/evolution-webhook/{CLIENTE_ID}"

    try:
        response = requests.post(
            url,
            json=evolution_payload("Perfecto, me llamo Maria Fernandez y me gustaria reservar una visita para el chalet este viernes a las 17:00"),
            timeout=30
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("\nRespuesta de Confirmacion de Cita:")
            print(data.get("reply", data))
        else:
            print("Error en respuesta:", response.text)
    except Exception as e:
        print(f"Error conectando al servidor: {e}")

def consultar_leads():
    print("\n--- CONSULTANDO LEADS CAPTURADOS EN BD/CRM ---")
    url = f"{BASE_URL}/api/v1/leads"
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print("Error en respuesta:", response.text)
    except Exception as e:
        print(f"Error conectando al servidor: {e}")

if __name__ == "__main__":
    probar_whatsapp()
    probar_voz()
    probar_agendamiento_cita()
    consultar_leads()
