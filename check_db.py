#!/usr/bin/env python3
"""
Database Check Script
Checks the database connection and structure
"""
import sys
from pathlib import Path

# Add the project root to path for imports
sys.path.append(str(Path(__file__).parent))

from backend.models import Base, engine, get_db
from backend.models.host import Host
from backend.models.job import Job
from sqlalchemy import inspect, text

def check_database():
    """Check database connection and structure"""
    print("Checking database connection...")
    
    try:
        # Check if we can connect to the database
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
            
            # Get database info
            print(f"Database URL: {engine.url}")
            
            # Check if tables exist
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            print(f"Tables in database: {tables}")
            
            # Check hosts table
            if "hosts" in tables:
                print("\nHosts table columns:")
                for column in inspector.get_columns("hosts"):
                    print(f"  - {column['name']} ({column['type']})")
                
                # Count hosts
                result = conn.execute(text("SELECT COUNT(*) FROM hosts"))
                count = result.scalar()
                print(f"Number of hosts in database: {count}")
                
                if count > 0:
                    # Show sample host
                    result = conn.execute(text("SELECT * FROM hosts LIMIT 1"))
                    sample = result.fetchone()
                    print("Sample host:")
                    for key, value in sample._mapping.items():
                        print(f"  {key}: {value}")
            else:
                print("❌ Hosts table does not exist")
                
                # Create tables
                print("\nCreating database tables...")
                Base.metadata.create_all(bind=engine)
                print("✅ Database tables created")
    
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    check_database() 