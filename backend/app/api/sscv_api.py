# file backend/app/api/sscv_api.py

import os
from pathlib import Path
import base64
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text, func
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

# incident management
@app.post("/sscv/api/incidents", response_model=IncidentResponse)
async def create_incident_endpoint(
    incident: IncidentCreate,
    db: Session = Depends(get_db)
):
    """Create a new incident record"""
    try:
        now = datetime.now()
        db_incident = Incident(
            violation_type=incident.violation_type,
            missing_items=incident.missing_items,
            location=incident.location,
            evidence_images=incident.evidence_images,
            reported_date=now.date(),
            reported_time=now.time(),
            report_text=incident.report_text,
            email_recipients=incident.email_recipients or  [],
            email_sent=False,
            email_sent_at=None
        )
        
        db.add(db_incident)
        db.commit()
        db.refresh(db_incident)
        
        return db_incident
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create incident: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create incident: {str(e)}"
        )

@app.get("/sscv/api/incidents", response_model=list[IncidentResponse])
async def list_incidents_endpoint(
    skip: int = 0,
    limit: int = 100,
    date_from: str = None,
    db: Session = Depends(get_db)
):
    """List all incidents with optional filtering"""
    query = db.query(Incident).order_by(Incident.created_at.desc())
    
    if date_from:
        try:
            target_date = datetime.strptime(date_from, "%Y-%m-%d").date()
            query = query.filter(Incident.reported_date >= target_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
    
    incidents = query.offset(skip).limit(limit).all()
    return incidents

@app.get("/sscv/api/incidents/{incident_id}", response_model=IncidentResponse)
async def get_incident_endpoint(
    incident_id: int,
    db: Session = Depends(get_db)
):
    """Get specific incident by ID"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found"
        )
    
    return incident

# report generation
@app.post("/sscv/api/generate", response_model=ReportResponse)
async def generate_ppe_report_endpoint(
    request: ReportRequest,
    db: Session = Depends(get_db)
):
    """Generate PPE violation report using Ollama and save to database"""
    try:
        logger.info(f"Generating report for: {request.missing_items} at {request.location}")
        logger.info(f"Received {len(request.image_ref)} image references")
        logger.info(f"Received {len(request.image_data)} image data items")
        
        # Save evidence images if provided
        saved_image_paths = []
        if request.image_data and len(request.image_data) > 0:
            for i, (image_ref, image_data) in enumerate(zip(request.image_ref, request.image_data)):
                try:
                    if not image_data:
                        continue
                        
                    # Decode base64 (remove data URL prefix if present)
                    if image_data.startswith('data:image'):
                        # Extract base64 from data URL
                        image_data = image_data.split(',')[1]
                    
                    image_bytes = base64.b64decode(image_data)
                    
                    # Save to evidence directory
                    evidence_dir = Path(settings.EVIDENCE_BASE_DIR) / "evidence_storage"
                    evidence_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Create filename with timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_ref = Path(image_ref).name  # Just the filename, no path
                    filename = f"{timestamp}_{i}_{safe_ref}"
                    filepath = evidence_dir / filename
                    
                    # Save file
                    filepath.write_bytes(image_bytes)
                    saved_image_paths.append(str(filepath))
                    logger.info(f"Saved evidence image: {filename}")
                    
                except Exception as e:
                    logger.error(f"Failed to save image {image_ref}: {e}")
        
        # Generate report text using Ollama
        report_text = ollama_service.generate_ppe_report(
            date_time=request.date_time,
            missing_items=request.missing_items,
            image_ref=request.image_ref,
            location=request.location
        )
        
        # Create database record
        now = datetime.now()
        incident = Incident(
            violation_type="PPE Violation",
            missing_items=request.missing_items,
            location=request.location,
            evidence_images=request.image_ref,  # Store original references
            reported_date=now.date(),
            reported_time=now.time(),
            report_text=report_text,
            email_recipients=[],
            email_sent=False,
            email_sent_at=None
        )
        
        db.add(incident)
        db.commit()
        db.refresh(incident)
        
        logger.info(f"[GENERATE PPE] Created incident record: ID={incident.id}")
        
        # Create subject
        clean_items = [item.replace('no_', '') for item in request.missing_items]
        subject = f"PPE Violation: {', '.join(clean_items)} at {request.location}"
        logger.warning(f"[SSCV_API::GENERATE PPE](report text):\n{report_text}")
        return ReportResponse(
            subject=subject,
            body=report_text,
            incident_id=incident.id,
            incident_ref=f"INC-{incident.id:06d}",
            success=True
        )
        
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )

# email management
@app.post("/sscv/api/incidents/{incident_id}/send-email")
async def send_incident_email_endpoint(
    incident_id: int,
    email_request: EmailSendRequest,
    # background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Send email for an incident (background task)"""
    try:
        # Get incident from database
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident {incident_id} not found"
            )
        
        # Create subject
        clean_items = [item.replace('no_', '') for item in incident.missing_items]
        subject = f"PPE Violation: {', '.join(clean_items)} at {incident.location}"
        
        # Send email SYNCHRONOUSLY (not background task)
        success, message = email_service.send_incident_email(
            recipients=email_request.recipients,
            subject=subject,
            body=incident.report_text or "No report text available",
            evidence_images=incident.evidence_images,
            incident_id=f"INC-{incident.id:06d}"  # Now used in logging
        )
        
        # Update database immediately
        if success:
            incident.email_sent = True
            incident.email_sent_at = datetime.now()
            incident.email_recipients = email_request.recipients
            db.commit()
            db.refresh(incident)
            
            logger.info(f"✅ Email sent and DB updated for incident {incident_id}")
            
            return {
                "success": True,
                "message": message,
                "incident_id": incident.id,
                "incident_ref": f"INC-{incident.id:06d}",
                "email_sent": True,
                "sent_at": incident.email_sent_at.isoformat()
            }
        else:
            # Email failed but we return the error
            return {
                "success": False,
                "message": message,
                "incident_id": incident.id,
                "incident_ref": f"INC-{incident.id:06d}",
                "email_sent": False,
                "sent_at": None
            }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to send email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )
@app.get("/sscv/api/stats/daily-range")
async def get_daily_range_statistics(db: Session =Depends(get_db)):
    """Return incident count grouped by date"""
    results = (
        db.query(Incident.reported_date, func.count(Incident.id))\
        .group_by(Incident.reported_date)\
        .order_by(Incident.reported_date)\
        .all()
    )
    return [{
        "date": res[0].isoformat(),
        "count": res[1]
    } for res in results]