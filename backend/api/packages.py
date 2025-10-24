"""
Software Package API Router
Handles software package management operations for the Database page
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime

from backend.models import (
    get_db, 
    SoftwarePackage, 
    PackageCreate, 
    PackageUpdate, 
    PackageResponse,
    PackageType,
    PackageStatus
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/packages",
    tags=["packages"],
    responses={404: {"description": "Package not found"}},
)

@router.get("/", response_model=List[PackageResponse])
async def get_packages(
    skip: int = 0,
    limit: int = 100,
    package_type: Optional[str] = Query(None, description="Filter by package type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    vendor: Optional[str] = Query(None, description="Filter by vendor"),
    db: Session = Depends(get_db)
):
    """
    Get all software packages with optional filtering
    """
    query = db.query(SoftwarePackage)
    
    if package_type:
        query = query.filter(SoftwarePackage.package_type == package_type)
    
    if status:
        query = query.filter(SoftwarePackage.status == status)
    
    if vendor:
        query = query.filter(SoftwarePackage.vendor.ilike(f"%{vendor}%"))
    
    # Order by package type, then by version (descending)
    query = query.order_by(SoftwarePackage.package_type, SoftwarePackage.version.desc())
    
    packages = query.offset(skip).limit(limit).all()
    return packages

@router.get("/{package_id}", response_model=PackageResponse)
async def get_package(package_id: int, db: Session = Depends(get_db)):
    """
    Get a specific package by ID
    """
    package = db.query(SoftwarePackage).filter(SoftwarePackage.id == package_id).first()
    if package is None:
        raise HTTPException(status_code=404, detail="Package not found")
    return package

@router.post("/", response_model=PackageResponse)
async def create_package(package: PackageCreate, db: Session = Depends(get_db)):
    """
    Create a new software package
    """
    # Check if package with same type and version already exists
    existing = db.query(SoftwarePackage).filter(
        SoftwarePackage.package_type == package.package_type,
        SoftwarePackage.version == package.version
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Package {package.package_type} version {package.version} already exists"
        )
    
    # Create new package
    db_package = SoftwarePackage(**package.dict())
    db.add(db_package)
    db.commit()
    db.refresh(db_package)
    
    logger.info(f"Created new package: {db_package.name} v{db_package.version}")
    return db_package

@router.put("/{package_id}", response_model=PackageResponse)
async def update_package(
    package_id: int, 
    package_update: PackageUpdate, 
    db: Session = Depends(get_db)
):
    """
    Update an existing package
    """
    db_package = db.query(SoftwarePackage).filter(SoftwarePackage.id == package_id).first()
    if db_package is None:
        raise HTTPException(status_code=404, detail="Package not found")
    
    # Update fields
    update_data = package_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_package, field, value)
    
    db_package.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_package)
    
    logger.info(f"Updated package: {db_package.name} v{db_package.version}")
    return db_package

@router.delete("/{package_id}")
async def delete_package(package_id: int, db: Session = Depends(get_db)):
    """
    Delete a package
    """
    db_package = db.query(SoftwarePackage).filter(SoftwarePackage.id == package_id).first()
    if db_package is None:
        raise HTTPException(status_code=404, detail="Package not found")
    
    package_name = f"{db_package.name} v{db_package.version}"
    db.delete(db_package)
    db.commit()
    
    logger.info(f"Deleted package: {package_name}")
    return {"message": f"Package {package_name} deleted successfully"}

@router.get("/types/available", response_model=List[str])
async def get_available_package_types():
    """
    Get list of available package types
    """
    return [ptype.value for ptype in PackageType]

@router.get("/status/available", response_model=List[str])
async def get_available_statuses():
    """
    Get list of available package statuses
    """
    return [status.value for status in PackageStatus]

@router.post("/{package_id}/set-default", response_model=PackageResponse)
async def set_default_package(package_id: int, db: Session = Depends(get_db)):
    """
    Set a package as the default for its type
    """
    db_package = db.query(SoftwarePackage).filter(SoftwarePackage.id == package_id).first()
    if db_package is None:
        raise HTTPException(status_code=404, detail="Package not found")
    
    # Remove default flag from other packages of the same type
    db.query(SoftwarePackage).filter(
        SoftwarePackage.package_type == db_package.package_type,
        SoftwarePackage.id != package_id
    ).update({"is_default": False})
    
    # Set this package as default
    db_package.is_default = True
    db_package.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_package)
    
    logger.info(f"Set package as default: {db_package.name} v{db_package.version}")
    return db_package

@router.get("/defaults/by-type", response_model=List[PackageResponse])
async def get_default_packages(db: Session = Depends(get_db)):
    """
    Get all default packages grouped by type
    """
    packages = db.query(SoftwarePackage).filter(SoftwarePackage.is_default == True).all()
    return packages

@router.post("/bulk-import", response_model=List[PackageResponse])
async def bulk_import_packages(packages: List[PackageCreate], db: Session = Depends(get_db)):
    """
    Bulk import multiple packages
    """
    created_packages = []
    
    for package_data in packages:
        # Check if package already exists
        existing = db.query(SoftwarePackage).filter(
            SoftwarePackage.package_type == package_data.package_type,
            SoftwarePackage.version == package_data.version
        ).first()
        
        if not existing:
            db_package = SoftwarePackage(**package_data.dict())
            db.add(db_package)
            created_packages.append(db_package)
    
    if created_packages:
        db.commit()
        for package in created_packages:
            db.refresh(package)
    
    logger.info(f"Bulk imported {len(created_packages)} packages")
    return created_packages 