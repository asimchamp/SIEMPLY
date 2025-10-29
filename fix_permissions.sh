#!/bin/bash

# Fix file permissions for SIEMply
# Run this if you get "unable to open database file" errors

# Text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  SIEMply Permission Fix             ${NC}"
echo -e "${BLUE}======================================${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "\n${YELLOW}Current permissions:${NC}"
ls -la backend/siemply.db 2>/dev/null || echo "Database file not found"
ls -ld backend/ 2>/dev/null || echo "Backend directory not found"

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    IS_ROOT=true
    TARGET_USER="${SUDO_USER:-root}"
    
    if [ "$TARGET_USER" = "root" ]; then
        echo -e "\n${YELLOW}Running as root user.${NC}"
        echo -e "${YELLOW}Making files world-accessible...${NC}"
        
        chmod 666 backend/siemply.db 2>/dev/null || true
        chmod -R 777 backend/ 2>/dev/null || true
        chmod -R 777 logs/ 2>/dev/null || true
        chmod -R 777 playbooks/ 2>/dev/null || true
        
        echo -e "${GREEN}✓ Files set to world-accessible${NC}"
        echo -e "${YELLOW}⚠ Warning: This is not secure for production!${NC}"
    else
        echo -e "\n${YELLOW}Setting ownership to: $TARGET_USER${NC}"
        
        chown -R $TARGET_USER:$TARGET_USER backend/ 2>/dev/null || true
        chown -R $TARGET_USER:$TARGET_USER logs/ 2>/dev/null || true
        chown -R $TARGET_USER:$TARGET_USER playbooks/ 2>/dev/null || true
        chown -R $TARGET_USER:$TARGET_USER venv/ 2>/dev/null || true
        
        chmod 664 backend/siemply.db 2>/dev/null || true
        chmod 775 backend/ 2>/dev/null || true
        chmod 775 logs/ 2>/dev/null || true
        
        echo -e "${GREEN}✓ Ownership set to $TARGET_USER${NC}"
    fi
else
    echo -e "\n${YELLOW}Running as non-root user.${NC}"
    echo -e "${YELLOW}Setting file permissions...${NC}"
    
    chmod 664 backend/siemply.db 2>/dev/null || true
    chmod -R 775 backend/ 2>/dev/null || true
    chmod -R 775 logs/ 2>/dev/null || true
    
    echo -e "${GREEN}✓ Permissions updated${NC}"
fi

echo -e "\n${YELLOW}New permissions:${NC}"
ls -la backend/siemply.db 2>/dev/null
ls -ld backend/

# Verify database is accessible
echo -e "\n${YELLOW}Testing database access...${NC}"
if sqlite3 backend/siemply.db "SELECT 1;" &>/dev/null; then
    echo -e "${GREEN}✓ Database is accessible${NC}"
else
    echo -e "${RED}✗ Database still not accessible${NC}"
    echo -e "${YELLOW}Try running with sudo: sudo ./fix_permissions.sh${NC}"
fi

echo -e "\n${GREEN}======================================${NC}"
echo -e "${GREEN}  Permission Fix Complete!           ${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e "\nYou can now try starting the application again."
