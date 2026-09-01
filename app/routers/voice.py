from fastapi import APIRouter, Request
import logging
from app.services.ai_brain import procesar_mensaje_ia

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/webhook/{cliente_id}")
async def voice_assistant_multi_tenant_webhook(cliente_id: str, request: Request):
    """
    Webhook multi-cliente para asistentes de voz (Vapi.ai / Retell AI).
    URL: /api/v1/voice/webhook/clinica_sonrisas
    """
    body = await request.json()
    logger.info(f"[Voice Payload ({cliente_id})]: {body}")

    message = body.get("message", {})
    type_event = message.get("type")

    if type_event == "tool-calls":
        tool_calls = message.get("toolCalls", [])
        results = []
        for call in tool_calls:
            function_data = call.get("function", {})
            name = function_data.get("name")
            args = function_data.get("arguments", {})

            if name == "consultar_inventario":
                from app.database import buscar_en_inventario
                res = buscar_en_inventario(args.get("consulta", ""), cliente_id=cliente_id)
            elif name == "agendar_cita_visita":
                from app.database import agendar_cita_demo
                res = agendar_cita_demo(
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
    if transcript:
        conversacion = [{"role": "user", "content": transcript}]
        respuesta = procesar_mensaje_ia(conversacion, canal="voz", cliente_id=cliente_id)
        return {"response": respuesta}

    return {"status": "ok"}
