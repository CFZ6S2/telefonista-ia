import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    
    EVOLUTION_API_KEY: str = ""
    EVOLUTION_API_BASE: str = "http://172.17.0.1:8082"
    VPS_PUBLIC_URL: str = "http://telefonista-api.duckdns.org"
    VAPI_API_KEY: str = ""
    ADMIN_SECRET_KEY: str = ""
    ADMIN_EMAILS: str = "cesar.herrera.rojo@gmail.com"
    WEBHOOK_SECRET: str = "t3l3f0n1st4_s3cr3t_2026"

    WHATSAPP_TOKEN: str = "tu_token_de_meta_whatsapp"
    WHATSAPP_PHONE_NUMBER_ID: str = "tu_phone_number_id_de_meta"
    VERIFY_TOKEN: str = "mi_token_de_verificacion_seguro"
    DATABASE_URL: str = "sqlite:///./telefonista_ia.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
