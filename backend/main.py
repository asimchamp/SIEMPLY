#!/usr/bin/env python3
"""
SIEMply Backend Main Application
FastAPI server for the SIEMply system
"""
import os
import sys
import argparse
import logging
import socket
from pathlib import Path
from typing import List

# Add the project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.config.settings import settings
from backend.models import get_db, Base, engine
from backend.api.hosts import router as hosts_router
from backend.api.jobs import router as jobs_router
from backend.api.auth import router as auth_router
from backend.api.configs import router as configs_router
from backend.api.scheduler import router as scheduler_router
from backend.api.monitoring import router as monitoring_router
from backend.api.splunk import router as splunk_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="SIEMply - SIEM Installation & Management System",
)

# Get server IP address
def get_server_ip():
    try:
        # Get all network interfaces
        hostname = socket.gethostname()
        ip_addresses = socket.gethostbyname_ex(hostname)[2]
        # Filter out localhost
        ip_addresses = [ip for ip in ip_addresses if not ip.startswith("127.")]
        if ip_addresses:
            return ip_addresses[0]
    except Exception as e:
        logger.warning(f"Could not automatically detect server IP: {e}")
    return "localhost"

server_ip = get_server_ip()
logger.info(f"Detected server IP: {server_ip}")

# Configure CORS
# Allow specific origins including localhost and your frontend IP
origins = [
    "http://localhost:8500",
    "http://127.0.0.1:8500",
    f"http://{server_ip}:8500",  # Dynamically detected frontend IP
    "http://192.168.100.45:8500",  # Specific IP from error
    "http://192.168.100.62:8500",  # Additional IP that might be needed
    "*",  # Allow all origins - only use in development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Use the defined origins list instead of "*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
app.include_router(hosts_router)
app.include_router(jobs_router)
app.include_router(auth_router)
app.include_router(configs_router)
app.include_router(scheduler_router)
app.include_router(monitoring_router)
app.include_router(splunk_router)

# Root API route
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to SIEMply API", 
        "version": settings.VERSION,
        "endpoints": {
            "hosts": "/hosts",
            "jobs": "/jobs",
            "health": "/health",
            "auth": "/auth",
            "configs": "/configs",
            "scheduler": "/scheduler",
            "monitoring": "/monitoring",
            "splunk": "/splunk"
        }
    }

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "api_version": settings.VERSION}

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="SIEMply Backend Server")
    parser.add_argument(
        "--port", 
        type=int, 
        default=settings.API_PORT,
        help=f"API server port (default: {settings.API_PORT})"
    )
    parser.add_argument(
        "--host", 
        type=str, 
        default=settings.API_HOST,
        help=f"API server host (default: {settings.API_HOST})"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        default=settings.DEBUG,
        help="Run in debug mode"
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    logger.info(f"Starting {settings.PROJECT_NAME} API on {args.host}:{args.port}")
    
    # Create database tables if they don't exist
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created (if they didn't exist)")
    
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.debug,
        log_level="debug" if args.debug else "info",
    ) 