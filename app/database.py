from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Diccionario dinámico de catálogos en memoria (Vacío por defecto, sin Mocks)
CATALOGO_CLIENTES: Dict[str, List[Dict[str, Any]]] = {}

# Lista dinámica de citas registradas
CITAS_MOCK: List[Dict[str, Any]] = []

def buscar_en_inventario(query: str, cliente_id: str = "default") -> List[Dict[str, Any]]:
    """Busca productos/servicios en el catálogo real del cliente."""
    cat_cliente = CATALOGO_CLIENTES.get(cliente_id, [])
    query_lower = query.lower()
    resultados = []
    
    for item in cat_cliente:
        if (query_lower in item.get("nombre", "").lower() or 
            query_lower in item.get("categoria", "").lower() or 
            query_lower in item.get("detalles", "").lower()):
            resultados.append(item)

    return resultados if resultados else cat_cliente

def agendar_cita_demo(nombre: str, telefono: str, fecha: str, hora: str, motivo: str, cliente_id: str = "default") -> Dict[str, Any]:
    """Agenda una cita comercial vinculada al cliente."""
    cita = {
        "id": len(CITAS_MOCK) + 1,
        "cliente_id": cliente_id,
        "nombre": nombre,
        "telefono": telefono,
        "fecha": fecha,
        "hora": hora,
        "motivo": motivo,
        "creado_el": datetime.now().isoformat()
    }
    CITAS_MOCK.append(cita)
    return cita
