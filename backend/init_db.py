#!/usr/bin/env python3
"""
Database initialization script
Creates required database tables and initial admin user
"""
import sys
import logging
from pathlib import Path

# Add the project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from backend.models import Base, engine, User
from backend.config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    """Initialize database with tables and admin user"""
    # Create tables
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Create admin user if it doesn't exist
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if admin user exists
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            logger.info("Creating admin user...")
            admin_user = User(
                username="admin",
                email="admin@siemply.local",
                full_name="SIEMply Admin",
                hashed_password=User.get_password_hash("admin"),
                role="admin"
            )
            db.add(admin_user)
            db.commit()
            logger.info("Admin user created successfully.")
        else:
            logger.info("Admin user already exists.")
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialization complete.") 