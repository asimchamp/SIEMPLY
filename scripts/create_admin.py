#!/usr/bin/env python3
"""
Create Admin User Script
Creates an admin user for SIEMply
"""
import sys
import os
import logging
from pathlib import Path

# Add the project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models.user import User
from backend.config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

def create_admin_user(username="admin", password="admin123", email="admin@siemply.local"):
    """Create an admin user"""
    try:
        # Create engine with absolute path
        db_uri = settings.DB_URI
        logger.info(f"Using database URI: {db_uri}")
        
        engine = create_engine(db_uri)
        
        # Create session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Check if admin user exists
        admin = db.query(User).filter(User.username == username).first()
        
        if admin:
            logger.info(f"User '{username}' already exists")
            return
        
        # Create admin user
        logger.info(f"Creating admin user '{username}'...")
        admin_user = User(
            username=username,
            email=email,
            hashed_password=User.get_password_hash(password),
            full_name="SIEMply Administrator",
            role="admin",
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        logger.info(f"Admin user '{username}' created successfully!")
        
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        return False
    finally:
        db.close()
    
    return True

def main():
    """Main function"""
    logger.info("======================================")
    logger.info("  SIEMply Admin User Creation        ")
    logger.info("======================================")
    
    # Get username and password from command line arguments
    username = "admin"
    password = "admin123"
    email = "admin@siemply.local"
    
    if len(sys.argv) > 1:
        username = sys.argv[1]
    if len(sys.argv) > 2:
        password = sys.argv[2]
    if len(sys.argv) > 3:
        email = sys.argv[3]
    
    # Create admin user
    success = create_admin_user(username, password, email)
    
    if success:
        logger.info("\n======================================")
        logger.info("      Admin User Created!           ")
        logger.info("======================================")
        logger.info(f"\nUsername: {username}")
        logger.info(f"Password: {password}")
        logger.info("\nYou can now log in with these credentials.")
    else:
        logger.error("\n======================================")
        logger.error("      Admin User Creation Failed!   ")
        logger.error("======================================")

if __name__ == "__main__":
    main() 