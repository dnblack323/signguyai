"""
Migration Tracker - Database Version Control

This module tracks which migrations have been applied to the database
and provides utilities for running migrations safely.
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Dict
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import os
import logging

logger = logging.getLogger(__name__)


class MigrationTracker:
    """Tracks and manages database migrations"""
    
    COLLECTION_NAME = "schema_migrations"
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.migrations_collection = db[self.COLLECTION_NAME]
    
    async def get_applied_migrations(self) -> List[Dict]:
        """Get list of all applied migrations"""
        cursor = self.migrations_collection.find({}).sort("version", 1)
        return await cursor.to_list(1000)
    
    async def get_current_version(self) -> Optional[str]:
        """Get the current schema version"""
        latest = await self.migrations_collection.find_one(
            {"status": "completed"},
            sort=[("version", -1)]
        )
        return latest["version"] if latest else None
    
    async def is_migration_applied(self, version: str) -> bool:
        """Check if a specific migration has been applied"""
        migration = await self.migrations_collection.find_one({
            "version": version,
            "status": "completed"
        })
        return migration is not None
    
    async def record_migration_start(self, version: str, name: str) -> str:
        """Record that a migration is starting"""
        doc = {
            "version": version,
            "name": name,
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "error": None,
            "rollback_available": False
        }
        result = await self.migrations_collection.insert_one(doc)
        return str(result.inserted_id)
    
    async def record_migration_success(self, version: str, rollback_available: bool = True):
        """Record that a migration completed successfully"""
        await self.migrations_collection.update_one(
            {"version": version},
            {"$set": {
                "status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "rollback_available": rollback_available
            }}
        )
        logger.info(f"Migration {version} completed successfully")
    
    async def record_migration_failure(self, version: str, error: str):
        """Record that a migration failed"""
        await self.migrations_collection.update_one(
            {"version": version},
            {"$set": {
                "status": "failed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "error": error
            }}
        )
        logger.error(f"Migration {version} failed: {error}")
    
    async def get_pending_migrations(self, available_migrations: List[str]) -> List[str]:
        """Get list of migrations that haven't been applied yet"""
        applied = await self.get_applied_migrations()
        applied_versions = {m["version"] for m in applied if m["status"] == "completed"}
        return [v for v in available_migrations if v not in applied_versions]


async def run_migration(db: AsyncIOMotorDatabase, version: str, name: str, 
                       migrate_func, rollback_func=None) -> bool:
    """
    Run a single migration with tracking
    
    Args:
        db: Database connection
        version: Migration version (e.g., "001")
        name: Migration name (e.g., "add_soft_deletes")
        migrate_func: Async function to run the migration
        rollback_func: Optional async function to rollback
    
    Returns:
        True if successful, False otherwise
    """
    tracker = MigrationTracker(db)
    
    # Check if already applied
    if await tracker.is_migration_applied(version):
        logger.info(f"Migration {version} already applied, skipping")
        return True
    
    # Record start
    await tracker.record_migration_start(version, name)
    
    try:
        # Run migration
        logger.info(f"Running migration {version}: {name}")
        await migrate_func(db)
        
        # Record success
        await tracker.record_migration_success(version, rollback_func is not None)
        return True
        
    except Exception as e:
        # Record failure
        await tracker.record_migration_failure(version, str(e))
        logger.exception(f"Migration {version} failed")
        return False


async def check_migration_status(db: AsyncIOMotorDatabase) -> Dict:
    """Get current migration status for health checks"""
    tracker = MigrationTracker(db)
    
    applied = await tracker.get_applied_migrations()
    current_version = await tracker.get_current_version()
    
    return {
        "current_version": current_version,
        "total_applied": len([m for m in applied if m["status"] == "completed"]),
        "failed_migrations": [m for m in applied if m["status"] == "failed"],
        "last_migration": applied[-1] if applied else None
    }
