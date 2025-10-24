"""
Files API Router
Handles file operations including upload, download, delete, and folder management
"""
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.models import get_db
from backend.api.auth import get_current_user
from backend.models import User

# Configure logging
import logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/files",
    tags=["files"],
    responses={404: {"description": "File not found"}},
)

# Base files directory
FILES_BASE_DIR = Path("files")
FILES_BASE_DIR.mkdir(exist_ok=True)

class FileItem:
    def __init__(self, name: str, path: Path, is_dir: bool = False):
        self.name = name
        self.path = path
        self.is_dir = is_dir
        self.size = 0
        self.modified_time = datetime.now()
        self.created_time = datetime.now()
        
        if path.exists():
            stat = path.stat()
            self.modified_time = datetime.fromtimestamp(stat.st_mtime)
            self.created_time = datetime.fromtimestamp(stat.st_ctime)
            if not is_dir:
                self.size = stat.st_size

def get_file_info(file_path: Path) -> Dict[str, Any]:
    """Get file information"""
    if not file_path.exists():
        return None
    
    stat = file_path.stat()
    is_dir = file_path.is_dir()
    
    return {
        "name": file_path.name,
        "path": str(file_path.relative_to(FILES_BASE_DIR)),
        "is_dir": is_dir,
        "size": stat.st_size if not is_dir else 0,
        "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "extension": file_path.suffix if not is_dir else "",
        "mime_type": get_mime_type(file_path) if not is_dir else "folder"
    }

