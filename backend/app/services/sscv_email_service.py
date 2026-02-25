# file: backend/app/services/sscv_email_service.py

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
import os

from app.configs.config import settings

logger = logging.getLogger(__name__)

class SSCVEmailService:
    """Email service for sending PPE violation reports"""
    
    def __init__(self):
        self.sender_email = settings.EMAIL_SENDER
        self.sender_password = settings.EMAIL_PASSWORD
        self.smtp_server = settings.EMAIL_SMTP_SERVER
        self.smtp_port = settings.EMAIL_SMTP_PORT
        self.evidence_base_dir = settings.EVIDENCE_BASE_DIR

        logger.info(f"Email service initialized for: {self.sender_email}")
        logger.info(f"SMTP Server: {self.smtp_server}:{self.smtp_port}")
        logger.info(f"Evidence base dir: {self.evidence_base_dir}")
    
    def send_incident_email(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        evidence_images: List[str] = None,
        incident_id: str = None,
        incident_date: str = None   # new parameter
    ) -> Tuple[bool, str]:
        """
        Send email with incident report
        
        Args:
            recipients: List of email addresses
            subject: Email subject
            body: Plain text body
            evidence_images: List of image filenames
            incident_id: Optional incident reference (for logging)
            incident_date: Optional incident date in YYYY-MM-DD format
        """
        # Validate configuration
        if not self.sender_email or not self.sender_password:
            error_msg = "Email not configured in backend - missing sender or password"
            logger.error(error_msg)
            return False, error_msg
        
        if not recipients:
            error_msg = "No recipients specified"
            logger.error(error_msg)
            return False, error_msg
        
        log_prefix = f"[{incident_id}] " if incident_id else "[EMAIL] "
        logger.info(f"{log_prefix}Preparing email to: {recipients}")
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = ", ".join(recipients)
            msg['Subject'] = subject
            
            if incident_id:
                body = f"Incident Reference: {incident_id}\n\n{body}"
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach evidence images
            attached_count = 0
            if evidence_images:
                logger.info(f"{log_prefix}Looking for {len(evidence_images)} evidence images")
                for image_ref in evidence_images:
                    try:
                        image_name = Path(image_ref).name
                        image_path = self._find_image_path(image_name, incident_date=incident_date)
                        if image_path and image_path.exists():
                            logger.info(f"{log_prefix}Found image at: {image_path}")
                            with open(image_path, "rb") as f:
                                img_data = f.read()
                                img = MIMEImage(img_data)
                                img.add_header('Content-Disposition', 'attachment', filename=image_path.name)
                                msg.attach(img)
                            attached_count += 1
                            logger.info(f"{log_prefix}Attached image: {image_path.name}")
                        else:
                            logger.warning(f"{log_prefix}Image not found: {image_name}")
                    except Exception as e:
                        logger.error(f"{log_prefix}Failed to attach image {image_ref}: {e}")
            
            # Send email
            logger.info(f"{log_prefix}Connecting to SMTP server: {self.smtp_server}:{self.smtp_port}")
            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            
            message = f"Email sent to {len(recipients)} recipient(s)"
            if attached_count > 0:
                message += f" with {attached_count} attachment(s)"
            
            logger.info(f"✅ {log_prefix}{message}")
            return True, message
            
        except Exception as e:
            error_msg = f"Failed to prepare or send email: {str(e)}"
            logger.error(f"❌ {log_prefix}{error_msg}")
            return False, error_msg
    
    def _find_image_path(self, image_name: str, incident_date: str = None) -> Optional[Path]:
        """Find image file by name, optionally using incident date"""
        search_paths = self._get_search_paths(image_name, incident_date=incident_date)
        for path in search_paths:
            if path.exists():
                logger.debug(f"Found image at: {path}")
                return path
        logger.warning(f"Image not found: {image_name}")
        return None
    
    def _get_search_paths(self, image_name: str, incident_date: str = None) -> List[Path]:
        """Get all possible search paths for an image"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        paths = [
            # Direct filename
            Path(image_name),
            # Current date folder
            self.evidence_base_dir / "daily_violations" / current_date / image_name,
            # Daily violations root
            self.evidence_base_dir / "daily_violations" / image_name
        ]
        # If incident date is provided and different from current date, add that path early
        if incident_date and incident_date != current_date:
            paths.insert(1, self.evidence_base_dir / "daily_violations" / incident_date / image_name)
        return paths
    
    def test_connection(self) -> bool:
        """Test email connection"""
        if not self.sender_email or not self.sender_password:
            logger.warning("Email test: No sender or password configured")
            return False
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.noop()
            server.quit()
            logger.info("✅ Email connection test successful")
            return True
        except Exception as e:
            logger.error(f"❌ Email connection test failed: {e}")
            return False

# Singleton instance
email_service = SSCVEmailService()
