import logging
logging.basicConfig(level=logging.INFO)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.routers import voice, whatsapp, evolution, admin_clientes, onboarding
from app.services.crm import obtener_leads

app = FastAPI(
    title="Telefonista IA API",
    description="Backend unificado para llamadas de voz y WhatsApp (Evolution API Gratis & Meta API)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers de la API
app.include_router(voice.router, prefix="/api/v1/voice", tags=["Voice Assistant"])
app.include_router(whatsapp.router, prefix="/api/v1/whatsapp", tags=["WhatsApp Meta API"])
app.include_router(evolution.router, prefix="/api/v1/whatsapp", tags=["WhatsApp Evolution API Gratis"])
app.include_router(admin_clientes.router, prefix="/api/v1/admin", tags=["Gestión de Clientes"])
app.include_router(onboarding.router, prefix="/api/v1/onboarding", tags=["Onboarding Self-Service"])

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Telefonista IA operativa y escuchando.",
        "dashboard": "/dashboard",
        "documentation": "/docs"
    }

from app.database import obtener_citas
from fastapi import Depends
from app.routers.admin_clientes import verificar_admin_api_key

@app.get("/api/v1/leads", dependencies=[Depends(verificar_admin_api_key)])
def listar_leads(cliente_id: str = None):
    return {"leads": obtener_leads(cliente_id=cliente_id)}

@app.get("/api/v1/citas", dependencies=[Depends(verificar_admin_api_key)])
def listar_citas(cliente_id: str = None):
    return {"citas": obtener_citas(cliente_id=cliente_id)}

# Client-facing endpoints (No Admin Key required)
@app.get("/api/v1/client/leads/{cliente_id}")
def listar_leads_cliente(cliente_id: str):
    return {"leads": obtener_leads(cliente_id=cliente_id)}

@app.get("/api/v1/client/citas/{cliente_id}")
def listar_citas_cliente(cliente_id: str):
    from app.services.crm import obtener_citas
    return {"citas": obtener_citas(cliente_id=cliente_id)}

@app.get("/api/v1/client/conversaciones/{cliente_id}")
def listar_conversaciones_cliente(cliente_id: str):
    from app.database import _get_db, _firestore_direction
    db = _get_db()
    if not db: return {"conversaciones": []}
    try:
        convs_ref = db.collection("clientes").document(cliente_id).collection("conversaciones")
        contactos = []
        for doc in convs_ref.stream():
            last_msg = None
            msgs = doc.reference.collection("mensajes").order_by("timestamp", direction=_firestore_direction()).limit(1).stream()
            for m in msgs: last_msg = m.to_dict()
            contactos.append({
                "remitente": doc.id,
                "ultimo_mensaje": last_msg.get("content", "") if last_msg else "",
                "ultimo_role": last_msg.get("role", "") if last_msg else "",
                "timestamp": str(last_msg.get("timestamp", "")) if last_msg else ""
            })
        contactos.sort(key=lambda x: x["timestamp"], reverse=True)
        return {"conversaciones": contactos}
    except Exception:
        return {"conversaciones": []}

@app.get("/api/v1/client/conversaciones/{cliente_id}/{remitente}")
def obtener_mensajes_conversacion_cliente(cliente_id: str, remitente: str, limite: int = 50):
    from app.database import _get_db
    db = _get_db()
    if not db: return {"mensajes": []}
    try:
        msgs_ref = db.collection("clientes").document(cliente_id).collection("conversaciones").document(remitente).collection("mensajes").order_by("timestamp").limit(limite)
        mensajes = [{"role": doc.to_dict().get("role", "user"), "content": doc.to_dict().get("content", ""), "timestamp": str(doc.to_dict().get("timestamp", ""))} for doc in msgs_ref.stream()]
        return {"mensajes": mensajes, "remitente": remitente, "cliente_id": cliente_id}
    except Exception:
        return {"mensajes": []}

if os.path.exists("public"):
    app.mount("/dashboard", StaticFiles(directory="public", html=True), name="dashboard")
