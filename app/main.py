from fastapi import FastAPI
from app.routers import voice, whatsapp, evolution
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

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Telefonista IA operativa y escuchando.",
        "documentation": "/docs"
    }

@app.get("/api/v1/leads")
def listar_leads():
    return {"leads": obtener_leads()}
