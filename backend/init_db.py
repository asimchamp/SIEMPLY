#!/usr/bin/env python3
"""
Database Initialization Script
Creates all database tables defined in models
"""
import sys
import os
import logging
from pathlib import Path

# Add the parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from backend.models import Base, engine, User
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    """Initialize the database by creating all tables"""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully!")
    
    # Create admin user if it doesn't exist
    create_admin_user()

def create_admin_user():
    """Create an admin user if one doesn't exist"""
    # Create a session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if admin user exists
        admin = db.query(User).filter(User.username == "admin").first()
        
        if not admin:
            logger.info("Creating admin user...")
            admin_user = User(
                username="admin",
                email="admin@siemply.local",
                hashed_password=User.get_password_hash("admin"),
                full_name="SIEMply Administrator",
                role="admin",
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            logger.info("Admin user created successfully!")
        else:
            logger.info("Admin user already exists")
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_db() 