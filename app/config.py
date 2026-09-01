import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    OPENAI_API_KEY: str = "tu_clave_de_deepseek"
    OPENAI_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-v4-pro"
    
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
