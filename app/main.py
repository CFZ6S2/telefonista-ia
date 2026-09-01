from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.routers import voice, whatsapp, evolution, admin_clientes
from app.services.crm import obtener_leads

app = FastAPI(
    title="Telefonista IA API",
    description="Backend unificado para llamadas de voz y WhatsApp (Evolution API Gratis & Meta API)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://telefonista-web-app.web.app",
        "https://telefonista-web-app.firebaseapp.com",
        "http://localhost:8000",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

from app.database import obtener_citas

@app.get("/api/v1/leads")
def listar_leads(cliente_id: str = None):
    return {"leads": obtener_leads(cliente_id=cliente_id)}

@app.get("/api/v1/citas")
def listar_citas(cliente_id: str = None):
    return {"citas": obtener_citas(cliente_id=cliente_id)}

if os.path.exists("public"):
    app.mount("/dashboard", StaticFiles(directory="public", html=True), name="dashboard")

