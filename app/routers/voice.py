from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
from app.services.ai_brain import procesar_mensaje_ia
from app.database import buscar_en_inventario
from app.services.crm import registrar_lead

logger = logging.getLogger(__name__)

router = APIRouter()

class VoiceWebhookPayload(BaseModel):
    caller_number: Optional[str] = "Desconocido"
    transcript: Optional[str] = ""
    call_id: Optional[str] = None

@router.post("/webhook")
async def voice_assistant_webhook(request: Request):
    """
    Webhook genérico para agentes de voz en tiempo real (Vapi.ai / Retell AI / Bland AI).
    Recibe la transcripción parcial/total y devuelve la instrucción de respuesta o función a ejecutar.
    """
    body = await request.json()
    logger.info(f"[Voice Payload Received]: {body}")

    # Ejemplo de formateo adaptable a Vapi.ai / Retell AI
    message = body.get("message", {})
    type_event = message.get("type")

    # Manejo de Function Callings solicitados por Vapi/Retell
    if type_event == "tool-calls":
        tool_calls = message.get("toolCalls", [])
        results = []
        for call in tool_calls:
            function_data = call.get("function", {})
            name = function_data.get("name")
            args = function_data.get("arguments", {})

            if name == "consultar_inventario":
                res = buscar_en_inventario(args.get("consulta", ""))
            elif name == "registrar_interes_lead":
                res = registrar_lead(
                    nombre=args.get("nombre", "Llamada Voz"),
                    telefono=args.get("telefono", "Voz"),
                    canal="voz",
                    interes=args.get("interes", ""),
                    notas=args.get("notas", "")
                )
            else:
                res = {"status": "ok"}

            results.append({
                "toolCallId": call.get("id"),
                "result": res
            })

        return {"results": results}

    # Procesamiento básico si nos envían una transcripción directa
    transcript = body.get("transcript") or message.get("transcript")
    if transcript:
        conversacion = [{"role": "user", "content": transcript}]
        respuesta = procesar_mensaje_ia(conversacion, canal="voz")
        return {"response": respuesta}

    return {"status": "ok", "message": "Evento de voz procesado correctamente."}
