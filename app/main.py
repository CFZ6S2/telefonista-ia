from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
from app.routers import voice, whatsapp, evolution, admin_clientes
from app.services.crm import obtener_leads

app = FastAPI(
    title="Telefonista IA API",
    description="Backend unificado para llamadas de voz y WhatsApp (Evolution API Gratis & Meta API)",
    version="1.0.0"
)

# Registrar routers de la API
app.include_router(voice.router, prefix="/api/v1/voice", tags=["Voice Assistant"])
app.include_router(whatsapp.router, prefix="/api/v1/whatsapp", tags=["WhatsApp Meta API"])
app.include_router(evolution.router, prefix="/api/v1/whatsapp", tags=["WhatsApp Evolution API Gratis"])
app.include_router(admin_clientes.router, prefix="/api/v1/admin", tags=["Gestión de Clientes"])

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Telefonista IA operativa y escuchando.",
        "dashboard": "/dashboard",
        "documentation": "/docs"
    }

@app.get("/api/v1/leads")
def listar_leads():
    return {"leads": obtener_leads()}

if os.path.exists("public"):
    app.mount("/dashboard", StaticFiles(directory="public", html=True), name="dashboard")
