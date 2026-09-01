from typing import List, Dict, Optional, Any
from datetime import datetime

# Catálogo de ejemplo más detallado con campos clave para inmobiliaria y servicios
INVENTARIO_MOCK = [
    {
        "id": "INMO-001",
        "nombre": "Piso céntrico en alquiler",
        "categoria": "Alquiler Inmobiliario",
        "precio": "850 €/mes",
        "ubicacion": "Centro Ciudad, Calle Mayor 12",
        "disponible": True,
        "detalles": "2 habitaciones, 1 baño, amueblado, calefacción central. Se aceptan mascotas pequeñas. Fianza de 1 mes."
    },
    {
        "id": "INMO-002",
        "nombre": "Chalet unifamiliar con piscina en venta",
        "categoria": "Venta Inmobiliaria",
        "precio": "295.000 €",
        "ubicacion": "Urbanización Los Olivos",
        "disponible": True,
        "detalles": "4 habitaciones, 3 baños, jardín de 300m2, garaje para 2 coches, piscina privada. Año construcción 2018."
    },
    {
        "id": "SERV-001",
        "nombre": "Consultoría Comercial e Implementación de IA",
        "categoria": "Servicios Profesionales",
        "precio": "150 €/hora",
        "ubicacion": "Online / Remoto",
        "disponible": True,
        "detalles": "Asesoramiento para implementar agentes de IA en empresas, automatización de ventas por WhatsApp y voz."
    }
]

CITAS_MOCK: List[Dict[str, Any]] = []

def buscar_en_inventario(query: str) -> List[Dict[str, Any]]:
    """Busca productos o servicios por término clave en nombre, categoría o detalles."""
    query_lower = query.lower()
    resultados = []
    for item in INVENTARIO_MOCK:
        if (query_lower in item["nombre"].lower() or 
            query_lower in item["categoria"].lower() or 
            query_lower in item["detalles"].lower() or
            query_lower in item.get("ubicacion", "").lower()):
            resultados.append(item)
    return resultados if resultados else INVENTARIO_MOCK

def agendar_cita_demo(nombre: str, telefono: str, fecha: str, hora: str, motivo: str) -> Dict[str, Any]:
    """Agenda una cita o visita comercial para el cliente."""
    cita = {
        "id": len(CITAS_MOCK) + 1,
        "nombre": nombre,
        "telefono": telefono,
        "fecha": fecha,
        "hora": hora,
        "motivo": motivo,
        "creado_el": datetime.now().isoformat()
    }
    CITAS_MOCK.append(cita)
    return cita
