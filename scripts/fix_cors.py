#!/usr/bin/env python3
"""
Fix CORS Configuration Script
This script updates the CORS configuration in the main.py file
"""
import sys
import os
import logging
import re
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

def update_cors_config():
    """Update the CORS configuration in main.py"""
    # Get script directory
    script_dir = Path(__file__).parent.parent
    main_py_path = script_dir / "backend" / "main.py"
    
    if not main_py_path.exists():
        logger.error(f"❌ main.py not found at {main_py_path}")
        return False
    
    logger.info(f"Updating CORS configuration in {main_py_path}...")
    
    # Read the current content
    with open(main_py_path, 'r') as f:
        content = f.read()
    
    # Create backup of original file
    backup_path = main_py_path.with_suffix('.py.bak')
    with open(backup_path, 'w') as f:
        f.write(content)
    
    logger.info(f"✅ Created backup at {backup_path}")
    
    # Find the CORS middleware section
    cors_pattern = r"app\.add_middleware\(\s*CORSMiddleware,\s*allow_origins=.*?\)"
    
    # Replace with new configuration
    new_cors_config = """app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now to troubleshoot
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)"""
    
    # Use regex to replace the CORS middleware section
    updated_content = re.sub(cors_pattern, new_cors_config, content, flags=re.DOTALL)
    
    # Write the updated content
    with open(main_py_path, 'w') as f:
        f.write(updated_content)
    
    logger.info(f"✅ Updated CORS configuration in {main_py_path}")
    return True

def main():
    """Main function"""
    logger.info("======================================")
    logger.info("  SIEMply CORS Configuration Fix     ")
    logger.info("======================================")
    
    # Update CORS configuration
    success = update_cors_config()
    
    if success:
        logger.info("\n======================================")
        logger.info("      CORS Fix Complete!             ")
        logger.info("======================================")
        logger.info("\nYou need to restart the backend for changes to take effect:")
        logger.info("  systemctl restart siemply")
        logger.info("  or")
        logger.info("  ./start_backend.sh")
    else:
        logger.error("\n======================================")
        logger.error("      CORS Fix Failed!              ")
        logger.error("======================================")

if __name__ == "__main__":
    main() 