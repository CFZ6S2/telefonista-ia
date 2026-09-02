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

async def _guardar_llamada_completa(cliente_id: str, body: dict):
    """Guarda la transcripcion completa y datos de una llamada finalizada en Firestore."""
    from app.database import _get_db, _server_timestamp
    from fastapi.concurrency import run_in_threadpool
    from app.services.crm import registrar_lead

    message = body.get("message", {})
    call_data = message.get("call", {}) or body.get("call", {})
    customer = call_data.get("customer", {})
    caller_number = customer.get("number", "voz_desconocido")

    transcript_raw = message.get("transcript", "")
    artifact = message.get("artifact", {})
    messages_list = artifact.get("messages", [])
    summary = message.get("summary") or artifact.get("summary", "")
    duration_seconds = message.get("durationSeconds") or call_data.get("duration")
    ended_reason = message.get("endedReason", "")

    remitente = f"voz_{caller_number}"

    if messages_list:
        for msg in messages_list:
            role = msg.get("role", "user")
            content = msg.get("message") or msg.get("content", "")
            if not content:
                continue
            if role in ("bot", "assistant"):
                role = "assistant"
            elif role in ("user", "customer"):
                role = "user"
            else:
                continue
            await guardar_mensaje_historial_async(cliente_id, remitente, role, content)
    elif transcript_raw:
        await guardar_mensaje_historial_async(cliente_id, remitente, "user", transcript_raw)

    def guardar_resumen():
        db = _get_db()
        if not db:
            return
        doc_data = {
            "tipo": "voz",
            "telefono": caller_number,
            "duracion_segundos": duration_seconds,
            "resumen": summary,
            "motivo_fin": ended_reason,
            "timestamp": _server_timestamp(),
        }
        db.collection("clientes").document(cliente_id)\
          .collection("conversaciones").document(remitente)\
          .set(doc_data, merge=True)

    await run_in_threadpool(guardar_resumen)

    if caller_number and caller_number != "voz_desconocido":
        await run_in_threadpool(
            registrar_lead,
            nombre=f"Llamada de {caller_number}",
            telefono=caller_number,
            canal="voz",
            interes=summary[:200] if summary else "Llamada de voz",
            notas=f"Duración: {duration_seconds or '?'}s. Fin: {ended_reason}",
            cliente_id=cliente_id,
        )

    logger.info(f"[Voice] Llamada guardada para {cliente_id}: {remitente}, {len(messages_list)} msgs, {duration_seconds}s")


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

    if type_event == "end-of-call-report":
        await _guardar_llamada_completa(cliente_id, body)
        return {"status": "ok"}

    if type_event == "assistant-request":
        telefono_personal = ""
        nombre_empresa = cliente_id
        voz_asistente = ""

        data = await get_cliente_doc_async(cliente_id) or {}
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

        partes = []
        if data.get("horario"):
            partes.append(f"HORARIO: {data['horario']}")
        if data.get("direccion"):
            partes.append(f"UBICACION/DIRECCION: {data['direccion']}")
        if data.get("tarifas"):
            partes.append(f"TARIFAS Y PRECIOS: {data['tarifas']}")
        if data.get("reglas"):
            partes.append(f"REGLAS Y CONDICIONES: {data['reglas']}")
        if data.get("instrucciones_ia"):
            partes.append(f"INSTRUCCIONES ESPECIALES: {data['instrucciones_ia']}")
        config_negocio = "\n".join(partes)

        system_prompt = f"""You are '{nombre_empresa}', answering a real-time phone call.

=== BUSINESS CONFIGURATION (THIS IS WHO YOU ARE) ===
{config_negocio}
=== END CONFIGURATION ===

RULES:
1. You ARE {nombre_empresa}. Adopt the personality and tone from INSTRUCCIONES ESPECIALES above.
2. You ONLY know what is listed above. Use exact prices, address, schedule. NEVER invent data.
3. Detect the caller's language and respond in the same language.
4. Speak in short, natural sentences suitable for voice. No lists or bullet points.
5. If asked for the address/location, give it exactly as listed above.
6. Offer to send details via WhatsApp or schedule a visit when appropriate."""

        VOCES = {
            "openai_alloy": {"provider": "openai", "voiceId": "alloy"},
            "openai_echo": {"provider": "openai", "voiceId": "echo"},
            "openai_nova": {"provider": "openai", "voiceId": "nova"},
            "openai_onyx": {"provider": "openai", "voiceId": "onyx"},
            "openai_shimmer": {"provider": "openai", "voiceId": "shimmer"},
            "openai_fable": {"provider": "openai", "voiceId": "fable"},
        }
        voz_config = VOCES.get(voz_asistente, {"provider": "openai", "voiceId": "shimmer"})

        return {
            "assistant": {
                "firstMessage": f"Hola, has llamado a {nombre_empresa}, en que te puedo ayudar?",
                "model": {
                    "provider": "openai",
                    "model": "gpt-4o",
                    "messages": [{"role": "system", "content": system_prompt}]
                },
                "voice": voz_config,
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

    return {"status": "ok"}