def get_mime_type(file_path: Path) -> str:
    """Get MIME type based on file extension"""
    extension = file_path.suffix.lower()
    mime_types = {
        '.txt': 'text/plain',
        '.py': 'text/x-python',
        '.js': 'application/javascript',
        '.ts': 'application/typescript',
        '.json': 'application/json',
        '.xml': 'application/xml',
        '.html': 'text/html',
        '.css': 'text/css',
        '.sh': 'application/x-sh',
        '.bash': 'application/x-sh',
        '.sql': 'application/sql',
        '.yaml': 'application/x-yaml',
        '.yml': 'application/x-yaml',
        '.md': 'text/markdown',
        '.log': 'text/plain',
        '.conf': 'text/plain',
        '.ini': 'text/plain',
        '.cfg': 'text/plain',
        '.zip': 'application/zip',
        '.tar': 'application/x-tar',
        '.gz': 'application/gzip',
        '.tgz': 'application/gzip',
        '.pdf': 'application/pdf',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml',
        '.ico': 'image/x-icon',
        '.mp4': 'video/mp4',
        '.avi': 'video/x-msvideo',
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.csv': 'text/csv',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    }
    return mime_types.get(extension, 'application/octet-stream')

def is_previewable_file(file_path: Path) -> bool:
    """Check if file is previewable/editable"""
    if file_path.is_dir():
        return False
    
    extension = file_path.suffix.lower()
    previewable_extensions = [
        '.txt', '.md', '.log', '.py', '.js', '.ts', '.sh', '.bash',
        '.json', '.xml', '.yaml', '.yml', '.sql', '.html', '.css',
        '.conf', '.ini', '.cfg', '.csv'
    ]
    
    return extension in previewable_extensions

@router.get("/", response_model=List[Dict[str, Any]])
async def list_files(
    path: str = "",
    current_user: User = Depends(get_current_user)
):
    """
    List files and folders in the specified path
    """
    try:
        logger.info(f"Listing files: path='{path}', user={current_user.username}")
        
        # Construct the full path
        full_path = FILES_BASE_DIR / path if path else FILES_BASE_DIR
        
        logger.info(f"Full path: {full_path}")
        logger.info(f"Path exists: {full_path.exists()}")
        logger.info(f"Path is dir: {full_path.is_dir()}")
        
        # Security check: ensure path is within files directory
        if not str(full_path.resolve()).startswith(str(FILES_BASE_DIR.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="Path not found")
        
        if not full_path.is_dir():
            raise HTTPException(status_code=400, detail="Path is not a directory")
        
        # Get all items in the directory
        items = []
        for item_path in full_path.iterdir():
            logger.info(f"Found item: {item_path.name}")
            if item_path.name.startswith('.'):  # Skip hidden files
                logger.info(f"Skipping hidden file: {item_path.name}")
                continue
            
            file_info = get_file_info(item_path)
            if file_info:
                items.append(file_info)
                logger.info(f"Added item: {file_info['name']} (is_dir: {file_info['is_dir']})")
            else:
                logger.warning(f"Could not get file info for: {item_path}")
        
        # Sort: folders first, then files alphabetically
        items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
        
        logger.info(f"Returning {len(items)} items")
        return items
        
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail="Failed to list files")

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    path: str = Form(""),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a file to the specified path
    """
    try:
        # Construct the target directory
        target_dir = FILES_BASE_DIR / path if path else FILES_BASE_DIR
        
        # Security check: ensure path is within files directory
        if not str(target_dir.resolve()).startswith(str(FILES_BASE_DIR.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Create directory if it doesn't exist
        target_dir.mkdir(parents=True, exist_ok=True)
        
        if not target_dir.is_dir():
            raise HTTPException(status_code=400, detail="Target path is not a directory")
        
        # Generate unique filename if file already exists
        file_path = target_dir / file.filename
        counter = 1
        while file_path.exists():
            name = file.filename.rsplit('.', 1)
            if len(name) > 1:
                new_name = f"{name[0]}_{counter}.{name[1]}"
            else:
                new_name = f"{file.filename}_{counter}"
            file_path = target_dir / new_name
            counter += 1
        
        # Save the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File uploaded: {file_path} by user {current_user.username}")
        
        return {
            "message": "File uploaded successfully",
            "file": get_file_info(file_path)
        }
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload file")

@router.post("/create-folder")
async def create_folder(
    name: str = Form(...),
    path: str = Form(""),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new folder in the specified path
    """
    try:
        logger.info(f"Creating folder: name='{name}', path='{path}', user={current_user.username}")
        
        # Validate folder name
        if not name or not name.strip():
            raise HTTPException(status_code=422, detail="Folder name cannot be empty")
        
        # Remove any invalid characters from folder name
        import re
        clean_name = re.sub(r'[<>:"/\\|?*]', '_', name.strip())
        if clean_name != name.strip():
            logger.warning(f"Folder name sanitized from '{name}' to '{clean_name}'")
            name = clean_name
        
        # Construct the target directory
        target_dir = FILES_BASE_DIR / path if path else FILES_BASE_DIR
        
        # Security check: ensure path is within files directory
        if not str(target_dir.resolve()).startswith(str(FILES_BASE_DIR.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Create parent directory if it doesn't exist
        target_dir.mkdir(parents=True, exist_ok=True)
        
        if not target_dir.is_dir():
            raise HTTPException(status_code=400, detail="Target path is not a directory")
        
        # Create the new folder
        new_folder_path = target_dir / name
        
        if new_folder_path.exists():
            raise HTTPException(status_code=400, detail="Folder already exists")
        
        new_folder_path.mkdir()
        
        logger.info(f"Folder created: {new_folder_path} by user {current_user.username}")
        
        return {
            "message": "Folder created successfully",
            "folder": get_file_info(new_folder_path)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating folder: {e}")
        raise HTTPException(status_code=500, detail="Failed to create folder")

@router.post("/create-file")
async def create_file(
    name: str = Form(...),
    content: str = Form(""),
    path: str = Form(""),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new file in the specified path
    """
    try:
        logger.info(f"Creating file: name='{name}', path='{path}', user={current_user.username}")
        
        # Validate file name
        if not name or not name.strip():
            raise HTTPException(status_code=422, detail="File name cannot be empty")
        
        # Remove any invalid characters from file name
        import re
        clean_name = re.sub(r'[<>:"/\\|?*]', '_', name.strip())
        if clean_name != name.strip():
            logger.warning(f"File name sanitized from '{name}' to '{clean_name}'")
            name = clean_name
        
        # Construct the target directory
        target_dir = FILES_BASE_DIR / path if path else FILES_BASE_DIR
        
        # Security check: ensure path is within files directory
        if not str(target_dir.resolve()).startswith(str(FILES_BASE_DIR.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Create directory if it doesn't exist
        target_dir.mkdir(parents=True, exist_ok=True)
        
        if not target_dir.is_dir():
            raise HTTPException(status_code=400, detail="Target path is not a directory")
        
        # Create the new file
        new_file_path = target_dir / name
        
        if new_file_path.exists():
            raise HTTPException(status_code=400, detail="File already exists")
        
        # Write content to file
        with open(new_file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        logger.info(f"File created: {new_file_path} by user {current_user.username}")
        
        return {
            "message": "File created successfully",
            "file": get_file_info(new_file_path)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating file: {e}")
        raise HTTPException(status_code=500, detail="Failed to create file")

@router.get("/download/{file_path:path}")
async def download_file(
    file_path: str,
    current_user: User = Depends(get_current_user)
):
    """
    Download a file
    """
    try:
        # Construct the full file path
        full_path = FILES_BASE_DIR / file_path
        
        # Security check: ensure path is within files directory
        if not str(full_path.resolve()).startswith(str(FILES_BASE_DIR.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if full_path.is_dir():
            raise HTTPException(status_code=400, detail="Cannot download a directory")
        
        logger.info(f"File downloaded: {full_path} by user {current_user.username}")
        
        return FileResponse(
            path=str(full_path),
            filename=full_path.name,
            media_type=get_mime_type(full_path)
        )
        
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        raise HTTPException(status_code=500, detail="Failed to download file")

@router.get("/content/{file_path:path}")
async def get_file_content(
    file_path: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get file content for preview/editing
    """
    try:
        # Construct the full file path
        full_path = FILES_BASE_DIR / file_path
        
        # Security check: ensure path is within files directory
        if not str(full_path.resolve()).startswith(str(FILES_BASE_DIR.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if full_path.is_dir():
            raise HTTPException(status_code=400, detail="Cannot get content of a directory")
        
        # Check if file is previewable
        if not is_previewable_file(full_path):
            raise HTTPException(status_code=400, detail="File type not supported for preview/editing")
        
        # Read file content
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="File is not a text file")
        
        logger.info(f"File content retrieved: {full_path} by user {current_user.username}")
        
        return {
            "content": content
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file content: {e}")
        raise HTTPException(status_code=500, detail="Failed to get file content")

@router.put("/content/{file_path:path}")
async def update_file_content(
    file_path: str,
    content: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """
    Update file content
    """
    try:
        # Construct the full file path
        full_path = FILES_BASE_DIR / file_path
        
        # Security check: ensure path is within files directory
        if not str(full_path.resolve()).startswith(str(FILES_BASE_DIR.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if full_path.is_dir():
            raise HTTPException(status_code=400, detail="Cannot update content of a directory")
        
        # Check if file is previewable
        if not is_previewable_file(full_path):
            raise HTTPException(status_code=400, detail="File type not supported for editing")
        
        # Write new content to file
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        logger.info(f"File content updated: {full_path} by user {current_user.username}")
        
        return {
            "message": "File content updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating file content: {e}")
        raise HTTPException(status_code=500, detail="Failed to update file content")

@router.delete("/{item_path:path}")
async def delete_item(
    item_path: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a file or folder
    """
    try:
        # Construct the full path
        full_path = FILES_BASE_DIR / item_path
        
        # Security check: ensure path is within files directory
        if not str(full_path.resolve()).startswith(str(FILES_BASE_DIR.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="Item not found")
        
        # Delete the item
        if full_path.is_dir():
            shutil.rmtree(full_path)
            logger.info(f"Folder deleted: {full_path} by user {current_user.username}")
        else:
            full_path.unlink()
            logger.info(f"File deleted: {full_path} by user {current_user.username}")
        
        return {"message": "Item deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting item: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete item")

@router.put("/rename")
async def rename_item(
    old_path: str = Form(...),
    new_name: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """
    Rename a file or folder
    """
    try:
        # Construct the old and new paths
        old_full_path = FILES_BASE_DIR / old_path
        new_full_path = old_full_path.parent / new_name
        
        # Security check: ensure paths are within files directory
        if not str(old_full_path.resolve()).startswith(str(FILES_BASE_DIR.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not str(new_full_path.resolve()).startswith(str(FILES_BASE_DIR.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not old_full_path.exists():
            raise HTTPException(status_code=404, detail="Item not found")
        
        if new_full_path.exists():
            raise HTTPException(status_code=400, detail="Target name already exists")
        
        # Rename the item
        old_full_path.rename(new_full_path)
        
        logger.info(f"Item renamed: {old_full_path} -> {new_full_path} by user {current_user.username}")
        
        return {
            "message": "Item renamed successfully",
            "item": get_file_info(new_full_path)
        }
        
    except Exception as e:
        logger.error(f"Error renaming item: {e}")
        raise HTTPException(status_code=500, detail="Failed to rename item")

@router.get("/search")
async def search_files(
    query: str,
    path: str = "",
    current_user: User = Depends(get_current_user)
):
    """
    Search for files and folders
    """
    try:
        # Construct the search directory
        search_dir = FILES_BASE_DIR / path if path else FILES_BASE_DIR
        
        # Security check: ensure path is within files directory
        if not str(search_dir.resolve()).startswith(str(FILES_BASE_DIR.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not search_dir.exists() or not search_dir.is_dir():
            raise HTTPException(status_code=404, detail="Search directory not found")
        
        # Search for files and folders
        results = []
        query_lower = query.lower()
        
        for root, dirs, files in os.walk(search_dir):
            # Search in directories
            for dir_name in dirs:
                if query_lower in dir_name.lower():
                    dir_path = Path(root) / dir_name
                    file_info = get_file_info(dir_path)
                    if file_info:
                        results.append(file_info)
            
            # Search in files
            for file_name in files:
                if query_lower in file_name.lower():
                    file_path = Path(root) / file_name
                    file_info = get_file_info(file_path)
                    if file_info:
                        results.append(file_info)
        
        # Sort results
        results.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
        
        return results
        
    except Exception as e:
        logger.error(f"Error searching files: {e}")
        raise HTTPException(status_code=500, detail="Failed to search files") 