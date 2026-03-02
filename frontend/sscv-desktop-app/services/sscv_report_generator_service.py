# file frontend/sscv-desktop-app/services/sscv_report_generator.py
# @author: Rackkoun
# goal of this file is to fetch text from ollama and mail it

import requests
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import base64

logger = logging.getLogger(__name__)

class SSCVReportGeneratorService:
    """Backend API client for report generation and email sending"""
    
    def __init__(self, backend_api_url: str):
        # logger.info(f"SSCVREPORTGEN INIT: api_url: {backend_api_url}")
        self.backend_api_url = backend_api_url.rstrip('/')
        self._last_incident_id: Optional[int] = None
        
        # logger.info(f"ReportGenerator initialized: {self.backend_api_url}")
    
    def generate_report(self, missing_items: List[str], image_paths: List[str] = None, 
                       location: str = "Site Area") -> Dict:
        """Generate report via backend API"""
        try:
            # Prepare image data
            image_refs = []
            image_data_list = []
            
            if image_paths:
                for img_path in image_paths:
                    path = Path(img_path)
                    if path.exists():
                        with open(path, 'rb') as f:
                            image_bytes = f.read()
                        # Convert to base64
                        encoded = base64.b64encode(image_bytes).decode('utf-8')
                        image_refs.append(path.name)
                        image_data_list.append(encoded)
            
            # Prepare request payload
            payload = {
                "missing_items": missing_items,
                "location": location,
                "image_ref": image_refs,
                "image_data": image_data_list,
                "date_time": datetime.now().isoformat()  # Add date_time
            }
            
            logger.info(f"[SSCVREPORT GENER](backend_url): {self.backend_api_url}")
            logger.info(f"Sending report request with {len(missing_items)} items, {len(image_refs)} images")
            logger.info(f"Sending report request to: {self.backend_api_url}/generate")
            logger.info(f"Payload missing_items: {missing_items}")
            logger.info(f"Payload location: {location}")
            logger.info(f"Payload image_ref count: {len(image_refs)}")
            logger.info(f"Payload image_data count: {len(image_data_list)}")
            
            # Call backend API
            response = requests.post(
                f"{self.backend_api_url}/generate",
                json=payload,
                timeout=30
            )
            
            logger.info(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self._last_incident_id = result.get("incident_id")
                return result
            else:
                return {
                "subject": f"Backend Error: {response.status_code}",
                "body": f"Failed to generate report. Backend returned status {response.status_code}.\n\nError: {response.text}",
                "incident_id": None,
                "success": False
            }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error: {e}")
            return self._fallback_report(missing_items, location, str(e))
    
    def send_email(self, incident_id: int, recipients: List[str]) -> Dict:
        """Send email via backend API"""
        if not incident_id:
            return {
                "success": False,
                "message": "No incident ID available. Generate a report first.",
                "email_sent": False
            }
        
        if not recipients:
            return {
                "success": False,
                "message": "No recipients specified",
                "email_sent": False
            }
        
        try:            
            response = requests.post(
                f"{self.backend_api_url}/incidents/{incident_id}/send-email",
                json={"recipients": recipients},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result
            else:
                error_msg = f"Backend error: {response.status_code} - {response.text}"
                return {
                    "success": False,
                    "message": error_msg,
                    "email_sent": False
                }
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {
                "success": False,
                "message": error_msg,
                "email_sent": False
            }
    
    def _fallback_report(self, missing_items: List[str], location: str, error: str = None) -> Dict:
        """Fallback when backend is down"""
        if not missing_items:
            return {
                "subject": "No Violations Detected",
                "body": "No PPE violations were detected or specified.",
                "incident_id": None,
                "success": False
            }
        clean_items = [item.replace('no_', '') for item in missing_items]
        return {
            "subject": f"PPE Violation: {', '.join(clean_items)} at {location}",
            "body": f"PPE violation detected at {location}. Missing: {', '.join(clean_items)}. "
                   f"Immediate supervisor action required. [Backend error: {error}]",
            "incident_id": None,
            "success": False
        }
    
    def health_check(self) -> Dict:
        """Check backend health"""
        try:
            base_url = self.backend_api_url.split('/api')[0] if '/api' in self.backend_api_url else self.backend_api_url
            health_url = f"{base_url}/health"
            response = requests.get(health_url, timeout=5)
            
            if response.status_code == 200:
                health_data = response.json()
                return {
                    "status": health_data.get("status", "unknown"),
                    "backend": True,
                    "services": health_data.get("services", {}),
                    "message": "Backend is running",
                    "data": health_data
                }
            else:
                return {
                    "status": "error",
                    "backend": True,
                    "message": f"HTTP {response.status_code}",
                    "services": {}
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "backend": False,
                "message": f"Cannot connect: {str(e)}",
                "services": {}
            }