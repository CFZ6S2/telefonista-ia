from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# En memoria para demostración inicial
LEADS_MOCK: List[Dict[str, Any]] = []

def registrar_lead(nombre: str, telefono: str, canal: str, interes: str, notas: str = "") -> Dict[str, Any]:
    """Registra un nuevo contacto interesando en el servicio/producto."""
    lead = {
        "id": len(LEADS_MOCK) + 1,
        "nombre": nombre,
        "telefono": telefono,
        "canal": canal,  # 'whatsapp' o 'voz'
        "interes": interes,
        "notas": notas
    }
    LEADS_MOCK.append(lead)
    logger.info(f"[CRM] Lead registrado exitosamente: {lead}")
    return lead

def obtener_leads() -> List[Dict[str, Any]]:
    """Obtiene la lista de todos los leads registrados."""
    return LEADS_MOCK
