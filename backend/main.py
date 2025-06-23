#!/usr/bin/env python3
"""
SIEMply Backend Main Application
FastAPI server for the SIEMply system
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List

# Add the project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.config.settings import settings
from backend.models import get_db, Host, HostCreate, HostResponse, HostUpdate

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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to SIEMply API", "version": settings.VERSION}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "api_version": settings.VERSION}

# Host CRUD operations
@app.get("/hosts", response_model=List[HostResponse])
async def get_hosts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all hosts"""
    hosts = db.query(Host).offset(skip).limit(limit).all()
    return hosts

@app.post("/hosts", response_model=HostResponse, status_code=status.HTTP_201_CREATED)
async def create_host(host: HostCreate, db: Session = Depends(get_db)):
    """Create a new host"""
    db_host = Host(**host.dict())
    db.add(db_host)
    db.commit()
    db.refresh(db_host)
    return db_host

@app.get("/hosts/{host_id}", response_model=HostResponse)
async def get_host(host_id: int, db: Session = Depends(get_db)):
    """Get a host by ID"""
    host = db.query(Host).filter(Host.id == host_id).first()
    if host is None:
        raise HTTPException(status_code=404, detail="Host not found")
    return host

@app.patch("/hosts/{host_id}", response_model=HostResponse)
async def update_host(host_id: int, host_update: HostUpdate, db: Session = Depends(get_db)):
    """Update a host"""
    db_host = db.query(Host).filter(Host.id == host_id).first()
    if db_host is None:
        raise HTTPException(status_code=404, detail="Host not found")
    
    # Update host attributes
    update_data = host_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_host, key, value)
    
    db.commit()
    db.refresh(db_host)
    return db_host

@app.delete("/hosts/{host_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_host(host_id: int, db: Session = Depends(get_db)):
    """Delete a host"""
    db_host = db.query(Host).filter(Host.id == host_id).first()
    if db_host is None:
        raise HTTPException(status_code=404, detail="Host not found")
    
    db.delete(db_host)
    db.commit()
    return None

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
    
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.debug,
        log_level="debug" if args.debug else "info",
    ) 