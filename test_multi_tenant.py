import requests
import json
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://178.156.186.149:8089"

def probar_cliente(cliente_id: str, mensaje: str, nombre_empresa: str):
    print(f"\n--- 🏬 PROBANDO CLIENTE: {nombre_empresa} (ID: {cliente_id}) ---")
    url = f"{BASE_URL}/api/v1/whatsapp/simular"
    payload = {
        "cliente_id": cliente_id,
        "mensaje": mensaje,
        "remitente": "+34699887766"
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            print(f"🤖 Respuesta de la IA para {nombre_empresa}:")
            print(data.get("respuesta_ia"))
        else:
            print("Error en respuesta:", response.text)
    except Exception as e:
        print(f"Error conectando al servidor: {e}")

if __name__ == "__main__":
    # Prueba 1: Cliente Inmobiliaria
    probar_cliente(
        cliente_id="cliente_demo_inmo",
        mensaje="Hola, ¿qué pisos en alquiler tenéis?",
        nombre_empresa="Agencia Inmobiliaria"
    )
    
    # Prueba 2: Cliente Clínica Dental
    probar_cliente(
        cliente_id="clinica_sonrisas",
        mensaje="Hola, ¿qué precio tiene la limpieza dental o la ortodoncia?",
        nombre_empresa="Clínica Dental Sonrisas"
    )
