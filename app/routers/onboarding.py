from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
import httpx
from app.database import _get_db, _server_timestamp
from app.services.evolution_manager import crear_instancia_evolution_y_conectar_webhook, obtener_qr_instancia_evolution
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

EVOLUTION_API_BASE = settings.EVOLUTION_API_BASE
EVOLUTION_GLOBAL_KEY = settings.EVOLUTION_API_KEY


class OnboardingPayload(BaseModel):
    nombre_empresa: str
    telefono_whatsapp: str
    nombre_contacto: str
    email: Optional[str] = ""


@router.post("/iniciar")
async def iniciar_onboarding(payload: OnboardingPayload):
    cliente_id = payload.nombre_empresa.lower().strip().replace(" ", "_").replace(".", "")
    cliente_id = "".join(c for c in cliente_id if c.isalnum() or c == "_")

    db = _get_db()
    if db:
        existing = db.collection("clientes").document(cliente_id).get()
        if existing.exists:
            raise HTTPException(status_code=409, detail="Ya existe una empresa con ese nombre. Contacta con soporte.")

    vps_base_url = getattr(settings, "VPS_PUBLIC_URL", "http://telefonista-api.duckdns.org")
    res_evolution = await crear_instancia_evolution_y_conectar_webhook(cliente_id, vps_base_url)

    if db:
        try:
            db.collection("clientes").document(cliente_id).set({
                "nombre_empresa": payload.nombre_empresa,
                "telefono_whatsapp": payload.telefono_whatsapp,
                "nombre_contacto": payload.nombre_contacto,
                "email": payload.email,
                "ia_activa": True,
                "onboarding_completado": False,
                "creado_el": _server_timestamp()
            })
        except Exception as e:
            logger.error(f"Error guardando cliente onboarding: {e}")

    qr_base64 = res_evolution.get("qrcode")

    return {
        "status": "ok",
        "cliente_id": cliente_id,
        "qrcode": qr_base64,
        "message": "Instancia creada. Escanea el codigo QR con WhatsApp."
    }


@router.get("/qr/{cliente_id}")
async def obtener_qr_onboarding(cliente_id: str):
    data = await obtener_qr_instancia_evolution(cliente_id)
    return data


@router.get("/estado/{cliente_id}")
async def verificar_estado_conexion(cliente_id: str):
    url = f"{EVOLUTION_API_BASE}/instance/connectionState/{cliente_id}"
    headers = {"apikey": EVOLUTION_GLOBAL_KEY}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                state = data.get("instance", {}).get("state", "unknown")
                connected = state == "open"

                if connected:
                    db = _get_db()
                    if db:
                        db.collection("clientes").document(cliente_id).set(
                            {"onboarding_completado": True}, merge=True
                        )

                return {"cliente_id": cliente_id, "state": state, "connected": connected}
    except Exception as e:
        logger.error(f"Error verificando estado de {cliente_id}: {e}")

    return {"cliente_id": cliente_id, "state": "error", "connected": False}


@router.get("/mi-empresa")
def buscar_empresa_por_email(email: str):
    db = _get_db()
    if not db:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")
    docs = db.collection("clientes").where("email", "==", email.lower().strip()).limit(1).stream()
    for doc in docs:
        data = doc.to_dict()
        return {
            "cliente_id": doc.id,
            "nombre_empresa": data.get("nombre_empresa", ""),
            "horario": data.get("horario", ""),
            "direccion": data.get("direccion", ""),
            "tarifas": data.get("tarifas", ""),
            "reglas": data.get("reglas", ""),
            "instrucciones_ia": data.get("instrucciones_ia", ""),
            "telefono_personal": data.get("telefono_personal", ""),
            "voz_asistente": data.get("voz_asistente", ""),
            "ia_activa": data.get("ia_activa", True),
            "telefono_voz": data.get("telefono_voz", "")
        }
    raise HTTPException(status_code=404, detail="No hay empresa registrada con ese email")


class ConfigNegocioPayload(BaseModel):
    horario: Optional[str] = ""
    direccion: Optional[str] = ""
    tarifas: Optional[str] = ""
    reglas: Optional[str] = ""
    instrucciones_ia: Optional[str] = ""
    telefono_personal: Optional[str] = ""
    voz_asistente: Optional[str] = ""
    ia_activa: Optional[bool] = None


@router.get("/config/{cliente_id}")
def obtener_config_negocio(cliente_id: str):
    db = _get_db()
    if not db:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")
    doc = db.collection("clientes").document(cliente_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    data = doc.to_dict()
    return {
        "cliente_id": cliente_id,
        "nombre_empresa": data.get("nombre_empresa", ""),
        "horario": data.get("horario", ""),
        "direccion": data.get("direccion", ""),
        "tarifas": data.get("tarifas", ""),
        "reglas": data.get("reglas", ""),
        "instrucciones_ia": data.get("instrucciones_ia", ""),
        "telefono_personal": data.get("telefono_personal", ""),
        "voz_asistente": data.get("voz_asistente", ""),
        "ia_activa": data.get("ia_activa", True),
        "telefono_voz": data.get("telefono_voz", "")
    }


@router.post("/config/{cliente_id}")
def guardar_config_negocio(cliente_id: str, payload: ConfigNegocioPayload):
    db = _get_db()
    if not db:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")
    doc = db.collection("clientes").document(cliente_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    try:
        db.collection("clientes").document(cliente_id).set(
            payload.model_dump(exclude_none=True), merge=True
        )
        return {"status": "ok", "message": "Configuracion guardada. La IA usara estos datos a partir de ahora."}
    except Exception as e:
        logger.error(f"Error guardando config negocio: {e}")
        raise HTTPException(status_code=500, detail="Error guardando configuracion")
