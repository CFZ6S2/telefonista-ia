from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from typing import List, Optional
import logging
from app.database import _get_db, _server_timestamp
from app.services.evolution_manager import crear_instancia_evolution_y_conectar_webhook, obtener_qr_instancia_evolution
from app.services.vapi_manager import crear_o_vincular_asistente_vapi
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

def verificar_admin_api_key(api_key: str = Depends(API_KEY_HEADER)):
    admin_secret = getattr(settings, "ADMIN_SECRET_KEY", None)
    if admin_secret and api_key != admin_secret:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid Admin API Key")
    return True

class ProductoItem(BaseModel):
    nombre: str
    categoria: str
    precio: str
    detalles: str
    ubicacion: Optional[str] = "No especificada"

class CrearClientePayload(BaseModel):
    cliente_id: str
    nombre_empresa: str
    telefono_voz: Optional[str] = "No configurado"
    telefono_whatsapp: Optional[str] = "No configurado"
    vapi_api_key: Optional[str] = None
    inventario: List[ProductoItem]

@router.post("/alta-cliente", dependencies=[Depends(verificar_admin_api_key)])
async def dar_de_alta_cliente(payload: CrearClientePayload):
    cliente_id = payload.cliente_id.lower().replace(" ", "_")
    items_dict = [item.model_dump() for item in payload.inventario]
    vps_base_url = getattr(settings, "VPS_PUBLIC_URL", "http://telefonista-api.duckdns.org")

    res_evolution = await crear_instancia_evolution_y_conectar_webhook(cliente_id, vps_base_url)

    res_vapi = await crear_o_vincular_asistente_vapi(
        cliente_id=cliente_id,
        nombre_empresa=payload.nombre_empresa,
        webhook_base_url=vps_base_url,
        vapi_api_key=payload.vapi_api_key
    )

    db = _get_db()
    if db:
        try:
            doc_ref = db.collection("clientes").document(cliente_id)
            doc_ref.set({
                "nombre_empresa": payload.nombre_empresa,
                "telefono_voz": payload.telefono_voz,
                "telefono_whatsapp": payload.telefono_whatsapp,
                "vapi_status": res_vapi,
                "evolution_status": res_evolution.get("status"),
                "creado_el": _server_timestamp()
            })

            for item in items_dict:
                doc_ref.collection("inventario").add(item)

            logger.info(f"[Firestore] Cliente {cliente_id} registrado.")
        except Exception as e:
            logger.error(f"Error guardando en Firestore: {e}")
    else:
        raise HTTPException(status_code=503, detail="Firestore no disponible. No se pudo registrar el cliente.")

    return {
        "status": "success",
        "message": f"Cliente '{payload.nombre_empresa}' dado de alta y conectado a WhatsApp y Vapi.",
        "cliente_id": cliente_id,
        "evolution_whatsapp": res_evolution,
        "vapi_voz": res_vapi,
        "webhook_whatsapp_url": f"{vps_base_url}/api/v1/whatsapp/evolution-webhook/{cliente_id}",
        "webhook_voz_url": f"{vps_base_url}/api/v1/voice/webhook/{cliente_id}"
    }

@router.get("/qr-whatsapp/{cliente_id}")
async def ver_qr_whatsapp(cliente_id: str):
    data = await obtener_qr_instancia_evolution(cliente_id)
    return data

@router.get("/lista-clientes")
def listar_clientes():
    db = _get_db()
    if not db:
        return {"clientes": []}
    try:
        docs = db.collection("clientes").stream()
        clientes = [{"cliente_id": doc.id, **doc.to_dict()} for doc in docs]
        return {"clientes": clientes}
    except Exception as e:
        logger.error(f"Error consultando clientes en Firestore: {e}")
        return {"clientes": []}
