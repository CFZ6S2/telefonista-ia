import os
import json
from app.database import db

def migrar_datos_a_firestore():
    """
    Migra el catálogo inicial de prueba a las colecciones de Firestore en Firebase.
    """
    if not db:
        print("❌ Error: Firebase Admin SDK no está inicializado.")
        return

    print("🚀 Migrando catálogos a Firebase Firestore...")

    cat_inmo = [
        {
            "nombre": "Piso céntrico en alquiler",
            "categoria": "Alquiler Inmobiliario",
            "precio": "850 €/mes",
            "detalles": "2 habitaciones, 1 baño, amueblado, calefacción central. Se aceptan mascotas pequeñas."
        },
        {
            "nombre": "Chalet unifamiliar con piscina en venta",
            "categoria": "Venta Inmobiliaria",
            "precio": "295.000 €",
            "detalles": "4 habitaciones, 3 baños, jardín de 300m2, garaje para 2 coches, piscina privada."
        }
    ]

    for item in cat_inmo:
        doc_ref = db.collection("clientes").document("cliente_demo_inmo").collection("inventario").add(item)
        print(f"  [+] Inmueble añadido a Firestore ID: {doc_ref[1].id}")

    cat_dental = [
        {
            "nombre": "Limpieza dental ultrasónica + Blanqueamiento",
            "categoria": "Tratamiento Dental",
            "precio": "60 €",
            "detalles": "Limpieza profunda con ultrasonidos para eliminar sarro."
        }
    ]

    for item in cat_dental:
        doc_ref = db.collection("clientes").document("clinica_sonrisas").collection("inventario").add(item)
        print(f"  [+] Servicio Dental añadido a Firestore ID: {doc_ref[1].id}")

    print("✅ Migración completada con éxito.")

if __name__ == "__main__":
    migrar_datos_a_firestore()
