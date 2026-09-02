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

from fastapi import HTTPException
import firebase_admin.auth as firebase_auth

def verificar_cliente(cliente_id: str, pin: str = None, token: str = None):
    from app.database import _get_db
    db = _get_db()
    if not db: raise HTTPException(status_code=503, detail="BD no disponible")
    doc = db.collection("clientes").document(cliente_id).get()
    if not doc.exists: raise HTTPException(status_code=404, detail="Cliente no encontrado")
    data = doc.to_dict()

    if token:
        try:
            decoded = firebase_auth.verify_id_token(token)
            email = decoded.get("email", "").lower().strip()
            if email and email == data.get("email", "").lower().strip():
                return True
        except Exception:
            pass
        raise HTTPException(status_code=401, detail="Token no válido")

    if pin and data.get("pin_acceso") == pin:
        return True

    raise HTTPException(status_code=401, detail="Acceso no autorizado")

@app.get("/api/v1/client/leads/{cliente_id}")
def listar_leads_cliente(cliente_id: str, pin: str = None, token: str = None):
    verificar_cliente(cliente_id, pin=pin, token=token)
    return {"leads": obtener_leads(cliente_id=cliente_id)}

@app.get("/api/v1/client/citas/{cliente_id}")
def listar_citas_cliente(cliente_id: str, pin: str = None, token: str = None):
    verificar_cliente(cliente_id, pin=pin, token=token)
    from app.database import obtener_citas
    return {"citas": obtener_citas(cliente_id=cliente_id)}

@app.get("/api/v1/client/conversaciones/{cliente_id}")
def listar_conversaciones_cliente(cliente_id: str, pin: str = None, token: str = None):
    verificar_cliente(cliente_id, pin=pin, token=token)
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

@app.get("/api/v1/client/whatsapp/status/{cliente_id}")
async def get_whatsapp_status(cliente_id: str, pin: str = None, token: str = None):
    verificar_cliente(cliente_id, pin=pin, token=token)
    from app.services.evolution_manager import obtener_estado_instancia_evolution, obtener_qr_instancia_evolution
    estado = await obtener_estado_instancia_evolution(cliente_id)
    state_str = estado.get("instance", {}).get("state", "unknown")
    
    if state_str in ["open"]:
        return {"status": "connected", "state": state_str}
    
    # If not connected, get QR code
    qr_data = await obtener_qr_instancia_evolution(cliente_id)
    base64_qr = qr_data.get("qrcode", {}).get("base64", "") if "qrcode" in qr_data else qr_data.get("base64", "")
    
    return {
        "status": "disconnected",
        "state": state_str,
        "qr_base64": base64_qr
    }

@app.get("/api/v1/client/conversaciones/{cliente_id}/{remitente}")
def obtener_mensajes_conversacion_cliente(cliente_id: str, remitente: str, pin: str = None, token: str = None, limite: int = 50):
    verificar_cliente(cliente_id, pin=pin, token=token)
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
