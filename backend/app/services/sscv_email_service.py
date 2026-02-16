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
        # if self.sender_email:
        #     logger.info(f"Email service initialized for: {self.sender_email}")
        # else:
        #     logger.warning("Email service: No sender configured")
    
    def send_incident_email(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        evidence_images: List[str] = None,
        incident_id: str = None
    ) -> Tuple[bool, str]:
        """
        Send email with incident report
        
        Returns: (success: bool, message: str)
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
        
        # Build log prefix with incident_id if available
        log_prefix = f"[{incident_id}] " if incident_id else "[EMAIL] "
        
        logger.info(f"{log_prefix}Preparing email to: {recipients}")
        
        try:
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = ", ".join(recipients)
            msg['Subject'] = subject
            
            logger.debug(f"{log_prefix}Subject: {subject}")
            
            # Add reference to incident in body if provided
            if incident_id:
                body = f"Incident Reference: {incident_id}\n\n{body}"
            
            # Add body text
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach evidence images
            attached_count = 0
            if evidence_images:
                logger.info(f"{log_prefix}Looking for {len(evidence_images)} evidence images")
                for image_ref in evidence_images:
                    try:
                        # Clean the image reference
                        if isinstance(image_ref, str):
                            image_name = Path(image_ref).name
                        else:
                            image_name = str(image_ref)
                        
                        # Try to find the image file
                        image_path = self._find_image_path(image_name)
                        if image_path and image_path.exists():
                            logger.info(f"{log_prefix}Found image at: {image_path}")
                            with open(image_path, "rb") as f:
                                img_data = f.read()
                                img = MIMEImage(img_data)
                                img.add_header(
                                    'Content-Disposition', 
                                    'attachment', 
                                    filename=image_path.name
                                )
                                msg.attach(img)
                            attached_count += 1
                            logger.info(f"{log_prefix}Attached image: {image_path.name}")
                        else:
                            logger.warning(f"{log_prefix}Image not found: {image_name}")
                            logger.warning(f"{log_prefix}Searched paths: {self._get_search_paths(image_name)}")
                    except Exception as e:
                        logger.error(f"{log_prefix}Failed to attach image {image_ref}: {e}")
            
            # Send email
            logger.info(f"{log_prefix}Connecting to SMTP server: {self.smtp_server}:{self.smtp_port}")
            
            try:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30)
                server.starttls()
                logger.info(f"{log_prefix}Starting TLS connection...")
                server.login(self.sender_email, self.sender_password)
                logger.info(f"{log_prefix}Logged in successfully")
                
                server.send_message(msg)
                server.quit()
                
                message = f"Email sent to {len(recipients)} recipient(s)"
                if attached_count > 0:
                    message += f" with {attached_count} attachment(s)"
                
                logger.info(f"✅ {log_prefix}{message}")
                return True, message
                
            except smtplib.SMTPAuthenticationError as e:
                error_msg = f"SMTP authentication failed: {str(e)}. Check email credentials."
                logger.error(f"❌ {log_prefix}{error_msg}")
                return False, error_msg
            except smtplib.SMTPException as e:
                error_msg = f"SMTP error: {str(e)}"
                logger.error(f"❌ {log_prefix}{error_msg}")
                return False, error_msg
            except Exception as e:
                error_msg = f"SMTP connection error: {str(e)}"
                logger.error(f"❌ {log_prefix}{error_msg}")
                return False, error_msg
            
        except Exception as e:
            error_msg = f"Failed to prepare or send email: {str(e)}"
            logger.error(f"❌ {log_prefix}{error_msg}")
            return False, error_msg
    
    def _find_image_path(self, image_ref: str) -> Optional[Path]:
        """Find image file by reference (filename)"""
        image_name = Path(image_ref).name
        
        # Try multiple possible locations
        search_paths = self._get_search_paths(image_name)
        
        for path in search_paths:
            if path.exists():
                logger.debug(f"Found image at: {path}")
                return path
        
        logger.warning(f"Image not found in any location: {image_name}")
        return None
    
    def _get_search_paths(self, image_name: str) -> List[Path]:
        """Get all possible search paths for an image"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        return [
            # Direct path
            Path(image_name),
            # Daily violations directory
            self.evidence_base_dir / "daily_violations" / current_date / image_name,
            # Daily violations root
            self.evidence_base_dir / "daily_violations" / image_name,
            # Evidence base dir directly
            self.evidence_base_dir / image_name,
            # Current working directory
            Path.cwd() / image_name,
            # Try without date subdirectory
            self.evidence_base_dir / "daily_violations" / image_name,
            # Try parent directory
            self.evidence_base_dir.parent / image_name,
        ]
    
    def test_connection(self) -> bool:
        """Test email connection"""
        if not self.sender_email or not self.sender_password:
            logger.warning("Email test: No sender or password configured")
            return False
        
        try:
            logger.info(f"Testing email connection to {self.smtp_server}:{self.smtp_port}")
            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.noop()
            server.quit()
            logger.info("✅ Email connection test successful")
            return True
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ Email authentication failed: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Email connection test failed: {e}")
            return False

# Singleton instance
email_service = SSCVEmailService()