from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database Configuration
    DATABASE_URL: str

    # JWT and Security Configuration
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)

    # Hyperledger Fabric Configuration
    FABRIC_CHANNEL: Optional[str] = Field(default=None)
    FABRIC_CHAINCODE: Optional[str] = Field(default=None)
    FABRIC_PEER_ENDPOINT: Optional[str] = Field(default=None)
    FABRIC_MSP_ID: Optional[str] = Field(default=None)
    FABRIC_IDENTITY: Optional[str] = Field(default=None)

    # Hyperledger Fabric TLS Credentials (file paths only, never embed contents)
    FABRIC_TLS_CA_CERT: Optional[str] = Field(default=None)
    FABRIC_IDENTITY_CERT: Optional[str] = Field(default=None)
    FABRIC_IDENTITY_KEY: Optional[str] = Field(default=None)

settings = Settings()