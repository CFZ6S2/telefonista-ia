from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Lista de leads real (Vacía por defecto)
LEADS_MOCK: List[Dict[str, Any]] = []

def registrar_lead(nombre: str, telefono: str, canal: str, interes: str, notas: str = "") -> Dict[str, Any]:
    """Registra un nuevo contacto en el sistema."""
    lead = {
        "id": len(LEADS_MOCK) + 1,
        "nombre": nombre,
        "telefono": telefono,
        "canal": canal,
        "interes": interes,
        "notas": notas
    }
    LEADS_MOCK.append(lead)
    logger.info(f"[CRM] Lead registrado: {lead}")
    return lead

def obtener_leads() -> List[Dict[str, Any]]:
    """Devuelve la lista real de leads registrados."""
    return LEADS_MOCK
