"""
SIEMply Settings Module
Loads and manages application configuration from environment variables
"""
import os
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import secrets

# Load environment variables from .env file if it exists
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=str(env_path))
else:
    # Try looking in the current directory
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=str(env_path))

# Generate a default secret key if not provided
DEFAULT_SECRET_KEY = secrets.token_hex(32)

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Project info
    PROJECT_NAME: str = Field(default="SIEMply")
    VERSION: str = "0.1.0"
    
    # Database
    DB_TYPE: str = Field(default="sqlite")
    DB_URI: str = Field(default="sqlite:///siemply.db")
    
    # API Server
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=5050)
    DEBUG: bool = Field(default=False)
    
    # Frontend
    UI_PORT: int = Field(default=8500)
    FRONTEND_URL: str = Field(default="http://localhost:8500")
    
    # Authentication
    SECRET_KEY: str = Field(default=DEFAULT_SECRET_KEY)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)
    ALGORITHM: str = Field(default="HS256")
    
    # SSH Configuration
    SSH_DEFAULT_USER: str = Field(default="root")
    SSH_DEFAULT_PORT: int = Field(default=22)
    SSH_KEY_PATH: str = Field(default="~/.ssh/id_rsa")
    SSH_TIMEOUT: int = Field(default=60)
    SSH_RETRIES: int = Field(default=3)
    
    # Cribl Configuration
    CRIBL_API_HOST: Optional[str] = None
    CRIBL_API_PORT: Optional[int] = None
    CRIBL_API_TOKEN: Optional[str] = None
    CRIBL_LEADER_URL: Optional[str] = None
    
    # Splunk Configuration
    SPLUNK_API_HOST: Optional[str] = None
    SPLUNK_API_PORT: Optional[int] = None
    SPLUNK_API_USER: Optional[str] = None
    SPLUNK_API_PASSWORD: Optional[str] = None
    
    # Installer paths
    SPLUNK_INSTALLER_PATH: Optional[str] = None
    CRIBL_INSTALLER_PATH: Optional[str] = None
    
    # Logging configuration
    LOG_LEVEL: str = Field(default="INFO")
    
    # Pydantic v2 configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        env_prefix="SIEMPLY_",
        extra="ignore"
    )


# Create settings instance
settings = Settings()

def get_settings() -> Settings:
    """Factory function to get settings instance"""
    return settings
