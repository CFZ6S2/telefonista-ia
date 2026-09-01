from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

_db = None
_db_initialized = False
_firestore_mod = None

def _get_db():
    global _db, _db_initialized, _firestore_mod
    if _db_initialized:
        return _db
    _db_initialized = True
    try:
        import firebase_admin
        from firebase_admin import credentials as fb_credentials
        if not firebase_admin._apps:
            import os
            cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            if cred_path and os.path.exists(cred_path):
                cred = fb_credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                logger.info(f"Firebase Admin SDK inicializado con credenciales: {cred_path}")
            else:
                try:
                    firebase_admin.initialize_app()
                    logger.info("Firebase Admin SDK inicializado con Application Default Credentials.")
                except Exception:
                    logger.error("Firebase Admin SDK no pudo inicializarse. Sin credenciales disponibles.")
                    return _db
        from firebase_admin import firestore as fs
        _firestore_mod = fs
        _db = fs.client()
        logger.info("Firestore Client conectado correctamente.")
    except Exception as e:
        logger.error(f"Firestore Client no disponible: {e}")
    return _db

def _server_timestamp():
    if _firestore_mod:
        return _firestore_mod.SERVER_TIMESTAMP
    return datetime.now().isoformat()

def buscar_en_inventario(query: str, cliente_id: str = "default") -> List[Dict[str, Any]]:
    db = _get_db()
    if not db:
        return []

    query_lower = query.lower()
    resultados = []
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

        return resultados
    except Exception as e:
        logger.error(f"Error consultando inventario en Firestore para {cliente_id}: {e}")
        return []

def agendar_cita(nombre: str, telefono: str, fecha: str, hora: str, motivo: str, cliente_id: str = "default") -> Dict[str, Any]:
    db = _get_db()
    cita = {
        "cliente_id": cliente_id,
        "nombre": nombre,
        "telefono": telefono,
        "fecha": fecha,
        "hora": hora,
        "motivo": motivo,
        "creado_el": _server_timestamp()
    }

    if not db:
        logger.error("No se pudo agendar cita: Firestore no disponible.")
        return {**cita, "id": "error_no_db"}

    try:
        doc_ref = db.collection("clientes").document(cliente_id).collection("citas").add(cita)
        cita["id"] = doc_ref[1].id
        logger.info(f"[Firestore] Cita persistida ID: {doc_ref[1].id} para cliente {cliente_id}")
        return cita
    except Exception as e:
        logger.error(f"Error guardando cita en Firestore: {e}")
        return {**cita, "id": "error"}

def guardar_mensaje_historial(cliente_id: str, remitente: str, role: str, content: str):
    db = _get_db()
    if not db:
        return
    try:
        msg_ref = db.collection("clientes").document(cliente_id)\
                    .collection("conversaciones").document(remitente)\
                    .collection("mensajes")
        msg_ref.add({
            "role": role,
            "content": content,
            "timestamp": _server_timestamp()
        })
    except Exception as e:
        logger.error(f"Error guardando historial conversacional en Firestore: {e}")

def obtener_historial_conversacion(cliente_id: str, remitente: str, limite: int = 10) -> List[Dict[str, str]]:
    db = _get_db()
    if not db:
        return []
    try:
        docs = db.collection("clientes").document(cliente_id)\
                 .collection("conversaciones").document(remitente)\
                 .collection("mensajes")\
                 .order_by("timestamp", direction=_firestore_mod.Query.DESCENDING)\
                 .limit(limite)\
                 .stream()

        mensajes = []
        for doc in docs:
            data = doc.to_dict()
            mensajes.append({"role": data.get("role", "user"), "content": data.get("content", "")})

        mensajes.reverse()
        return mensajes
    except Exception as e:
        logger.error(f"Error leyendo historial de Firestore: {e}")
        return []

def obtener_citas(cliente_id: str = None) -> List[Dict[str, Any]]:
    db = _get_db()
    if not db:
        return []
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
        return citas
    except Exception as e:
        logger.error(f"Error leyendo citas de Firestore: {e}")
        return []
