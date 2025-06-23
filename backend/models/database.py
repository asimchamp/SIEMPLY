"""
SIEMply Database Module
Sets up SQLAlchemy database connection and session management
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from backend.config.settings import settings

# Create engine based on settings
if settings.DB_TYPE == "sqlite":
    SQLALCHEMY_DATABASE_URL = settings.DB_URI
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:  # PostgreSQL
    SQLALCHEMY_DATABASE_URL = settings.DB_URI
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 