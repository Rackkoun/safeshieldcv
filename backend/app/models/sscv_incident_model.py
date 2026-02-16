# backend/app/models/scv_incident_model.py

"""Models for SSCV database"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Time, Boolean, ARRAY
from sqlalchemy.sql import func
from app.database import Base

class Incident(Base):
    """Incident report model"""
    __tablename__ = "incident"
    
    id = Column(Integer, primary_key=True, index=True)
    violation_type = Column(String(100), nullable=False)
    missing_items = Column(ARRAY(String))
    location = Column(String(200))
    evidence_images = Column(ARRAY(String))
    reported_date = Column(Date, nullable=False)
    reported_time = Column(Time, nullable=False)
    report_text = Column(Text)
    email_recipients = Column(ARRAY(String))
    email_sent = Column(Boolean, default=False)
    email_sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"[Incident] (id={self.id}, location= {self.location}, violation=\"{self.violation_type}\")"