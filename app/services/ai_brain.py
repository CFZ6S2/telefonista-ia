import json
import logging
from typing import List, Dict, Any
from openai import AsyncOpenAI
from app.config import settings
from app.database import buscar_en_inventario, agendar_cita, _get_db
from app.services.crm import registrar_lead

logger = logging.getLogger(__name__)

client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL,
    timeout=15.0
)

SYSTEM_PROMPT_WHATSAPP = """
You are the AI assistant for this business on WhatsApp. You MUST follow these rules strictly:

1. YOUR IDENTITY AND PERSONALITY: You ARE the person/business described in the BUSINESS CONFIGURATION above. Adopt the name, personality, tone and style defined there. If INSTRUCCIONES ESPECIALES say to be flirty, be flirty. If they say to be formal, be formal. Follow them exactly.

2. YOUR KNOWLEDGE: You ONLY know what is in the BUSINESS CONFIGURATION. Use the exact prices, services, rules, schedule and location listed there. NEVER invent or guess anything not listed.

3. LANGUAGE: Respond in the same language the customer uses.

4. FORMAT: Short messages, natural WhatsApp tone, emojis only if the business style calls for it.

5. TOOLS: Only call `consultar_inventario` if the business has a product catalog configured.
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

async def procesar_mensaje_ia(mensajes: List[Dict[str, str]], canal: str = "whatsapp", cliente_id: str = "default") -> str:
    """
    Procesa una conversación con DeepSeek aislando datos por cliente_id.
    """
    nombre_empresa = cliente_id
    config_negocio = ""
    db = _get_db()
    if db:
        try:
            doc = db.collection("clientes").document(cliente_id).get()
            if doc.exists:
                data = doc.to_dict()
                nombre_empresa = data.get("nombre_empresa", cliente_id)
                partes = []
                if data.get("horario"):
                    partes.append(f"HORARIO: {data['horario']}")
                if data.get("direccion"):
                    partes.append(f"UBICACION: {data['direccion']}")
                if data.get("tarifas"):
                    partes.append(f"TARIFAS Y PRECIOS: {data['tarifas']}")
                if data.get("reglas"):
                    partes.append(f"REGLAS Y CONDICIONES: {data['reglas']}")
                if data.get("instrucciones_ia"):
                    partes.append(f"INSTRUCCIONES ESPECIALES: {data['instrucciones_ia']}")
                if partes:
                    config_negocio = "\n\n=== BUSINESS CONFIGURATION (THIS IS WHO YOU ARE) ===\n" + "\n".join(partes) + "\n=== END CONFIGURATION ==="
        except Exception:
            pass

    prompt_base = SYSTEM_PROMPT_VOICE if canal == "voz" else SYSTEM_PROMPT_WHATSAPP
    prompt_sistema = f"You are '{nombre_empresa}'.{config_negocio}\n\n{prompt_base}"
    mensajes_con_system = [{"role": "system", "content": prompt_sistema}] + mensajes

    try:
        if settings.OPENAI_API_KEY in ["tu_clave_de_openai", "tu_clave_de_deepseek", ""]:
            raise ValueError("OPENAI_API_KEY no configurada. Configura tu API KEY en .env")


        response = await client.chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=mensajes_con_system,
            tools=HERRAMIENTAS_IA,
            tool_choice="auto",
            timeout=15.0
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

            segunda_respuesta = await client.chat.completions.create(
                model=settings.DEEPSEEK_MODEL,
                messages=mensajes_con_system,
                timeout=15.0
            )
            return segunda_respuesta.choices[0].message.content

        return response_message.content

    except Exception as e:
        logger.error(f"Error procesando llamada a DeepSeek API para cliente {cliente_id}: {e}")
        return "Disculpa, en este momento estoy teniendo dificultades técnicas. ¿Te gustaría dejar tu número de teléfono para contactarte?"
