from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging
from app.database import db, CATALOGO_CLIENTES

logger = logging.getLogger(__name__)

router = APIRouter()

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
    inventario: List[ProductoItem]

@router.post("/alta-cliente")
def dar_de_alta_cliente(payload: CrearClientePayload):
    """
    Endpoint para dar de alta a un cliente nuevo guardando opcionalmente 
    sus dos números de contacto distintos (uno para llamadas y otro para WhatsApp).
    """
    cliente_id = payload.cliente_id.lower().replace(" ", "_")
    items_dict = [item.model_dump() for item in payload.inventario]

    # 1. Guardar en Firebase Firestore
    if db:
        try:
            doc_ref = db.collection("clientes").document(cliente_id)
            doc_ref.set({
                "nombre_empresa": payload.nombre_empresa,
                "telefono_voz": payload.telefono_voz,
                "telefono_whatsapp": payload.telefono_whatsapp,
                "creado_el": firestore.SERVER_TIMESTAMP
            })

            for item in items_dict:
                doc_ref.collection("inventario").add(item)
                
            logger.info(f"[Firebase Firestore] Cliente {cliente_id} registrado.")
        except Exception as e:
            logger.error(f"Error guardando en Firestore: {e}")

    # 2. Guardar en memoria local (Fallback)
    CATALOGO_CLIENTES[cliente_id] = items_dict

    return {
        "status": "success",
        "message": f"Cliente '{payload.nombre_empresa}' configurado exitosamente con sus 2 canales.",
        "cliente_id": cliente_id,
        "telefono_voz_cliente": payload.telefono_voz,
        "telefono_whatsapp_cliente": payload.telefono_whatsapp,
        "webhook_whatsapp_url": f"http://178.156.186.149:8089/api/v1/whatsapp/evolution-webhook/{cliente_id}",
        "webhook_voz_url": f"http://178.156.186.149:8089/api/v1/voice/webhook/{cliente_id}"
    }
