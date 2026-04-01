"""
SignGuy AI - Main Application Entry Point

This file serves as the main entry point for the FastAPI application.
It imports from the modular structure while maintaining backward compatibility
with the existing server.py during the migration process.

Architecture:
- /core - Configuration, database, authentication utilities
- /models - Pydantic models and enums
- /routes - API route handlers (to be migrated)
- /services - Business logic (to be migrated)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import from modular structure
from core import db, shutdown_db_client, logger

# Import the existing server.py's app and routes
# This maintains backward compatibility during migration
from server import app, api_router

# Log startup
logger.info("SignGuy AI Backend - Modular Architecture Loaded")
logger.info(f"Database: {db.name}")

# The app is already configured in server.py
# This file can be extended to add new modular routes

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
