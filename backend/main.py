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
from datetime import datetime

# Add the project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import asyncio

from backend.config.settings import settings
from backend.models import get_db, Base, engine
from backend.api.hosts import router as hosts_router
from backend.api.jobs import router as jobs_router
from backend.api.auth import router as auth_router
from backend.api.configs import router as configs_router
from backend.api.scheduler import router as scheduler_router
from backend.api.monitoring import router as monitoring_router
from backend.api.splunk import router as splunk_router
from backend.api.packages import router as packages_router
from backend.api.users import router as users_router
from backend.api.serverclass import router as serverclass_router
from backend.api.files import router as files_router
from backend.api.ssh import router as ssh_router

from backend.api.playbooks import router as playbooks_router
from backend.api.executions import router as executions_router

# Splunk ACS API
from backend.splunk_acs import splunk_acs_router

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
    # Add timeout and connection handling
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
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

# Configure CORS for cross-browser compatibility
# Allow specific origins including localhost and your frontend IP
origins = [
    "http://localhost:8500",
    "http://127.0.0.1:8500",
    f"http://{server_ip}:8500",  # Dynamically detected frontend IP
    "http://192.168.100.44:8500",  # Specific IP from error
    "http://192.168.100.62:8500",  # Additional IP that might be needed
    "http://localhost:3000",  # React dev server default
    "http://127.0.0.1:3000",
    f"http://{server_ip}:3000",
    "*",  # Allow all origins - only use in development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Use the defined origins list instead of "*"
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],  # Explicit HTTP methods
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type", 
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers"
    ],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Add global exception handler for connection errors
@app.exception_handler(RuntimeError)
async def runtime_exception_handler(request: Request, exc: RuntimeError):
    """Handle runtime errors like TCP transport issues"""
    if "TCPTransport closed" in str(exc):
        logger.warning(f"TCP transport error: {exc}")
        return JSONResponse(
            status_code=499,  # Client Closed Request
            content={"detail": "Connection was closed by client"}
        )
    raise exc

# Add connection timeout middleware
@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    """Add timeout handling for requests"""
    try:
        # Set a reasonable timeout for requests
        response = await asyncio.wait_for(call_next(request), timeout=30.0)
        return response
    except asyncio.TimeoutError:
        logger.warning(f"Request timeout for {request.url}")
        return JSONResponse(
            status_code=408,
            content={"detail": "Request timeout"}
        )
    except Exception as e:
        logger.error(f"Request error: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

# Add global exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )

@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    """Handle runtime errors like TCP transport issues"""
    if "TCPTransport closed" in str(exc):
        logger.warning(f"TCP transport error handled: {exc}")
        return JSONResponse(
            status_code=503,
            content={"detail": "Service temporarily unavailable", "error": "Connection error"}
        )
    logger.error(f"Runtime error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )

app.include_router(hosts_router)
app.include_router(jobs_router)
app.include_router(auth_router)
app.include_router(configs_router)
app.include_router(scheduler_router)
app.include_router(monitoring_router)
app.include_router(splunk_router)
app.include_router(packages_router)

# Include workflows router
from backend.workflows.api import router as workflows_router
app.include_router(workflows_router)
app.include_router(users_router)
app.include_router(serverclass_router)
app.include_router(files_router)
app.include_router(ssh_router)
app.include_router(splunk_acs_router)

app.include_router(playbooks_router, prefix="/api")
app.include_router(executions_router, prefix="/api")

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
            "splunk": "/splunk",
            "packages": "/packages",
            "users": "/users",
            "serverclass": "/api/serverclass",
            "files": "/files",
            "ssh": "/ssh",
            "splunk_acs": "/splunk-acs",

            "playbooks": "/api/playbooks",
            "executions": "/api/executions",
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }

# Connection health check endpoint
@app.get("/health/connection")
async def connection_health_check():
    """Check connection health and server status"""
    try:
        # Basic health check
        return {
            "status": "healthy",
            "version": settings.VERSION,
            "timestamp": datetime.utcnow().isoformat(),
            "connection": "stable",
            "server": "running"
        }
    except Exception as e:
        logger.error(f"Connection health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="SIEMply Backend Server")
    parser.add_argument(
        "--host", 
        default=settings.API_HOST,
        help="Host to bind to"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=settings.API_PORT,
        help="Port to bind to"
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
        log_level="info" if not args.debug else "debug",
        # Enhanced connection handling for stability
        timeout_keep_alive=60,
        timeout_graceful_shutdown=60,
        access_log=True,
        # Conservative connection pool settings to prevent overload
        limit_concurrency=100,
        limit_max_requests=1000,
        # Single worker for stability
        workers=1,
        # Use asyncio loop for better compatibility
        loop="asyncio",
        # Add connection handling improvements
        http="httptools",
        # Add error handling
        log_config=None,
        # Add server header
        server_header=False
    ) 