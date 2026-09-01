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
    inventario: List[ProductoItem]

@router.post("/alta-cliente")
def dar_de_alta_cliente(payload: CrearClientePayload):
    """
    Endpoint para dar de alta a un cliente nuevo y guardar sus productos/servicios 
    en Firestore (o en memoria/fallback).
    """
    cliente_id = payload.cliente_id.lower().replace(" ", "_")
    items_dict = [item.model_dump() for item in payload.inventario]

    # 1. Guardar en Firebase Firestore
    if db:
        try:
            doc_ref = db.collection("clientes").document(cliente_id)
            doc_ref.set({"nombre_empresa": payload.nombre_empresa, "creado_el": firestore.SERVER_TIMESTAMP})

            for item in items_dict:
                doc_ref.collection("inventario").add(item)
                
            logger.info(f"[Firebase Firestore] Cliente {cliente_id} dado de alta exitosamente.")
        except Exception as e:
            logger.error(f"Error guardando en Firestore: {e}")

    # 2. Guardar en memoria local (Fallback)
    CATALOGO_CLIENTES[cliente_id] = items_dict

    return {
        "status": "success",
        "message": f"Cliente '{payload.nombre_empresa}' dado de alta correctamente.",
        "cliente_id": cliente_id,
        "webhook_whatsapp_url": f"http://178.156.186.149:8089/api/v1/whatsapp/evolution-webhook/{cliente_id}",
        "webhook_voz_url": f"http://178.156.186.149:8089/api/v1/voice/webhook/{cliente_id}"
    }

@router.get("/lista-clientes")
def listar_clientes():
    """Retorna la lista de todos los clientes/empresas registrados."""
    if db:
        try:
            docs = db.collection("clientes").stream()
            clientes = [{"cliente_id": doc.id, **doc.to_dict()} for doc in docs]
            if clientes:
                return {"clientes": clientes}
        except Exception as e:
            logger.error(f"Error consultando clientes en Firestore: {e}")

    return {"clientes": list(CATALOGO_CLIENTES.keys())}
