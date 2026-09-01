import json
import logging
from typing import List, Dict, Any
from openai import OpenAI
from app.config import settings
from app.database import buscar_en_inventario, agendar_cita_demo
from app.services.crm import registrar_lead

logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL
)

SYSTEM_PROMPT_WHATSAPP = """
Eres la IA comercial oficial de la empresa atendiendo a través de WhatsApp.

Directrices de Estilo:
1. Responde de forma amable, cercana y profesional. Usa un tono conversacional de WhatsApp (puedes usar algún emoji con moderación).
2. Proporciona detalles claros sobre precios, características y ubicaciones cuando te pregunten.
3. Si el cliente muestra interés en un producto/servicio o solicita una visita/cita, utiliza las herramientas (Function Calling) correspondientes para registrar su interés o agendar la cita.
4. Mantén los párrafos breves para facilitar la lectura en móviles.
"""

SYSTEM_PROMPT_VOICE = """
Eres la IA comercial oficial de la empresa atendiendo una llamada telefónica en tiempo real.

Directrices de Estilo:
1. Responde de manera extremadamente concisa, directa y natural.
2. Evita textos largos o listas numeradas extensas; el interlocutor está escuchando por voz.
3. Si el usuario hace una pregunta sobre el inventario, utiliza la herramienta `consultar_inventario` y resume el resultado en 1 o 2 frases habladas.
4. Si muestra intención de compra o visita, ofrece enviarle la información por WhatsApp o agendar una cita directamente.
"""

HERRAMIENTAS_IA = [
    {
        "type": "function",
        "function": {
            "name": "consultar_inventario",
            "description": "Busca productos, inmuebles o servicios en el catálogo por palabras clave (ej: 'piso', 'alquiler', 'chalet', 'precio').",
            "parameters": {
                "type": "object",
                "properties": {
                    "consulta": {
                        "type": "string",
                        "description": "Término de búsqueda o filtro"
                    }
                },
                "required": ["consulta"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "registrar_interes_lead",
            "description": "Registra un lead/contacto interesado cuando el cliente facilita su nombre y/o teléfono, e indica su interés.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string", "description": "Nombre del cliente"},
                    "telefono": {"type": "string", "description": "Teléfono de contacto"},
                    "interes": {"type": "string", "description": "Producto o servicio de interés"},
                    "notas": {"type": "string", "description": "Presupuesto, preferencias o notas adicionales"}
                },
                "required": ["nombre", "interes"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "agendar_cita_visita",
            "description": "Agenda una fecha y hora para una visita al inmueble o reunión de consultoría comercial.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string", "description": "Nombre del cliente"},
                    "telefono": {"type": "string", "description": "Teléfono del cliente"},
                    "fecha": {"type": "string", "description": "Fecha acordada (ej: '2026-09-05')"},
                    "hora": {"type": "string", "description": "Hora acordada (ej: '11:00')"},
                    "motivo": {"type": "string", "description": "Motivo de la cita (ej: Visita piso céntrico)"}
                },
                "required": ["nombre", "fecha", "hora", "motivo"]
            }
        }
    }
]

def procesar_mensaje_ia(mensajes: List[Dict[str, str]], canal: str = "whatsapp") -> str:
    """
    Procesa una conversación utilizando la API de DeepSeek y Function Calling.
    """
    if settings.OPENAI_API_KEY in ["tu_clave_de_openai", "tu_clave_de_deepseek"]:
        return "Hola, soy el asistente comercial. (Simulación: configura tu DEEPSEEK_API_KEY en tu .env para responder)."

    prompt_sistema = SYSTEM_PROMPT_VOICE if canal == "voz" else SYSTEM_PROMPT_WHATSAPP
    mensajes_con_system = [{"role": "system", "content": prompt_sistema}] + mensajes

    try:
        response = client.chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=mensajes_con_system,
            tools=HERRAMIENTAS_IA,
            tool_choice="auto"
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        if tool_calls:
            mensajes_con_system.append(response_message)

            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                if function_name == "consultar_inventario":
                    resultado = buscar_en_inventario(function_args.get("consulta", ""))
                elif function_name == "registrar_interes_lead":
                    resultado = registrar_lead(
                        nombre=function_args.get("nombre", "Cliente"),
                        telefono=function_args.get("telefono", "No especificado"),
                        canal=canal,
                        interes=function_args.get("interes", ""),
                        notas=function_args.get("notas", "")
                    )
                elif function_name == "agendar_cita_visita":
                    resultado = agendar_cita_demo(
                        nombre=function_args.get("nombre", "Cliente"),
                        telefono=function_args.get("telefono", "No especificado"),
                        fecha=function_args.get("fecha", ""),
                        hora=function_args.get("hora", ""),
                        motivo=function_args.get("motivo", "")
                    )
                else:
                    resultado = {"error": "Función no reconocida"}

                mensajes_con_system.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(resultado, ensure_ascii=False)
                })

            segunda_respuesta = client.chat.completions.create(
                model=settings.DEEPSEEK_MODEL,
                messages=mensajes_con_system
            )
            return segunda_respuesta.choices[0].message.content

        return response_message.content

    except Exception as e:
        logger.error(f"Error procesando llamada a DeepSeek API: {e}")
        return "Disculpa, en este momento estoy teniendo dificultades técnicas. ¿Te gustaría dejar tu número de teléfono para contactarte?"
