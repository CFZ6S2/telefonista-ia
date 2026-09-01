from fastapi import APIRouter, Request
import logging
from app.services.ai_brain import procesar_mensaje_ia
from app.database import buscar_en_inventario, agendar_cita, guardar_mensaje_historial, obtener_historial_conversacion, obtener_estado_ia, _get_db

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/webhook/{cliente_id}")
async def voice_assistant_multi_tenant_webhook(cliente_id: str, request: Request):
    """
    Webhook multi-cliente para asistentes de voz (Vapi.ai / Retell AI).
    URL: /api/v1/voice/webhook/clinica_sonrisas
    """
    try:
        body = await request.json()
    except Exception:
        return {"status": "error", "message": "Invalid JSON"}
    logger.info(f"[Voice Payload ({cliente_id})]: {body}")

    message = body.get("message", {})
    type_event = message.get("type")

    if type_event == "assistant-request":
        db = _get_db()
        telefono_personal = ""
        nombre_empresa = cliente_id
        elevenlabs_voice_id = ""
        if db:
            try:
                doc = db.collection("clientes").document(cliente_id).get()
                if doc.exists:
                    data = doc.to_dict()
                    telefono_personal = data.get("telefono_personal", "")
                    nombre_empresa = data.get("nombre_empresa", cliente_id)
                    elevenlabs_voice_id = data.get("elevenlabs_voice_id", "")
            except Exception:
                pass

        if not obtener_estado_ia(cliente_id):
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

        if elevenlabs_voice_id:
            return {
                "assistant": {
                    "voice": {
                        "provider": "11labs",
                        "voiceId": elevenlabs_voice_id
                    }
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
                res = buscar_en_inventario(args.get("consulta", ""), cliente_id=cliente_id)
            elif name == "agendar_cita_visita":
                res = agendar_cita(
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
        guardar_mensaje_historial(cliente_id, caller_number, "user", transcript)

        historial = obtener_historial_conversacion(cliente_id, caller_number, limite=6)
        if not historial:
            historial = [{"role": "user", "content": transcript}]

        respuesta = await procesar_mensaje_ia(historial, canal="voz", cliente_id=cliente_id)
        guardar_mensaje_historial(cliente_id, caller_number, "assistant", respuesta)
        return {"response": respuesta}

    return {"status": "ok"}
