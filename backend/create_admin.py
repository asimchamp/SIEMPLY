#!/usr/bin/env python3
"""
Create an initial admin user for SIEMply
"""
import os
import sys
from pathlib import Path

# Add the project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from backend.models import User, get_db, engine, Base

def create_admin_user(username, email, password, full_name=None):
    """Create an admin user if it doesn't exist"""
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Get database session
    db = next(get_db())
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        print(f"User '{username}' already exists.")
        return
    
    # Create new admin user
    user = User(
        username=username,
        email=email,
        hashed_password=User.get_password_hash(password),
        full_name=full_name,
        role="admin"
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    print(f"Admin user '{username}' created successfully.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create an admin user for SIEMply")
    parser.add_argument("--username", default="admin", help="Admin username")
    parser.add_argument("--email", default="admin@example.com", help="Admin email")
    parser.add_argument("--password", default="admin123", help="Admin password")
    parser.add_argument("--full-name", help="Admin's full name")
    
    args = parser.parse_args()
    
    create_admin_user(args.username, args.email, args.password, args.full_name) 