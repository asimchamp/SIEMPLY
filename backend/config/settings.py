"""
SIEMply Settings Module
Loads and manages application configuration from environment variables
"""
import os
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, Field

# Load environment variables from .env file if it exists
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=str(env_path))

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Project info
    PROJECT_NAME: str = "SIEMply"
    VERSION: str = "0.1.0"
    
    # Database
    DB_TYPE: str = Field(default="sqlite", env="SIEMPLY_DB_TYPE")
    DB_URI: str = Field(default="sqlite:///siemply.db", env="SIEMPLY_DB_URI")
    
    # API Server
    API_HOST: str = Field(default="0.0.0.0", env="SIEMPLY_API_HOST")
    API_PORT: int = Field(default=5000, env="SIEMPLY_API_PORT")
    DEBUG: bool = Field(default=False, env="SIEMPLY_DEBUG")
    
    # Frontend
    UI_PORT: int = Field(default=8500, env="SIEMPLY_UI_PORT")
    
    # Authentication
    SECRET_KEY: str = Field(..., env="SIEMPLY_SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, env="SIEMPLY_TOKEN_EXPIRE_MINUTES")
    
    # SSH Configuration
    SSH_DEFAULT_USER: str = Field(default="admin", env="SSH_DEFAULT_USER")
    SSH_DEFAULT_PORT: int = Field(default=22, env="SSH_DEFAULT_PORT")
    SSH_KEY_PATH: str = Field(default="~/.ssh/id_rsa", env="SSH_KEY_PATH")
    SSH_TIMEOUT: int = Field(default=60, env="SIEMPLY_SSH_TIMEOUT")
    SSH_RETRIES: int = Field(default=3, env="SSH_RETRIES")
    
    # Cribl Configuration
    CRIBL_API_TOKEN: Optional[str] = Field(default=None, env="CRIBL_API_TOKEN")
    CRIBL_LEADER_URL: Optional[str] = Field(default=None, env="CRIBL_LEADER_URL")
    
    # Splunk Configuration
    SPLUNK_API_URL: Optional[str] = Field(default=None, env="SPLUNK_API_URL")
    SPLUNK_API_USER: Optional[str] = Field(default=None, env="SPLUNK_API_USER")
    SPLUNK_API_PASSWORD: Optional[str] = Field(default=None, env="SPLUNK_API_PASSWORD")
    
    # Installer paths
    SPLUNK_INSTALLER_PATH: Optional[str] = Field(default=None, env="SIEMPLY_SPLUNK_INSTALLER_PATH")
    CRIBL_INSTALLER_PATH: Optional[str] = Field(default=None, env="SIEMPLY_CRIBL_INSTALLER_PATH")
    
    # Logging configuration
    LOG_LEVEL: str = Field(default="INFO", env="SIEMPLY_LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create settings instance
settings = Settings()

def get_settings() -> Settings:
    """Factory function to get settings instance"""
    return settings 