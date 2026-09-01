import logging
import httpx
from app.config import settings
from app.database import _get_db

logger = logging.getLogger(__name__)

ELEVENLABS_BASE = "https://api.elevenlabs.io/v1"


async def clonar_voz(cliente_id: str, audio_bytes: bytes, filename: str) -> dict:
    api_key = settings.ELEVENLABS_API_KEY
    if not api_key:
        return {"error": "ELEVENLABS_API_KEY no configurada"}

    db = _get_db()
    if not db:
        return {"error": "Base de datos no disponible"}

    doc = db.collection("clientes").document(cliente_id).get()
    if not doc.exists:
        return {"error": "Cliente no encontrado"}

    nombre_empresa = doc.to_dict().get("nombre_empresa", cliente_id)
    voice_name = f"telefonista_{cliente_id}"

    old_voice_id = doc.to_dict().get("elevenlabs_voice_id", "")
    if old_voice_id:
        try:
            async with httpx.AsyncClient() as client:
                await client.delete(
                    f"{ELEVENLABS_BASE}/voices/{old_voice_id}",
                    headers={"xi-api-key": api_key},
                    timeout=15
                )
        except Exception as e:
            logger.warning(f"No se pudo borrar voz anterior {old_voice_id}: {e}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ELEVENLABS_BASE}/voices/add",
                headers={"xi-api-key": api_key},
                data={
                    "name": voice_name,
                    "description": f"Voz clonada para {nombre_empresa}",
                },
                files={"files": (filename, audio_bytes, "audio/mpeg")},
                timeout=60
            )

        if response.status_code != 200:
            logger.error(f"ElevenLabs error {response.status_code}: {response.text}")
            return {"error": f"Error de ElevenLabs: {response.status_code}"}

        voice_id = response.json().get("voice_id")
        if not voice_id:
            return {"error": "No se obtuvo voice_id de ElevenLabs"}

        db.collection("clientes").document(cliente_id).set(
            {"elevenlabs_voice_id": voice_id}, merge=True
        )

        return {"status": "ok", "voice_id": voice_id, "message": f"Voz clonada para {nombre_empresa}"}

    except Exception as e:
        logger.error(f"Error clonando voz para {cliente_id}: {e}")
        return {"error": str(e)}


async def eliminar_voz_clonada(cliente_id: str) -> dict:
    api_key = settings.ELEVENLABS_API_KEY
    if not api_key:
        return {"error": "ELEVENLABS_API_KEY no configurada"}

    db = _get_db()
    if not db:
        return {"error": "Base de datos no disponible"}

    doc = db.collection("clientes").document(cliente_id).get()
    if not doc.exists:
        return {"error": "Cliente no encontrado"}

    voice_id = doc.to_dict().get("elevenlabs_voice_id", "")
    if not voice_id:
        return {"status": "ok", "message": "No habia voz clonada"}

    try:
        async with httpx.AsyncClient() as client:
            await client.delete(
                f"{ELEVENLABS_BASE}/voices/{voice_id}",
                headers={"xi-api-key": api_key},
                timeout=15
            )
    except Exception as e:
        logger.warning(f"Error borrando voz {voice_id}: {e}")

    db.collection("clientes").document(cliente_id).set(
        {"elevenlabs_voice_id": ""}, merge=True
    )

    return {"status": "ok", "message": "Voz clonada eliminada"}
