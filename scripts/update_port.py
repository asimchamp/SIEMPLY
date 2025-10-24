#!/usr/bin/env python3
"""
Update Port Configuration Script
This script updates the port configuration in the SIEMply application
"""
import os
import sys
import logging
from pathlib import Path

# Add the project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from backend.config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

def update_env_file():
    """Update the .env file with the new port configuration"""
    env_path = Path(__file__).parent.parent / '.env'
    
    if not env_path.exists():
        logger.error("❌ .env file not found")
        return False
    
    logger.info("Updating .env file...")
    
    # Read the current content
    with open(env_path, 'r') as f:
        content = f.read()
    
    # Update the API port
    if 'SIEMPLY_API_PORT=5050' in content:
        content = content.replace('SIEMPLY_API_PORT=5050', 'SIEMPLY_API_PORT=5050')
        logger.info("✅ Updated API port in .env file")
    else:
        logger.info("ℹ️ API port already updated in .env file")
    
    # Write the updated content
    with open(env_path, 'w') as f:
        f.write(content)
    
    return True

def main():
    """Main function"""
    logger.info("======================================")
    logger.info("  SIEMply Port Configuration Update  ")
    logger.info("======================================")
    
    # Update .env file
    update_env_file()
    
    logger.info("\n======================================")
    logger.info("      Port Update Complete!          ")
    logger.info("======================================")
    logger.info("\nThe backend API now uses port 5050 instead of 5050.")
    logger.info("Please restart the application for changes to take effect.")
    logger.info("\nTo restart:")
    logger.info("  systemctl restart siemply")
    logger.info("  or")
    logger.info("  ./start.sh")

if __name__ == "__main__":
    main() 