from typing import List, Dict, Any
import logging
from firebase_admin import firestore

logger = logging.getLogger(__name__)

try:
    import firebase_admin
    db = firestore.client() if firebase_admin._apps else None
except Exception as e:
    db = None

LEADS_MOCK: List[Dict[str, Any]] = []

def registrar_lead(nombre: str, telefono: str, canal: str, interes: str, notas: str = "", cliente_id: str = "default") -> Dict[str, Any]:
    """Registra y persiste un lead en Firestore."""
    lead = {
        "cliente_id": cliente_id,
        "nombre": nombre,
        "telefono": telefono,
        "canal": canal,
        "interes": interes,
        "notas": notas,
        "creado_el": firestore.SERVER_TIMESTAMP if db else None
    }
    
    if db:
        try:
            doc_ref = db.collection("clientes").document(cliente_id).collection("leads").add(lead)
            lead["id"] = doc_ref[1].id
            logger.info(f"[Firestore CRM] Lead guardado ID: {doc_ref[1].id}")
            return lead
        except Exception as e:
            logger.error(f"Error guardando lead en Firestore: {e}")

    LEADS_MOCK.append(lead)
    return lead

def obtener_leads(cliente_id: str = None) -> List[Dict[str, Any]]:
    """Devuelve los leads reales consultados desde Firestore."""
    if db:
        try:
            leads = []
            if cliente_id:
                docs = db.collection("clientes").document(cliente_id).collection("leads").stream()
                for doc in docs:
                    d = doc.to_dict()
                    d["id"] = doc.id
                    leads.append(d)
            else:
                # Consultar en todos los clientes
                cliente_docs = db.collection("clientes").stream()
                for c_doc in cliente_docs:
                    sub_leads = db.collection("clientes").document(c_doc.id).collection("leads").stream()
                    for doc in sub_leads:
                        d = doc.to_dict()
                        d["id"] = doc.id
                        d["cliente_id"] = c_doc.id
                        leads.append(d)
            if leads:
                return leads
        except Exception as e:
            logger.error(f"Error leyendo leads de Firestore: {e}")

    return LEADS_MOCK
