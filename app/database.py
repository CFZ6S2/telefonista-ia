from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
from firebase_admin import firestore
from app.config import settings

logger = logging.getLogger(__name__)

# Intentar obtener cliente de Firestore desde Firebase Admin SDK
try:
    import firebase_admin
    db = firestore.client() if firebase_admin._apps else None
except Exception as e:
    logger.warning(f"Firestore Client no disponible: {e}")
    db = None

# Cache / Fallback en RAM
CATALOGO_CLIENTES: Dict[str, List[Dict[str, Any]]] = {}

def buscar_en_inventario(query: str, cliente_id: str = "default") -> List[Dict[str, Any]]:
    """
    Busca productos/servicios leyendo DIRECTAMENTE de Firestore (colección 'clientes/{cliente_id}/inventario').
    Si Firestore no responde o no está disponible, cae a RAM local.
    """
    query_lower = query.lower()
    resultados = []

    if db:
        try:
            docs = db.collection("clientes").document(cliente_id).collection("inventario").stream()
            for doc in docs:
                item = doc.to_dict()
                item["id"] = doc.id
                nombre = item.get("nombre", "").lower()
                categoria = item.get("categoria", "").lower()
                detalles = item.get("detalles", "").lower()

                if query_lower in nombre or query_lower in categoria or query_lower in detalles:
                    resultados.append(item)

            if resultados:
                return resultados
        except Exception as e:
            logger.error(f"Error consultando inventario en Firestore para {cliente_id}: {e}")

    # Fallback local
    cat_cliente = CATALOGO_CLIENTES.get(cliente_id, [])
    for item in cat_cliente:
        if (query_lower in item.get("nombre", "").lower() or 
            query_lower in item.get("categoria", "").lower() or 
            query_lower in item.get("detalles", "").lower()):
            resultados.append(item)

    return resultados if resultados else cat_cliente

def agendar_cita_demo(nombre: str, telefono: str, fecha: str, hora: str, motivo: str, cliente_id: str = "default") -> Dict[str, Any]:
    """
    Persiste la cita DIRECTAMENTE en Firestore en la subcolección 'clientes/{cliente_id}/citas'.
    """
    cita = {
        "cliente_id": cliente_id,
        "nombre": nombre,
        "telefono": telefono,
        "fecha": fecha,
        "hora": hora,
        "motivo": motivo,
        "creado_el": firestore.SERVER_TIMESTAMP if db else datetime.now().isoformat()
    }

    if db:
        try:
            doc_ref = db.collection("clientes").document(cliente_id).collection("citas").add(cita)
            cita["id"] = doc_ref[1].id
            logger.info(f"[Firestore Cita Persistida] ID: {doc_ref[1].id} para cliente {cliente_id}")
            return cita
        except Exception as e:
            logger.error(f"Error guardando cita en Firestore: {e}")

    cita["id"] = "local_temp_id"
    return cita

def guardar_mensaje_historial(cliente_id: str, remitente: str, role: str, content: str):
    """
    Guarda cada mensaje en el historial conversacional en Firestore ('clientes/{cliente_id}/conversaciones/{remitente}/mensajes').
    """
    if not db:
        return
    try:
        msg_ref = db.collection("clientes").document(cliente_id)\
                    .collection("conversaciones").document(remitente)\
                    .collection("mensajes")
        msg_ref.add({
            "role": role,
            "content": content,
            "timestamp": firestore.SERVER_TIMESTAMP
        })
    except Exception as e:
        logger.error(f"Error guardando historial conversacional en Firestore: {e}")

def obtener_historial_conversacion(cliente_id: str, remitente: str, limite: int = 10) -> List[Dict[str, str]]:
    """
    Obtiene los últimos `limite` mensajes de la conversación entre el usuario y la IA.
    """
    if not db:
        return []
    try:
        docs = db.collection("clientes").document(cliente_id)\
                 .collection("conversaciones").document(remitente)\
                 .collection("mensajes")\
                 .order_by("timestamp", direction=firestore.Query.DESCENDING)\
                 .limit(limite)\
                 .stream()
        
        mensajes = []
        for doc in docs:
            data = doc.to_dict()
            mensajes.append({"role": data.get("role", "user"), "content": data.get("content", "")})
        
        mensajes.reverse() # Reordenar cronológicamente (antiguo -> nuevo)
        return mensajes
    except Exception as e:
        logger.error(f"Error leyendo historial de Firestore: {e}")
        return []

def obtener_citas(cliente_id: str = None) -> List[Dict[str, Any]]:
    """Devuelve las citas registradas en Firestore filtradas por cliente_id."""
    if db:
        try:
            citas = []
            if cliente_id:
                docs = db.collection("clientes").document(cliente_id).collection("citas").stream()
                for doc in docs:
                    d = doc.to_dict()
                    d["id"] = doc.id
                    citas.append(d)
            else:
                cliente_docs = db.collection("clientes").stream()
                for c_doc in cliente_docs:
                    sub_citas = db.collection("clientes").document(c_doc.id).collection("citas").stream()
                    for doc in sub_citas:
                        d = doc.to_dict()
                        d["id"] = doc.id
                        d["cliente_id"] = c_doc.id
                        citas.append(d)
            if citas:
                return citas
        except Exception as e:
            logger.error(f"Error leyendo citas de Firestore: {e}")

    return CITAS_MOCK

