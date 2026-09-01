import requests
import json
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://178.156.186.149:8089"

def probar_idioma(mensaje: str, idioma_nombre: str):
    print(f"\n--- 🌐 PROBANDO MULTILENGUAJE: {idioma_nombre} ---")
    url = f"{BASE_URL}/api/v1/whatsapp/simular"
    payload = {
        "mensaje": mensaje,
        "remitente": "+34699887766"
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            print("🤖 Respuesta de la IA:")
            print(data.get("respuesta_ia"))
        else:
            print("Error en respuesta:", response.text)
    except Exception as e:
        print(f"Error conectando al servidor: {e}")

if __name__ == "__main__":
    probar_idioma("Hello! Do you have any apartments for rent available right now?", "INGLÉS")
    probar_idioma("Bonjour, avez-vous des maisons ou des appartements disponibles ?", "FRANCÉS")
    probar_idioma("Hallo, haben Sie Wohnungen zur Miete?", "ALEMÁN")
