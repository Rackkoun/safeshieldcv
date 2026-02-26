# file sscv_incident_service.py

from sqlalchemy.orm import Session
from app.models.sscv_incident_model import Incident
from datetime import datetime
from typing import List, Optional

def create_incident(
        db: Session,
        violation_type: str,
        missing_items: List[str],
        location: str,
        report_text: str,
        image_ref: Optional[List[str]] = None,
        email_sent: bool = False
    ) -> Incident:
    """Save incident to database"""
    now = datetime.now()
    
    incident = Incident(
        violation_type=violation_type,
        missing_items=missing_items,
        location=location,
        evidence_images=image_ref if image_ref else [],
        reported_date=now.date(),
        reported_time=now.time(),
        report_text=report_text,
        email_sent=email_sent,
        email_recipients=[]
    )
    
    db.add(incident)
    db.commit()
    db.refresh(incident)
    
    return incident
    
def get_incidents(db: Session, skip: int = 0, limit: int = 100) -> List[Incident]:
    """Get all incidents with pagination"""
    return db.query(Incident)\
        .order_by(Incident.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()

def get_incident_by_id(db: Session, incident_id: int) -> Optional[Incident]:
    """Get incident by ID"""
    return db.query(Incident).filter(Incident.id == incident_id).first()

def mark_email_sent(db: Session, incident_id: int, recipients: List[str]) -> Optional[Incident]:
    """Mark incident email as sent"""
    incident = get_incident_by_id(db, incident_id)
    if incident:
        incident.email_sent = True
        incident.email_recipients = recipients
        db.commit()
        db.refresh(incident)
    return incident

def get_daily_stats(db: Session, date: datetime.date = None) -> dict:
    """Get statistics for a specific day"""
    
    if not date:
        date = datetime.now().date()
    
    # Get incidents for the date
    incidents = db.query(Incident)\
        .filter(Incident.reported_date == date)\
        .all()
    
    # Calculate stats
    stats = {
        "date": date,
        "total": len(incidents),
        "emails_sent": sum(1 for i in incidents if i.email_sent),
        "by_location": {},
        "by_violation": {}
    }
    
    for incident in incidents:
        # Count by location
        stats["by_location"][incident.location] = stats["by_location"].get(incident.location, 0) + 1
        
        # Count missing items
        for item in incident.missing_items:
            stats["by_violation"][item] = stats["by_violation"].get(item, 0) + 1
    
    return stats