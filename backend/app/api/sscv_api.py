# file backend/app/api/sscv_api.py

import os
from pathlib import Path
import base64
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
# import uuid
from datetime import datetime
from contextlib import asynccontextmanager
import logging
import base64
from pathlib import Path
from app.configs.config import settings
from app.database import get_db
from app.models.sscv_incident_model import Incident
from app.schemas.sscv_incident_schema import (
    IncidentCreate, IncidentResponse, ReportRequest, ReportResponse, EmailSendRequest
)
from app.services.sscv_ollama_service import ollama_service
from app.services.sscv_incident_service import create_incident, get_incidents
from app.services.sscv_email_service import email_service

logger = logging.getLogger(__name__)

# startup event
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "=" * 60)
    print("SafeShieldCV Backend API Server")
    print("=" * 60)
    print("API Documentation: http://127.0.0.1:8000/sscv/docs")
    print("API Base URL: http://127.0.0.1:8000/sscv/api")

    # Ollama
    if ollama_service.health_check():
        print("[^v^] Ollama service: Connected")
    else:
        print("[`o´] Ollama service: Not connected")

    # Email
    if email_service.test_connection():
        print("[^v^] Email service: Configured and ready")
    else:
        print("[`o´] Email service: Not configured")

    print("=" * 60 + "\n")

    yield  # application runs here

    print("SafeShieldCV Backend API shutting down...")
    
# Init FastAPI
app = FastAPI(
    title="SafeShieldCV Backend API",
    description="Backend API for PPE violation reporting system",
    version="1.0.0",
    openapi_url="/sscv/openapi.json",
    docs_url="/sscv/docs",
    redoc_url="/sscv/redoc",
    lifespan=lifespan
)
# cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for desktop app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Initialize services
# ollama_service = SSCVOllamaClientService()
# health and root
@app.get("/")
async def root():
    """SSCV Root endpoint"""
    return {
        "message": "SafeShieldCV API Server",
        "version": "1.0.0",
        "documentation": "/sscv/docs",
        "api_base": "/sscv/api"
    }

@app.get("/sscv/health")
async def health_check():
    """Health check endpoint for SSCV services"""
    ollama_healthy = ollama_service.health_check()
    
    # Check database connection
    db_healthy = False
    try:
        db = next(get_db())
        db.execute(text("SELECT 1"))
        db_healthy = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
    
    # check email config
    email_configured = email_service.test_connection()
    status_map = {
        "ollama": "healthy" if ollama_healthy else "unhealthy",
        "database": "healthy" if db_healthy else "unhealthy",
        "email": "configured" if email_configured else "not_configured"
    }
    
    overall_status = "healthy" if ollama_healthy and db_healthy else "degraded"
    
    return {
        "status": overall_status,
        "services": status_map,
        "timestamp": datetime.now().isoformat()
    }