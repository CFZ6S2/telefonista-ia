from fastapi import APIRouter, Request, HTTPException
import logging
from app.services.ai_brain import procesar_mensaje_ia
from app.database import (
    buscar_en_inventario_async, agendar_cita_async, guardar_mensaje_historial_async, 
    obtener_historial_conversacion_async, obtener_estado_ia_async, get_cliente_doc_async
)
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/webhook/{cliente_id}")
async def voice_assistant_multi_tenant_webhook(cliente_id: str, request: Request):
    """
    Webhook multi-cliente para asistentes de voz (Vapi.ai / Retell AI).
    URL: /api/v1/voice/webhook/clinica_sonrisas
    """
    vapi_secret = request.headers.get("x-vapi-secret")
    if vapi_secret != settings.WEBHOOK_SECRET:
        logger.warning(f"Intento de acceso no autorizado a Vapi Webhook para {cliente_id}")
        raise HTTPException(status_code=401, detail="Unauthorized webhook caller")

    try:
        body = await request.json()
    except Exception:
        return {"status": "error", "message": "Invalid JSON"}
    logger.info(f"[Voice Payload ({cliente_id})]: {body}")

    message = body.get("message", {})
    type_event = message.get("type")

    if type_event == "assistant-request":
        telefono_personal = ""
        nombre_empresa = cliente_id
        voz_asistente = ""
        
        data = await get_cliente_doc_async(cliente_id)
        if data:
            telefono_personal = data.get("telefono_personal", "")
            nombre_empresa = data.get("nombre_empresa", cliente_id)
            voz_asistente = data.get("voz_asistente", "")

        ia_activa = await obtener_estado_ia_async(cliente_id)
        if not ia_activa:
            if telefono_personal:
                return {
                    "messageResponse": {
                        "type": "transfer-call",
                        "destination": {
                            "type": "number",
                            "number": telefono_personal,
                            "message": f"Te paso con {nombre_empresa}. Un momento por favor."
                        }
                    }
                }
            else:
                return {
                    "messageResponse": {
                        "type": "end-call",
                        "message": f"Gracias por llamar a {nombre_empresa}. En este momento no estamos disponibles. Por favor, intentalo mas tarde o escribenos por WhatsApp."
                    }
                }
        if voz_asistente:
            VOCES = {
                "openai_alloy": {"provider": "openai", "voiceId": "alloy"},
                "openai_echo": {"provider": "openai", "voiceId": "echo"},
                "openai_nova": {"provider": "openai", "voiceId": "nova"},
                "openai_onyx": {"provider": "openai", "voiceId": "onyx"},
                "openai_shimmer": {"provider": "openai", "voiceId": "shimmer"},
                "openai_fable": {"provider": "openai", "voiceId": "fable"},
            }
            voz_config = VOCES.get(voz_asistente)
            if voz_config:
                return {
                    "assistant": {
                        "voice": voz_config
                    }
                }

    if type_event == "tool-calls":
        tool_calls = message.get("toolCalls", [])
        results = []
        for call in tool_calls:
            function_data = call.get("function", {})
            name = function_data.get("name")
            args = function_data.get("arguments", {})

            if name == "consultar_inventario":
                res = await buscar_en_inventario_async(args.get("consulta", ""), cliente_id=cliente_id)
            elif name == "agendar_cita_visita":
                res = await agendar_cita_async(
                    nombre=args.get("nombre", "Cliente Voz"),
                    telefono=args.get("telefono", "Voz"),
                    fecha=args.get("fecha", ""),
                    hora=args.get("hora", ""),
                    motivo=args.get("motivo", ""),
                    cliente_id=cliente_id
                )
            else:
                res = {"status": "ok"}

            results.append({
                "toolCallId": call.get("id"),
                "result": res
            })

        return {"results": results}

    transcript = body.get("transcript") or message.get("transcript")
    caller_number = body.get("call", {}).get("customer", {}).get("number", "voz_desconocido")

    if transcript:
        await guardar_mensaje_historial_async(cliente_id, caller_number, "user", transcript)

        historial = await obtener_historial_conversacion_async(cliente_id, caller_number, limite=6)
        if not historial:
            historial = [{"role": "user", "content": transcript}]

        respuesta = await procesar_mensaje_ia(historial, canal="voz", cliente_id=cliente_id)
        await guardar_mensaje_historial_async(cliente_id, caller_number, "assistant", respuesta)
        return {"response": respuesta}

    return {"status": "ok"}
