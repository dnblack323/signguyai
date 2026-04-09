"""
Cloud Object Storage Service

This module provides cloud storage integration using Emergent Object Storage.
All file uploads are stored in the cloud instead of MongoDB to improve performance
and scalability.

Usage:
    from services.storage import storage_service
    
    # Upload a file
    result = storage_service.upload_file(
        tenant_id="tenant-123",
        category="orders",
        filename="document.pdf",
        data=file_bytes,
        content_type="application/pdf"
    )
    
    # Download a file
    data, content_type = storage_service.download_file(result["storage_path"])
"""

import os
import uuid
import logging
import requests
from typing import Tuple, Optional, Dict, Any

logger = logging.getLogger(__name__)

# Storage API configuration
STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
APP_NAME = "signguy-ai"  # Prefix all paths to avoid bucket collisions

# Module-level storage key - initialized once at startup
_storage_key: Optional[str] = None


class StorageService:
    """Cloud storage service for file uploads and downloads."""
    
    def __init__(self):
        self.storage_url = STORAGE_URL
        self.app_name = APP_NAME
        self._initialized = False
    
    def init(self) -> bool:
        """
        Initialize the storage service. Call once at startup.
        Returns True if initialization successful, False otherwise.
        """
        global _storage_key
        
        if _storage_key:
            self._initialized = True
            return True
        
        emergent_key = os.environ.get("EMERGENT_LLM_KEY")
        if not emergent_key:
            logger.error("EMERGENT_LLM_KEY not found in environment")
            return False
        
        try:
            resp = requests.post(
                f"{self.storage_url}/init",
                json={"emergent_key": emergent_key},
                timeout=30
            )
            resp.raise_for_status()
            _storage_key = resp.json()["storage_key"]
            self._initialized = True
            logger.info("Cloud storage initialized successfully")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to initialize storage: {e}")
            return False
    
    def _get_storage_key(self) -> str:
        """Get the storage key, initializing if necessary."""
        global _storage_key
        
        if not _storage_key:
            if not self.init():
                raise RuntimeError("Storage service not initialized")
        
        return _storage_key
    
    def upload_file(
        self,
        tenant_id: str,
        category: str,
        filename: str,
        data: bytes,
        content_type: str,
        subfolder: str = ""
    ) -> Dict[str, Any]:
        """
        Upload a file to cloud storage.
        
        Args:
            tenant_id: The tenant ID for isolation
            category: File category (e.g., "orders", "documents", "webstores")
            filename: Original filename (used to extract extension)
            data: File content as bytes
            content_type: MIME type of the file
            subfolder: Optional subfolder within the category
        
        Returns:
            Dict with storage_path, size, and other metadata
        """
        key = self._get_storage_key()
        
        # Extract extension from filename
        ext = filename.split(".")[-1].lower() if "." in filename else "bin"
        
        # Build the storage path
        # Format: signguy-ai/{tenant_id}/{category}/{subfolder?}/{uuid}.{ext}
        unique_id = str(uuid.uuid4())
        if subfolder:
            storage_path = f"{self.app_name}/{tenant_id}/{category}/{subfolder}/{unique_id}.{ext}"
        else:
            storage_path = f"{self.app_name}/{tenant_id}/{category}/{unique_id}.{ext}"
        
        try:
            resp = requests.put(
                f"{self.storage_url}/objects/{storage_path}",
                headers={
                    "X-Storage-Key": key,
                    "Content-Type": content_type
                },
                data=data,
                timeout=120
            )
            resp.raise_for_status()
            result = resp.json()
            
            logger.info(f"File uploaded to cloud storage: {storage_path}")
            
            return {
                "storage_path": result.get("path", storage_path),
                "size": result.get("size", len(data)),
                "etag": result.get("etag", ""),
                "content_type": content_type,
                "original_filename": filename
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to upload file: {e}")
            raise RuntimeError(f"Failed to upload file to cloud storage: {e}")
    
    def download_file(self, storage_path: str) -> Tuple[bytes, str]:
        """
        Download a file from cloud storage.
        
        Args:
            storage_path: The path returned from upload_file
        
        Returns:
            Tuple of (file_bytes, content_type)
        """
        key = self._get_storage_key()
        
        try:
            resp = requests.get(
                f"{self.storage_url}/objects/{storage_path}",
                headers={"X-Storage-Key": key},
                timeout=60
            )
            resp.raise_for_status()
            
            content_type = resp.headers.get("Content-Type", "application/octet-stream")
            return resp.content, content_type
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download file: {e}")
            raise RuntimeError(f"Failed to download file from cloud storage: {e}")
    
    def is_initialized(self) -> bool:
        """Check if storage service is initialized."""
        return self._initialized and _storage_key is not None


# Singleton instance
storage_service = StorageService()


# MIME type mapping for common file types
MIME_TYPES = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
    "pdf": "application/pdf",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xls": "application/vnd.ms-excel",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "csv": "text/csv",
    "txt": "text/plain",
    "json": "application/json",
    "xml": "application/xml",
    "zip": "application/zip",
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "mp4": "video/mp4",
    "svg": "image/svg+xml",
}


def get_mime_type(filename: str) -> str:
    """Get MIME type from filename extension."""
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    return MIME_TYPES.get(ext, "application/octet-stream")
