#!/usr/bin/env python3
"""
Populate Packages Script
Populates the database with sample Splunk and Cribl packages for demonstration
"""
import sys
from pathlib import Path

# Add the project root to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.models import get_db, SoftwarePackage, Base, engine
from backend.models.package import PackageType, PackageStatus
from sqlalchemy.orm import Session
from datetime import datetime

def populate_sample_packages():
    """Populate database with sample packages"""
    
    # Create database tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Sample Splunk packages
        splunk_packages = [
            {
                "name": "Splunk Universal Forwarder",
                "package_type": "splunk_uf",
                "version": "9.4.3",
                "description": "Latest Splunk Universal Forwarder for data collection and forwarding",
                "vendor": "Splunk Inc.",
                "download_url": "https://download.splunk.com/products/universalforwarder/releases/9.4.3/linux/splunkforwarder-9.4.3-b9e5b7b9db3c-linux-2.6-x86_64.rpm",
                "file_size": 28.5,
                "architecture": "x86_64",
                "os_compatibility": ["linux"],
                "default_install_dir": "/opt",
                "default_user": "splunk",
                "default_group": "splunk",
                "default_ports": {"management": 8089},
                "min_requirements": {"ram": 512, "disk": 2048},
                "status": "active",
                "is_default": True,
                "release_date": datetime(2024, 11, 15),
                "installation_notes": "Recommended version for production environments. Requires manual configuration of outputs.conf."
            },
            {
                "name": "Splunk Universal Forwarder",
                "package_type": "splunk_uf",
                "version": "9.1.1",
                "description": "Stable Splunk Universal Forwarder (LTS)",
                "vendor": "Splunk Inc.",
                "download_url": "https://download.splunk.com/products/universalforwarder/releases/9.1.1/linux/splunkforwarder-9.1.1-64e843ea36b1-linux-2.6-x86_64.rpm",
                "file_size": 26.8,
                "architecture": "x86_64",
                "os_compatibility": ["linux"],
                "default_install_dir": "/opt",
                "default_user": "splunk",
                "default_group": "splunk",
                "default_ports": {"management": 8089},
                "min_requirements": {"ram": 512, "disk": 2048},
                "status": "active",
                "is_default": False,
                "release_date": datetime(2023, 6, 12),
                "installation_notes": "Long-term support version. Stable for enterprise deployments."
            },
            {
                "name": "Splunk Enterprise",
                "package_type": "splunk_enterprise",
                "version": "9.4.3",
                "description": "Latest Splunk Enterprise for indexing and search",
                "vendor": "Splunk Inc.",
                "download_url": "https://download.splunk.com/products/splunk/releases/9.4.3/linux/splunk-9.4.3-b9e5b7b9db3c-linux-2.6-x86_64.rpm",
                "file_size": 485.2,
                "architecture": "x86_64",
                "os_compatibility": ["linux"],
                "default_install_dir": "/opt",
                "default_user": "splunk",
                "default_group": "splunk",
                "default_ports": {"web": 8000, "management": 8089, "indexing": 9997},
                "min_requirements": {"ram": 4096, "disk": 20480},
                "status": "active",
                "is_default": True,
                "release_date": datetime(2024, 11, 15),
                "installation_notes": "Full Splunk Enterprise installation. Requires license configuration."
            }
        ]
        
        # Sample Cribl packages
        cribl_packages = [
            {
                "name": "Cribl Stream Leader",
                "package_type": "cribl_stream_leader",
                "version": "4.8.1",
                "description": "Cribl Stream Leader for centralized configuration management",
                "vendor": "Cribl Inc.",
                "download_url": "https://cdn.cribl.io/dl/4.8.1/cribl-4.8.1-linux-x64.tgz",
                "file_size": 78.4,
                "architecture": "x86_64",
                "os_compatibility": ["linux"],
                "default_install_dir": "/opt",
                "default_user": "cribl",
                "default_group": "cribl",
                "default_ports": {"web": 9000, "api": 9000, "distributed": 4200},
                "min_requirements": {"ram": 1024, "disk": 5120},
                "status": "active",
                "is_default": True,
                "release_date": datetime(2024, 12, 5),
                "installation_notes": "Leader node for distributed deployments. Configure worker groups after installation."
            },
            {
                "name": "Cribl Stream Worker",
                "package_type": "cribl_stream_worker",
                "version": "4.8.1",
                "description": "Cribl Stream Worker for data processing",
                "vendor": "Cribl Inc.",
                "download_url": "https://cdn.cribl.io/dl/4.8.1/cribl-4.8.1-linux-x64.tgz",
                "file_size": 78.4,
                "architecture": "x86_64",
                "os_compatibility": ["linux"],
                "default_install_dir": "/opt",
                "default_user": "cribl",
                "default_group": "cribl",
                "default_ports": {"api": 9000, "metrics": 9090},
                "min_requirements": {"ram": 1024, "disk": 5120},
                "status": "active",
                "is_default": True,
                "release_date": datetime(2024, 12, 5),
                "installation_notes": "Worker node for data processing. Must be connected to a Leader node."
            },
            {
                "name": "Cribl Edge",
                "package_type": "cribl_edge",
                "version": "4.8.1",
                "description": "Cribl Edge for lightweight data collection",
                "vendor": "Cribl Inc.",
                "download_url": "https://cdn.cribl.io/dl/edge/4.8.1/cribl-edge-4.8.1-linux-x64.tgz",
                "file_size": 45.2,
                "architecture": "x86_64",
                "os_compatibility": ["linux"],
                "default_install_dir": "/opt",
                "default_user": "cribl",
                "default_group": "cribl",
                "default_ports": {"api": 9420, "metrics": 9430},
                "min_requirements": {"ram": 256, "disk": 1024},
                "status": "active",
                "is_default": True,
                "release_date": datetime(2024, 12, 5),
                "installation_notes": "Lightweight edge collection agent. Ideal for remote locations with limited resources."
            },
            {
                "name": "Cribl Stream Leader",
                "package_type": "cribl_stream_leader",
                "version": "4.7.2",
                "description": "Previous stable version of Cribl Stream Leader",
                "vendor": "Cribl Inc.",
                "download_url": "https://cdn.cribl.io/dl/4.7.2/cribl-4.7.2-linux-x64.tgz",
                "file_size": 76.8,
                "architecture": "x86_64",
                "os_compatibility": ["linux"],
                "default_install_dir": "/opt",
                "default_user": "cribl",
                "default_group": "cribl",
                "default_ports": {"web": 9000, "api": 9000, "distributed": 4200},
                "min_requirements": {"ram": 1024, "disk": 5120},
                "status": "active",
                "is_default": False,
                "release_date": datetime(2024, 10, 15),
                "installation_notes": "Previous stable version. Use for compatibility with older worker nodes."
            }
        ]
        
        # Combine all packages
        all_packages = splunk_packages + cribl_packages
        
        # Check if packages already exist and add new ones
        added_count = 0
        for pkg_data in all_packages:
            existing = db.query(SoftwarePackage).filter(
                SoftwarePackage.package_type == pkg_data["package_type"],
                SoftwarePackage.version == pkg_data["version"]
            ).first()
            
            if not existing:
                package = SoftwarePackage(**pkg_data)
                db.add(package)
                added_count += 1
                print(f"Added: {pkg_data['name']} v{pkg_data['version']}")
            else:
                print(f"Skipped (already exists): {pkg_data['name']} v{pkg_data['version']}")
        
        # Commit all changes
        db.commit()
        print(f"\nSuccessfully added {added_count} new packages to the database.")
        print(f"Total packages in database: {db.query(SoftwarePackage).count()}")
        
    except Exception as e:
        print(f"Error populating packages: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Populating database with sample packages...")
    populate_sample_packages()
    print("Done!") 