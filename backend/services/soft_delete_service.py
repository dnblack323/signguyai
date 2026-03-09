"""
Soft Delete Service

This module provides utilities for soft deleting and restoring records.
All delete operations should go through this service to maintain consistency.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


class SoftDeleteService:
    """Service for managing soft deletes across all collections"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def soft_delete(
        self, 
        collection_name: str, 
        record_id: str, 
        deleted_by: str,
        tenant_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        Soft delete a record by setting deleted_at timestamp.
        
        Args:
            collection_name: Name of the MongoDB collection
            record_id: The 'id' field of the record
            deleted_by: User ID who performed the deletion
            tenant_id: Tenant ID for isolation
            reason: Optional reason for deletion
        
        Returns:
            True if successful, False otherwise
        """
        collection = self.db[collection_name]
        
        # Ensure we only delete within the tenant's data
        result = await collection.update_one(
            {
                "id": record_id,
                "tenant_id": tenant_id,
                "deleted_at": None  # Only delete if not already deleted
            },
            {
                "$set": {
                    "deleted_at": datetime.now(timezone.utc).isoformat(),
                    "deleted_by": deleted_by,
                    "deletion_reason": reason
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"Soft deleted {collection_name}/{record_id} by {deleted_by}")
            return True
        else:
            logger.warning(f"Failed to soft delete {collection_name}/{record_id}")
            return False
    
    async def restore(
        self,
        collection_name: str,
        record_id: str,
        restored_by: str,
        tenant_id: str
    ) -> bool:
        """
        Restore a soft-deleted record.
        
        Args:
            collection_name: Name of the MongoDB collection
            record_id: The 'id' field of the record
            restored_by: User ID who performed the restoration
            tenant_id: Tenant ID for isolation
        
        Returns:
            True if successful, False otherwise
        """
        collection = self.db[collection_name]
        
        result = await collection.update_one(
            {
                "id": record_id,
                "tenant_id": tenant_id,
                "deleted_at": {"$ne": None}  # Only restore if deleted
            },
            {
                "$set": {
                    "deleted_at": None,
                    "deleted_by": None,
                    "deletion_reason": None,
                    "restored_at": datetime.now(timezone.utc).isoformat(),
                    "restored_by": restored_by
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"Restored {collection_name}/{record_id} by {restored_by}")
            return True
        else:
            logger.warning(f"Failed to restore {collection_name}/{record_id}")
            return False
    
    async def hard_delete(
        self,
        collection_name: str,
        record_id: str,
        tenant_id: str,
        admin_confirmation: bool = False
    ) -> bool:
        """
        Permanently delete a record. USE WITH CAUTION.
        
        Args:
            collection_name: Name of the MongoDB collection
            record_id: The 'id' field of the record
            tenant_id: Tenant ID for isolation
            admin_confirmation: Must be True to proceed
        
        Returns:
            True if successful, False otherwise
        """
        if not admin_confirmation:
            logger.error("Hard delete attempted without admin confirmation")
            return False
        
        collection = self.db[collection_name]
        
        # First verify the record exists and belongs to tenant
        record = await collection.find_one({
            "id": record_id,
            "tenant_id": tenant_id
        })
        
        if not record:
            logger.warning(f"Hard delete failed: record not found {collection_name}/{record_id}")
            return False
        
        result = await collection.delete_one({
            "id": record_id,
            "tenant_id": tenant_id
        })
        
        if result.deleted_count > 0:
            logger.warning(f"HARD DELETED {collection_name}/{record_id} (PERMANENT)")
            return True
        return False
    
    async def get_deleted_records(
        self,
        collection_name: str,
        tenant_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all soft-deleted records for admin review.
        
        Args:
            collection_name: Name of the MongoDB collection
            tenant_id: Tenant ID for isolation
            limit: Maximum number of records to return
        
        Returns:
            List of deleted records
        """
        collection = self.db[collection_name]
        
        cursor = collection.find(
            {
                "tenant_id": tenant_id,
                "deleted_at": {"$ne": None}
            },
            {"_id": 0}
        ).sort("deleted_at", -1).limit(limit)
        
        return await cursor.to_list(limit)


def build_active_filter(tenant_id: str, include_deleted: bool = False) -> Dict[str, Any]:
    """
    Build a MongoDB filter that excludes soft-deleted records by default.
    
    Args:
        tenant_id: Tenant ID for isolation
        include_deleted: If True, include soft-deleted records
    
    Returns:
        MongoDB filter dict
    """
    base_filter = {"tenant_id": tenant_id}
    
    if not include_deleted:
        base_filter["deleted_at"] = None
    
    return base_filter


def exclude_deleted_filter(existing_filter: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Add deleted_at filter to an existing filter dict.
    
    Args:
        existing_filter: Existing MongoDB filter to extend
    
    Returns:
        Filter with deleted_at condition added
    """
    if existing_filter is None:
        existing_filter = {}
    
    existing_filter["deleted_at"] = None
    return existing_filter
