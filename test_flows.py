import requests
import json
import sys

# Asegurar codificación utf-8 para la consola de Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://178.156.186.149:8089"

def probar_whatsapp():
    print("\n--- 💬 PROBANDO FLUJO DE WHATSAPP (DeepSeek + Evolution) ---")
    url = f"{BASE_URL}/api/v1/whatsapp/simular"
    payload = {
        "mensaje": "Hola, estoy buscando un piso céntrico en alquiler. ¿Tenéis algo disponible y cuánto cuesta?",
        "remitente": "+34699887766"
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("\n🤖 Respuesta de la IA:")
            print(data.get("respuesta_ia"))
        else:
            print("Error en respuesta:", response.text)
    except Exception as e:
        print(f"Error conectando al servidor: {e}")

def probar_voz():
    print("\n--- 🎙️ PROBANDO FLUJO DE VOZ (Vapi.ai / Tool Calling) ---")
    url = f"{BASE_URL}/api/v1/voice/webhook"
    
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
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("\n🤖 Resultado devuelto a Vapi.ai (Function Calling):")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print("Error en respuesta:", response.text)
    except Exception as e:
        print(f"Error conectando al servidor: {e}")

def probar_agendamiento_cita():
    print("\n--- 📅 PROBANDO AGENDAMIENTO DE CITA EN CRM ---")
    url = f"{BASE_URL}/api/v1/whatsapp/simular"
    payload = {
        "mensaje": "Perfecto, me llamo María Fernández y me gustaría reservar una visita para el chalet este viernes a las 17:00",
        "remitente": "+34699887766"
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("\n🤖 Respuesta de Confirmación de Cita:")
            print(data.get("respuesta_ia"))
        else:
            print("Error en respuesta:", response.text)
    except Exception as e:
        print(f"Error conectando al servidor: {e}")

def consultar_leads():
    print("\n--- 📋 CONSULTANDO LEADS CAPTURADOS EN BD/CRM ---")
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
