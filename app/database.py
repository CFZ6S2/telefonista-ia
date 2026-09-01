from typing import List, Dict, Optional, Any
from datetime import datetime

# Catálogo Multi-Cliente (Indexado por cliente_id / tenant_id)
CATALOGO_CLIENTES = {
    "cliente_demo_inmo": [
        {
            "id": "INMO-001",
            "nombre": "Piso céntrico en alquiler",
            "categoria": "Alquiler Inmobiliario",
            "precio": "850 €/mes",
            "ubicacion": "Centro Ciudad, Calle Mayor 12",
            "disponible": True,
            "detalles": "2 habitaciones, 1 baño, amueblado, calefacción central."
        }
    ],
    "clinica_sonrisas": [
        {
            "id": "DENT-001",
            "nombre": "Limpieza dental ultrasónica + Blanqueamiento",
            "categoria": "Tratamiento Dental",
            "precio": "60 €",
            "ubicacion": "Plaza España 4",
            "disponible": True,
            "detalles": "Limpieza profunda con ultrasonidos para eliminar sarro y manchas."
        },
        {
            "id": "DENT-002",
            "nombre": "Ortodoncia Invisible (Invisalign)",
            "categoria": "Tratamiento Dental",
            "precio": "Desde 1.900 €",
            "ubicacion": "Plaza España 4",
            "disponible": True,
            "detalles": "Férulas transparentes extraíbles. Consulta de valoración gratuita."
        }
    ]
}

CITAS_MOCK: List[Dict[str, Any]] = []

def buscar_en_inventario(query: str, cliente_id: str = "cliente_demo_inmo") -> List[Dict[str, Any]]:
    """Busca productos/servicios en el catálogo específico de un cliente/empresa."""
    cat_cliente = CATALOGO_CLIENTES.get(cliente_id, CATALOGO_CLIENTES["cliente_demo_inmo"])
    query_lower = query.lower()
    resultados = []
    for item in cat_cliente:
        if (query_lower in item["nombre"].lower() or 
            query_lower in item["categoria"].lower() or 
            query_lower in item["detalles"].lower()):
            resultados.append(item)
    return resultados if resultados else cat_cliente

def agendar_cita_demo(nombre: str, telefono: str, fecha: str, hora: str, motivo: str, cliente_id: str = "default") -> Dict[str, Any]:
    """Agenda cita asignada al cliente/empresa correspondiente."""
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
