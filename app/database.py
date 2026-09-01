import os
import json
import logging
from typing import List, Dict, Any
import firebase_admin
from firebase_admin import credentials, firestore

logger = logging.getLogger(__name__)

# Inicializar Firebase Admin SDK si no se ha inicializado
if not firebase_admin._apps:
    try:
        # Intentar cargar credenciales desde variable o archivo de servicio
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        else:
            # Inicialización por defecto en Google Cloud / Firebase Cloud Functions
            firebase_admin.initialize_app()
    except Exception as e:
        logger.warning(f"Firebase no inicializado con credenciales explícitas: {e}")

db = firestore.client() if firebase_admin._apps else None

# Datos de respaldo por si no hay conexión a Firestore temporalmente
CATALOGO_MOCK_FALLBACK = {
    "cliente_demo_inmo": [
        {
            "id": "INMO-001",
            "nombre": "Piso céntrico en alquiler",
            "categoria": "Alquiler Inmobiliario",
            "precio": "850 €/mes",
            "detalles": "2 habitaciones, 1 baño, amueblado, calefacción central."
        }
    ]
}

def buscar_en_inventario(query: str, cliente_id: str = "cliente_demo_inmo") -> List[Dict[str, Any]]:
    """
    Busca productos/servicios en Firestore (Firebase).
    Si Firestore no está configurado o falla, usa el fallback local.
    """
    query_lower = query.lower()
    resultados = []

    if db:
        try:
            # Consultar la colección 'clientes/{cliente_id}/inventario'
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
            logger.error(f"Error consultando Firestore para {cliente_id}: {e}")

    # Fallback si falla la BD
    cat_cliente = CATALOGO_MOCK_FALLBACK.get(cliente_id, CATALOGO_MOCK_FALLBACK["cliente_demo_inmo"])
    return cat_cliente

def agendar_cita_demo(nombre: str, telefono: str, fecha: str, hora: str, motivo: str, cliente_id: str = "default") -> Dict[str, Any]:
    """
    Guarda la cita en Firestore (Firebase) de forma persistente.
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
            logger.info(f"[Firebase Firestore] Cita guardada con éxito: {doc_ref[1].id}")
            return cita
        except Exception as e:
            logger.error(f"Error guardando cita en Firestore: {e}")

    cita["id"] = "local_temp_id"
    return cita
