# file safeshieldcv/frontend/sscv-desktop-app/containers/right_panel_container.py

import os
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QListWidget,
    QLineEdit, QGroupBox, QFileDialog, QMessageBox, QProgressBar,
    QListWidgetItem, QPushButton, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QPixmap
from widgets.color_widget import SSCVColor
from services.sscv_report_generator_service import SSCVReportGeneratorService
# import frontend config
from configs.sscv_config import get_config

class SSCVGenerateThread(QThread):
    """Thread for generating report text."""
    report_signal_ready = pyqtSignal(dict)
    progress_signal_update = pyqtSignal(str, int)

    def __init__(self, generator, missing_items, image_paths, location):
        super().__init__()
        self.generator = generator
        self.missing_items = missing_items
        self.image_paths = image_paths
        self.location = location

    def run(self):
        try:
            self.progress_signal_update.emit("Generating report...", 30)
            result = self.generator.generate_report(
                missing_items=self.missing_items,
                image_paths=self.image_paths,
                location=self.location
            )
            self.progress_signal_update.emit("Report generated", 100)
            # print(f"[GENERATOR_THREAD](results): {result}")
            self.report_signal_ready.emit(result)
        except Exception as e:
            error_result = {
                "subject": "Error",
                "body": f'Failed to generate report: {str(e)}',
                "incident_id": None,
                "success": False
            }
            self.report_signal_ready.emit(error_result)

class SSCVSendThread(QThread):
    """Thread for sending the report email."""
    report_signal_sent = pyqtSignal(bool, str)
    progress_signal_update = pyqtSignal(str, int)

    def __init__(self, generator, incident_id, recipients):
        super().__init__()
        self.generator = generator
        self.incident_id = incident_id
        self.recipients = recipients

    def run(self):
        try:
            self.progress_signal_update.emit("Sending email...", 50)
            result = self.generator.send_email(
                incident_id=self.incident_id,
                recipients=self.recipients
            )
            self.progress_signal_update.emit("Email sent", 100)
            self.report_signal_sent.emit(
                result.get("success", False),
                result.get("message", "Unknown error")
            )
        except Exception as e:
            self.report_signal_sent.emit(False, f"Error: {str(e)}")

class SSCV_RightTopContainer(QWidget):
    
    def __init__(self):
        # https://emojipedia.org/
        super().__init__()

        self.current_violations = []
        layout = QVBoxLayout()
        # app logo
        self.logo_label = QLabel()
        logo_path = Path(__file__).resolve().parents[1] / "logo" / "sscv_logo.png"
        if logo_path.exists():
            # print(f"[DEBUG LOGO] file exist: {logo_path}")
            pixmap = QPixmap(str(logo_path))
            self.logo_label.setPixmap(
                pixmap.scaled(
                    220, 150,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )
            self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.logo_label)
            
        # else:
            # print(f"[DEBUG LOGO] file not found: at {logo_path}")
        # set policy
        self.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed
        )
        self.setMinimumHeight(120)
        # summary label
        self.summary_label = QLabel("🟢 No Violations Detected")
        self.summary_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #27ae60;")
        layout.addWidget(self.summary_label)
        # current violations list
        self.violations_list = QLabel("")
        # self.violations_list.setStyleSheet("color: #7f8c8d;")
        self.violations_list.setStyleSheet("""
        color: #ECF0F1;
        font-size: 13px;
        padding-left: 5px;
        """)
        layout.addWidget(self.violations_list)
        self.setLayout(layout)
    
    # def setup_app_logo(self):
    #     logo_path = Path(__file__).resolve().parents[1] / "logo" / "sscv_logo.png"
    #     pixmap = QPixmap(str(logo_path))
    #     self.logo_label.setPixmap(
    #         pixmap.scaled(
    #             220, 150,
    #             Qt.AspectRatioMode.KeepAspectRatio,
    #             Qt.TransformationMode.SmoothTransformation
    #         )
    #     )
    
    def update_violations(self, violations):
        # update current violations
        self.current_violations = violations
        if violations:
            self.summary_label.setText(f"🔴 Active Violations: {len(violations)}")
            self.summary_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #e74c3c;")
            # print(f"[TOPRIGHT_PANEL - DEBUG](missing items SANITY): {violations}")
            self.violations_list.setText("\n".join([f"• {v}" for v in violations]))
        else:
            self.summary_label.setText(f"🟢 No Violations Detected")
            self.summary_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #27ae60;")
            self.violations_list.setText("")
            
    def get_current_violations(self):
        """Get current violations as a list"""
        return self.current_violations

