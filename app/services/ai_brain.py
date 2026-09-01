import json
import logging
from typing import List, Dict, Any
from openai import OpenAI
from app.config import settings
from app.database import buscar_en_inventario, agendar_cita, _get_db
from app.services.crm import registrar_lead

logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL
)

SYSTEM_PROMPT_WHATSAPP = """
You are the official commercial AI assistant for the business attending via WhatsApp.

MULTILINGUAL INSTRUCTION:
- Automatically detect the language used by the customer in their message (Spanish, English, French, German, Italian, etc.).
- ALWAYS respond in the exact same language the user spoke to you.

CRITICAL TOOL USAGE:
- When the customer asks about services, prices, availability, or options: ALWAYS call `consultar_inventario` FIRST with a broad keyword before responding. Never guess prices or services from memory.
- Use short, generic search terms (1-2 words) that match product names or categories. For example: "corte", "tinte", "paquete", "viaje", "premium".
- If the first search returns empty, try a different keyword before telling the customer you have no results.

Style & Directives:
1. Be friendly, approachable, and professional. Use a natural WhatsApp conversational tone with moderate emojis.
2. Provide clear details about prices, features, and locations when asked.
3. Keep paragraphs short for easy reading on smartphones.
"""

SYSTEM_PROMPT_VOICE = """
You are the official commercial AI assistant attending a real-time phone call.

MULTILINGUAL INSTRUCTION:
- Automatically detect the language of the caller and respond in the exact same language.

Style & Directives:
1. Speak in an extremely concise, direct, and natural manner.
2. Avoid long paragraphs or bulleted lists as the user is listening to speech.
3. If asked about inventory, call `consultar_inventario` and summarize the result in 1 or 2 spoken sentences.
4. Offer to send details via WhatsApp or schedule a visit directly.
"""

HERRAMIENTAS_IA = [
    {
        "type": "function",
        "function": {
            "name": "consultar_inventario",
            "description": "Searches products, properties, or services in the catalog by keywords (e.g. 'apartment', 'rent', 'villa', 'price', 'piso').",
            "parameters": {
                "type": "object",
                "properties": {
                    "consulta": {
                        "type": "string",
                        "description": "Search keyword or filter"
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
            "description": "Registers a lead when the customer provides their name, phone, or expresses interest in a product.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string", "description": "Customer name"},
                    "telefono": {"type": "string", "description": "Phone number"},
                    "interes": {"type": "string", "description": "Product or service of interest"},
                    "notas": {"type": "string", "description": "Budget or additional notes"}
                },
                "required": ["nombre", "interes"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "agendar_cita_visita",
            "description": "Schedules a date and time for a property visit or sales meeting.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string", "description": "Customer name"},
                    "telefono": {"type": "string", "description": "Customer phone"},
                    "fecha": {"type": "string", "description": "Agreed date (e.g. '2026-09-05')"},
                    "hora": {"type": "string", "description": "Agreed time (e.g. '11:00')"},
                    "motivo": {"type": "string", "description": "Reason for appointment"}
                },
                "required": ["nombre", "fecha", "hora", "motivo"]
            }
        }
    }
]

def procesar_mensaje_ia(mensajes: List[Dict[str, str]], canal: str = "whatsapp", cliente_id: str = "default") -> str:
    """
    Procesa una conversación con DeepSeek aislando datos por cliente_id.
    """
    if settings.OPENAI_API_KEY in ["tu_clave_de_openai", "tu_clave_de_deepseek"]:
        raise ValueError("OPENAI_API_KEY no configurada. Configura tu DEEPSEEK_API_KEY en .env")

    nombre_empresa = cliente_id
    db = _get_db()
    if db:
        try:
            doc = db.collection("clientes").document(cliente_id).get()
            if doc.exists:
                nombre_empresa = doc.to_dict().get("nombre_empresa", cliente_id)
        except Exception:
            pass

    prompt_base = SYSTEM_PROMPT_VOICE if canal == "voz" else SYSTEM_PROMPT_WHATSAPP
    prompt_sistema = f"You work for '{nombre_empresa}'. {prompt_base}"
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
                    resultado = buscar_en_inventario(function_args.get("consulta", ""), cliente_id=cliente_id)
                elif function_name == "registrar_interes_lead":
                    resultado = registrar_lead(
                        nombre=function_args.get("nombre", "Cliente"),
                        telefono=function_args.get("telefono", "No especificado"),
                        canal=canal,
                        interes=function_args.get("interes", ""),
                        notas=function_args.get("notas", ""),
                        cliente_id=cliente_id
                    )
                elif function_name == "agendar_cita_visita":
                    resultado = agendar_cita(
                        nombre=function_args.get("nombre", "Cliente"),
                        telefono=function_args.get("telefono", "No especificado"),
                        fecha=function_args.get("fecha", ""),
                        hora=function_args.get("hora", ""),
                        motivo=function_args.get("motivo", ""),
                        cliente_id=cliente_id
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
        logger.error(f"Error procesando llamada a DeepSeek API para cliente {cliente_id}: {e}")
        return "Disculpa, en este momento estoy teniendo dificultades técnicas. ¿Te gustaría dejar tu número de teléfono para contactarte?"
