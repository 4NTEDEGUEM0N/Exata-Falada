from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    SECRET_KEY: str
    DATABASE_URL: str
    ADMIN_USER: str
    ADMIN_PASSWORD: str
    
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 
    ALGORITHM: str = "HS256"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
""""""

"""
from typing import Literal
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # O tipo Literal força o usuário a digitar exatamente "aws" ou "oracle" no .env
    storage_provider: Literal["aws", "oracle"]
    
    # === Credenciais AWS S3 (Opcionais) ===
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_bucket_name: str | None = None

    # === Credenciais Oracle OCI (Opcionais) ===
    oci_user: str | None = None
    oci_fingerprint: str | None = None
    oci_tenancy: str | None = None
    oci_region: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # A mágica acontece aqui: O Pydantic roda essa função após ler o .env
    @model_validator(mode='after')
    def check_storage_credentials(self):
        # Se escolheu AWS, obriga a ter as chaves da AWS
        if self.storage_provider == "aws":
            if not all([self.aws_access_key_id, self.aws_secret_access_key, self.aws_bucket_name]):
                raise ValueError("Você escolheu 'aws' como storage_provider, mas faltam credenciais da AWS no .env!")
        
        # Se escolheu Oracle, obriga a ter as chaves da Oracle
        elif self.storage_provider == "oracle":
            if not all([self.oci_user, self.oci_fingerprint, self.oci_tenancy, self.oci_region]):
                raise ValueError("Você escolheu 'oracle' como storage_provider, mas faltam credenciais do OCI no .env!")
        
        return self

settings = Settings()
"""