class SSCV_RightMidContainer(QWidget):
    """Mid Container to display evidence image"""
    image_selected = pyqtSignal(str)

    def __init__(self):
       super().__init__()
       self.images = []
       # track currently displayed image
       self.current_image_path = None
       layout = QVBoxLayout()
       # add title
       title = QLabel("Evidence Images")
       title.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
       layout.addWidget(title)
       # image list with scroll
       self.image_list = QListWidget()
       self.image_list.setStyleSheet("""

        QListWidget {
            background-color: #ECF0F1;
            color: black;
            border-radius: 4px;
        }

        QListWidget::item {
            padding: 6px;
        }

        QListWidget::item:selected {
            background-color: #FBBC04;
            color: black;
        }

        """)
       self.image_list.itemClicked.connect(self.on_image_selected)
       layout.addWidget(self.image_list, 2)
       
       # current image 
       self.current_image_label = QLabel("Select an image to preview")
       self.current_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
       self.current_image_label.setStyleSheet("""
           border: 2px dashed #bdc3c7;
           border-radius: 5px;
           padding: 20px;
           background-color: #ecf0f1;
           color: #7f8c8d;
       """)
       # set policy to do not let selected image affect the app ui
       self.current_image_label.setSizePolicy(
           QSizePolicy.Policy.Ignored,
           QSizePolicy.Policy.Ignored
       )
       self.current_image_label.setMinimumHeight(200)
       self.current_image_label.setMaximumHeight(300)
       layout.addWidget(self.current_image_label, 3)
       # control btn
       btn_layout = QHBoxLayout()
       self.add_image_btn = QPushButton("➕ Add Image")
       self.remove_image_btn = QPushButton("Remove Image")
       self.clear_all_btn = QPushButton("Clear All")
       # connect btn signal to slot
       self.add_image_btn.clicked.connect(self.add_image)
       self.remove_image_btn.clicked.connect(self.remove_selected_image)
       self.clear_all_btn.clicked.connect(self.clear_all_images)
       # add to controls widgets
       btn_layout.addWidget(self.add_image_btn)
       btn_layout.addWidget(self.remove_image_btn)
       btn_layout.addWidget(self.clear_all_btn)
       # add widget to layout
       layout.addLayout(btn_layout, 0)
       self.setLayout(layout)
    
    def add_image(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Evidence Images", "",
            "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*.*)"
        )
        for file in files:
            if file not in self.images:
                self.images.append(file)
                item = QListWidgetItem(os.path.basename(file))
                item.setData(Qt.ItemDataRole.UserRole, file)
                self.image_list.addItem(item)
    
    def remove_selected_image(self):
        current = self.image_list.currentRow()
        if current >= 0:
            item = self.image_list.takeItem(current)
            if item:
                file_path = item.data(Qt.ItemDataRole.UserRole)
                if file_path in self.images:
                    self.images.remove(file_path)
                if file_path == self.current_image_path:
                    self.clear_preview()

    def on_image_selected(self, item):
       file_path = item.data(Qt.ItemDataRole.UserRole)
       self.current_image_path = file_path
       self.image_selected.emit(file_path)
       # display preview
       pixmap = QPixmap(file_path)
       if not pixmap.isNull():
           scaled = pixmap.scaled(
               self.current_image_label.size(),
               Qt.AspectRatioMode.KeepAspectRatio,
               Qt.TransformationMode.SmoothTransformation
           )
           self.current_image_label.setPixmap(scaled)
    
    def display_image(self, filename):
        """Display image in the preview area"""
        if filename and filename not in self.images:
            self.add_image(filename)

        pixmap = QPixmap(filename)
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                self.current_image_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.current_image_label.setPixmap(scaled)
            # clear text placeholder
            self.current_image_label.setText("")
        else:
            self.current_image_label.setText("No preview available")
            self.current_image_label.setPixmap(QPixmap()) # clear
    
    def get_image_paths(self):
        """Return list of all image paths"""
        return self.images.copy()
    
    @pyqtSlot(str)
    def handle_automated_evidence(self, file_path):
        """Programmatically add a violation screenshot to the list"""
        if file_path and os.path.exists(file_path):
            if file_path not in self.images:
                self.images.append(file_path)
                item = QListWidgetItem(os.path.basename(file_path))
                item.setData(Qt.ItemDataRole.UserRole, file_path)
                self.image_list.addItem(item)
                # automatically select the newest one
                self.image_list.setCurrentItem(item)
                self.on_image_selected(item)
                print(f"[UI] Evidence added to list: {file_path}")

    def clear_all_images(self):
        self.image_list.clear()
        self.images.clear()
        self.current_image_label.setText("Select an image to preview")
        self.clear_preview()
    
    def clear_preview(self):
        """Clear the image preview and reset default state"""
        self.current_image_path = None
        # remove pixmap
        self.current_image_label.clear()
        self.current_image_label.setText("Select an image to preview")
        self.current_image_label.setStyleSheet("""
           border: 2px dashed #bdc3c7;
           border-radius: 5px;
           padding: 20px;
           background-color: #ecf0f1;
           color: #7f8c8d;
       """)
    
    def resizeEvent(self, event):
        if self.current_image_label.pixmap():
            pixmap = self.current_image_label.pixmap()
            if pixmap:
                scaled = pixmap.scaled(
                    self.current_image_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.current_image_label.setPixmap(scaled)
        super().resizeEvent(event)

class SSCV_RightBotContainer(QWidget):
    """Bottom container to preview generated PPE violation report"""
    # signal when report is ready for preview
    report_generated_sgn = pyqtSignal(dict)
    # signal for status updates
    report_status = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.config = get_config()
        self.report_generator = None
        self.current_report = None
        self.worker_thread = None
        self.init_ui()
        self.init_generator()
    
    def init_ui(self):
        layout = QVBoxLayout()
        # report config group
        config_group = QGroupBox("Report Configuration")
        config_layout = QVBoxLayout()
        config_group.setLayout(config_layout)
        # email recipients
        recipients_layout = QHBoxLayout()
        recipients_layout.addWidget(QLabel("To:"))
        self.recipients_input = QLineEdit()
        self.recipients_input.setPlaceholderText("supervisor@sscv.cm, other@company.com")
        # load default recipients
        default_recipients = self.config.default_recipients
        if default_recipients:
            self.recipients_input.setText(", ".join(default_recipients))
        recipients_layout.addWidget(self.recipients_input)
        config_layout.addLayout(recipients_layout)
        # location
        location_layout = QHBoxLayout()
        location_layout.addWidget(QLabel("Location:"))
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Contruction Zone A")
        # add default location from config file
        self.location_input.setText(self.config.default_location)
        location_layout.addWidget(self.location_input)
        config_layout.addLayout(location_layout)
        # add to main layout
        layout.addWidget(config_group)

        # report preview group
        preview_group = QGroupBox("Report Preview")
        preview_layout = QVBoxLayout()
        self.subject_preview = QLineEdit()
        self.subject_preview.setReadOnly(True)
        self.subject_preview.setStyleSheet(
            """
            QLineEdit {
                background-color: #f8f9fa;
                color: #000000;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 5px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """
        )
        # add subject to layout preview
        preview_layout.addWidget(QLabel("Subject:"))
        preview_layout.addWidget(self.subject_preview)
        # add body to preview layout
        self.body_preview = QTextEdit()
        self.body_preview.setReadOnly(True)
        self.body_preview.setMaximumHeight(100)
        self.body_preview.setStyleSheet(
            """
            QTextEdit {
                background-color: #f8f9fa;
                color: #000000;
                border: 1px solid #ced4da;
                border-radius: 4px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 10pt;
            }
        """)
        preview_layout.addWidget(QLabel("Message:"))
        preview_layout.addWidget(self.body_preview)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

        # progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        layout.addWidget(self.status_label)

        # btn
        button_layout = QHBoxLayout()
        # generate btn
        self.generate_btn = QPushButton("Generate Report")
        self.generate_btn.clicked.connect(self.generate_report)
        button_layout.addWidget(self.generate_btn)
        # send btn
        self.send_btn = QPushButton("Send Report")
        self.send_btn.clicked.connect(self.send_report)
        self.send_btn.setEnabled(False)
        button_layout.addWidget(self.send_btn)
        # cancel btn
        self.cancel_btn = QPushButton("Cancel")
        button_layout.addWidget(self.cancel_btn)
        # layout.addLayout(button_layout)
        # self.setLayout(layout)
        # add a test btn to test the connection
        self.test_btn = QPushButton("🔧 Test Connection")
        self.test_btn.clicked.connect(self.test_connection)
        self.test_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #07e664; }
        """)
        button_layout.addWidget(self.test_btn)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def init_generator(self):
        """Initialize backend API client"""
        try:
            # print(f"[SSCV INIT GENERATOR] (URL): config api url: {self.config.api_url}")
            self.generator = SSCVReportGeneratorService(self.config.api_url)
            # Test connection
            health = self.generator.health_check()
            # print(f"[SSCV-RightBotUI - Healt]: health status - <({health})>")
            if health.get("backend", False):
                if health.get("status") == "healthy":
                    self.status_label.setText("✅ Backend connected")
                else:
                    self.status_label.setText("⚠️ Backend degraded")
            else:
                self.status_label.setText("❌ Backend offline")
                
        except Exception as e:
            self.status_label.setText(f"❌ Error: {str(e)}")
            print(f"[ERROR] Failed to initialize generator: {e}")
    
    def test_connection(self):
        """Test backend connection"""
        try:
            health = self.generator.health_check()
            
            if not health.get("backend", False):
                QMessageBox.warning(self, "Connection Test", 
                                  "Cannot connect to backend server.\n"
                                  "Make sure the backend is running on localhost:8000")
                return
            
            if health.get("status") == "healthy":
                services = health.get("data", {}).get("services", {})
                msg = (
                    "✅ Backend is running!\n\n"
                    f"Status: {health.get('status')}\n"
                    f"Ollama: {services.get('ollama', 'unknown')}\n"
                    f"Database: {services.get('database', 'unknown')}\n"
                    f"Email: {services.get('email', 'unknown')}"
                )
                QMessageBox.information(self, "Connection Test", msg)
                self.status_label.setText("✅ Backend connected")
            else:
                QMessageBox.warning(self, "Connection Test", 
                                  f"Backend is running but has issues:\n{health.get('message')}")
                
        except Exception as e:
            QMessageBox.critical(self, "Connection Test", f"Error: {str(e)}")

    def generate_report(self):
        """Generate report from current violations"""
        # Debug first
        self.debug_report_flow()
        # Check if generator is initialized
        if not self.generator:
            QMessageBox.warning(self, "Error", 
                              "Report generator not initialized. Please check backend connection.")
            return
        
        # Get image paths
        parent = self.parent()
        image_paths = []
        if isinstance(parent, SSCV_RightMainContainer):
            mid_container = parent.mid_container
            if hasattr(mid_container, 'get_image_paths'):
                image_paths = mid_container.get_image_paths()
        
        # Get missing items
        missing_items = []
        if isinstance(parent, SSCV_RightMainContainer):
            top_container = parent.top_container
            if hasattr(top_container, 'get_current_violations'):
                missing_items = top_container.get_current_violations()
            else:
                missing_items = getattr(top_container, "current_violations", [])
        # Debug: print what we're sending
        # print(f"[DEBUG] Missing items from UI: {missing_items}")
        # print(f"[DEBUG] Image paths: {image_paths}")
        # Fallback if no violations
        # if not missing_items:
        #     missing_items = ['no_helmet', 'no_gloves']
        #     print(f"[DEBUG] Using fallback missing items: {missing_items}")
        # sanitize missing items
        missing_items = [
            item.replace("Missing ", "").strip()
            for item in missing_items
            if isinstance(item, str)
        ]
        # print(f"[DEBUG] Missing items before sending to backend: {missing_items}")
        
        # Get location
        location = self.location_input.text().strip() or self.config.default_location
        
        # Validate
        if not missing_items and not image_paths:
            QMessageBox.information(self, "No violations", 
                                  "No detected violations available to generate a report.")
            return
        
        # Disable UI during generation
        self.generate_btn.setEnabled(False)
        self.send_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Generating report...")
        
        # Start worker thread
        self.worker_thread = SSCVGenerateThread(
            generator=self.generator,
            missing_items=missing_items,
            image_paths=image_paths,
            location=location
        )
        
        self.worker_thread.report_signal_ready.connect(self.on_report_ready)
        self.worker_thread.progress_signal_update.connect(self.on_progress_update)
        self.worker_thread.finished.connect(self.on_worker_finished)
        self.worker_thread.start()
    
    def update_violations_from_detection(self, detected_items):
        """Update violations from detection system"""
        parent = self.parent()
        if isinstance(parent, SSCV_RightMainContainer):
            top_container = parent.top_container
            if hasattr(top_container, 'update_violations'):
                # Convert detected items to proper format
                violations = [item for item in detected_items if item]
                top_container.update_violations(violations)
                # print(f"[DEBUG] Updated violations: {violations}")

    @pyqtSlot(dict)
    def on_report_ready(self, report_data):
        """Handle generated report data"""
        self.current_incident_id = report_data.get("incident_id")
        
        # Update preview
        self.subject_preview.setText(report_data.get('subject', ''))
        self.body_preview.setText(report_data.get('body', ''))
        
        # Enable send button if we have an incident ID
        if self.current_incident_id and report_data.get('success', False):
            self.send_btn.setEnabled(True)
            self.status_label.setText("✅ Report ready for sending")
        else:
            self.status_label.setText("⚠️ Report generated (backend offline)")
        
        # Emit signal
        self.report_generated_sgn.emit(report_data)
    
    @pyqtSlot(bool, str)
    def on_report_sent(self, success, message):
        """Handle report sending completion"""
        if success:
            QMessageBox.information(self, "Success", message)
            self.status_label.setText("✅ Email sent")
            
            # Clear form for next report
            self.subject_preview.clear()
            self.body_preview.clear()
            self.send_btn.setEnabled(False)
            self.current_incident_id = None
        else:
            QMessageBox.warning(self, "Error", message)
            self.status_label.setText("❌ Email failed")
    
    @pyqtSlot(str, int)
    def on_progress_update(self, message, percent):
        """Update progress display."""
        self.progress_bar.setValue(percent)
        self.status_label.setText(message)
        # print(f"[UI DEBUG] Progress: {message} ({percent}%)")
    
    @pyqtSlot()
    def on_worker_finished(self):
        """Clean up after worker thread."""
        # Re-enable the generate button, but the send button should only be enabled if we have a report
        self.generate_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.worker_thread = None
        # print("[UI DEBUG] Worker thread finished")
    
    def send_report(self):
        """Send the generated report"""
        if not self.current_incident_id:
            QMessageBox.warning(self, "Error", "No incident generated. Please generate a report first.")
            return
        
        # Get recipients
        recipients_text = self.recipients_input.text().strip()
        if not recipients_text:
            QMessageBox.warning(self, "Error", "Please specify email recipients.")
            return
        
        recipients = [email.strip() for email in recipients_text.split(',') if email.strip()]
        if not recipients:
            QMessageBox.warning(self, "Error", "Please specify valid email recipients.")
            return
        
        # Disable UI during sending
        self.send_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Sending email...")
        
        # Start worker thread
        self.worker_thread = SSCVSendThread(
            generator=self.generator,
            incident_id=self.current_incident_id,
            recipients=recipients
        )
        
        self.worker_thread.report_signal_sent.connect(self.on_report_sent)
        self.worker_thread.progress_signal_update.connect(self.on_progress_update)
        self.worker_thread.finished.connect(self.on_worker_finished)
        self.worker_thread.start()
    
    def cancel_operation(self):
        """Cancel current operation."""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.terminate()
            self.worker_thread.wait()
        
        self.on_worker_finished()
        self.status_label.setText("Operation cancelled")
    
    def clear_form(self):
        """Clear the report form."""
        self.subject_preview.clear()
        self.body_preview.clear()
        self.send_btn.setEnabled(False)
        self.current_report = None
    
    def debug_signal_connections(self):
        """Debug method to check signal connections"""
        print("\n=== SIGNAL DEBUG ===")
        print(f"1. Worker thread exists: {self.worker_thread is not None}")
        
        if self.worker_thread:
            print(f"2. Thread signals:")
            print(f"   - report_signal_ready: {hasattr(self.worker_thread, 'report_signal_ready')}")
            print(f"   - report_signal_sent: {hasattr(self.worker_thread, 'report_signal_sent')}")
            print(f"   - progress_signal_update: {hasattr(self.worker_thread, 'progress_signal_update')}")
        
        print(f"3. Slots connected:")
        print(f"   - on_report_ready signature: {self.on_report_ready.__annotations__ if hasattr(self.on_report_ready, '__annotations__') else 'No annotations'}")
        print(f"   - on_report_sent signature: {self.on_report_sent.__annotations__ if hasattr(self.on_report_sent, '__annotations__') else 'No annotations'}")
        print("===================\n")
    
    def debug_report_flow(self):
        """Debug the report generation flow"""
        print("\n=== REPORT FLOW DEBUG ===")
        
        # Check parent and container relationships
        parent = self.parent()
        print(f"1. Has parent: {parent is not None}")
        print(f"2. Parent type: {type(parent).__name__}")
        
        if isinstance(parent, SSCV_RightMainContainer):
            print(f"3. Top container exists: {parent.top_container is not None}")
            print(f"4. Mid container exists: {parent.mid_container is not None}")
            
            # Check top container violations
            if hasattr(parent.top_container, 'get_current_violations'):
                violations = parent.top_container.get_current_violations()
                print(f"5. Current violations: {violations}")
        
        # Check generator
        print(f"6. Generator initialized: {self.generator is not None}")
        print("===================\n")


class SSCV_RightMainContainer(QWidget):
    
    def __init__(self):
        super().__init__()
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(10, 0, 10, 0)
        self.main_layout.setSpacing(5)
        self.setLayout(self.main_layout)

        # add sub panel
        self.top_container = SSCV_RightTopContainer()
        self.mid_container = SSCV_RightMidContainer()
        self.bot_container = SSCV_RightBotContainer()
        self.initLayout()

    def initLayout(self):
        # set container stretch
        self.main_layout.addWidget(self.top_container, 1)
        self.main_layout.addWidget(self.mid_container, 3)
        self.main_layout.addWidget(self.bot_container, 6)