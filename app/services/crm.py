from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

def _get_db():
    from app.database import _get_db as get_db
    return get_db()

def _server_timestamp():
    from app.database import _server_timestamp as st
    return st()

def registrar_lead(nombre: str, telefono: str, canal: str, interes: str, notas: str = "", cliente_id: str = "default") -> Dict[str, Any]:
    db = _get_db()
    lead = {
        "cliente_id": cliente_id,
        "nombre": nombre,
        "telefono": telefono,
        "canal": canal,
        "interes": interes,
        "notas": notas,
        "creado_el": _server_timestamp()
    }

    if not db:
        logger.error("No se pudo registrar lead: Firestore no disponible.")
        return {**lead, "id": "error_no_db"}

    try:
        doc_ref = db.collection("clientes").document(cliente_id).collection("leads").add(lead)
        lead["id"] = doc_ref[1].id
        logger.info(f"[Firestore CRM] Lead guardado ID: {doc_ref[1].id}")
        return lead
    except Exception as e:
        logger.error(f"Error guardando lead en Firestore: {e}")
        return {**lead, "id": "error"}

def obtener_leads(cliente_id: str = None) -> List[Dict[str, Any]]:
    db = _get_db()
    if not db:
        return []
    try:
        leads = []
        if cliente_id:
            docs = db.collection("clientes").document(cliente_id).collection("leads").stream()
            for doc in docs:
                d = doc.to_dict()
                d["id"] = doc.id
                leads.append(d)
        else:
            cliente_docs = db.collection("clientes").stream()
            for c_doc in cliente_docs:
                sub_leads = db.collection("clientes").document(c_doc.id).collection("leads").stream()
                for doc in sub_leads:
                    d = doc.to_dict()
                    d["id"] = doc.id
                    d["cliente_id"] = c_doc.id
                    leads.append(d)
        return leads
    except Exception as e:
        logger.error(f"Error leyendo leads de Firestore: {e}")
        return []
