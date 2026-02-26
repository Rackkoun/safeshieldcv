# file sscv_incident_schema.py

from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import List, Optional
from datetime import date, time, datetime

class IncidentBase(BaseModel):
    violation_type: str = Field(..., description="Type of violation")
    location: str = Field(..., description="Location where violation occured")
    missing_items: List[str] = Field(..., description="List of missing PPE items")
    evidence_images: List[str] = Field(default=[], description="Evidence images")

class IncidentCreate(IncidentBase):
    report_text: Optional[str] = Field(None, description="Generated report text")
    email_recipients: List[str] = Field(default=[], description="Email recipients")

class IncidentResponse(IncidentBase):
    id: int
    reported_date: date
    reported_time: time
    report_text: Optional[str]
    email_recipients: List[str]
    email_sent: bool
    email_sent_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ReportRequest(BaseModel):
    """Schema for request generation"""
    date_time: Optional[str] = None
    missing_items: List[str]
    image_ref: Optional[List[str]] = None
    image_data: List[str] = []
    location: str = "Site Area"

    @field_validator('date_time', mode="before")
    def set_datetime_now(cls, v):
        if v is None:
            # Generate current datetime if not provided
            return datetime.now().isoformat()
        return v

    class Config:
        schema_extra = {
            "example": {
                "missing_items": ["no_helmet", "no_gloves"],
                "location": "Construction Zone A",
                "image_ref": ["violation1.jpg"],
                "image_data": ["base64_encoded_image_data"],
                "date_time": "2024-02-04T10:30:00"  # Optional
            }
        }

class ReportResponse(BaseModel):
    """Schema for report response"""
    subject: str
    body: str
    incident_id: int
    incident_ref: str # human readable id
    success: bool

# schema to handle emails request
class EmailSendRequest(BaseModel):
    """Schema for email sending request"""
    recipients: List[EmailStr]