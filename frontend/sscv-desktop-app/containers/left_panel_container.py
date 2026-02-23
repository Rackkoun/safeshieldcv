# safeshieldcv/frontend/sscv-desktop-app/containers/left_panel_container.py
from pathlib import Path
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QTableWidget
from PyQt6.QtGui import QFont
from widgets.color_widget import SSCVColor
from widgets.webcam_widget import WebcamProcessing

from widgets.chart_report_incident_widget import SSCVIncidentReportChart
class SSCV_VideoProcessingContainer(SSCVColor):
    """Class to handle webcam feed"""
    # add signal for violation detection
    violation_detected_sgn = pyqtSignal(list, str)
    def __init__(self):
        super().__init__("black")
        self.setContentsMargins(0, 0, 0, 0)
        # path to model
        model_path = Path(__file__).resolve().parents[1] / "models" / "sscv_yolo26n_v2.onnx"
        print(f"[SSCV_VID_PROC] model_path: {model_path}")
        # init webcam
        conf_threshold = 0.25
        self.webcam_processing = WebcamProcessing(str(model_path), conf_threshold=conf_threshold)
        # connect webcam signal to update right panel
        self.webcam_processing.violation_detected_sgn.connect(self.on_violation_detected)
        # set up layout
        video_layout = QVBoxLayout()
        video_layout.setContentsMargins(0, 0, 0, 0)
        video_layout.addWidget(self.webcam_processing)
        self.setLayout(video_layout)
    
    def start_webcam(self):
        """Start webcam capture"""
        return self.webcam_processing.start_camera()
    
    def stop_webcam(self):
        """Stop webcam capture"""
        return self.webcam_processing.stop_camera()
    
    def on_violation_detected(self, missing_items, filename):
        """handle violation detection and update ui"""
        # add no + missing ppe equipment to display in the ui
        violations_display = [f"Missing {item}" for item in missing_items]
        print(f"[DEBUG] Violation detected in container: {violations_display}, file: {filename}")
        # emit signal to main window to update right panel
        # parent = self.parent()
        # if hasattr(parent, 'violation_alert_sgn'):
        #     parent.violation_alert_sgn.emit(violations_display, filename)
        self.violation_detected_sgn.emit(violations_display, filename)

class SSCV_LeftTopContainer(QWidget):
    """Container class to handle webcam processing"""
    
    violation_alert_sgn = pyqtSignal(list, str)
    def __init__(self):
        super().__init__()
        self.main_container = QVBoxLayout()
        self.main_container.setContentsMargins(0, 0, 0, 0)
        self.main_container.setSpacing(5)

        # webcam container
        self.webcam_container = SSCV_VideoProcessingContainer()
        # propagate signal
        self.webcam_container.violation_detected_sgn.connect(self.violation_alert_sgn.emit)
        # container for btn
        self.controls_layout = QHBoxLayout()
        
        self.setup_ui_btn()
        # connect btn signal
        self.cam_btn.clicked.connect(self.start_camera)
        self.stop_btn.clicked.connect(self.stop_camera)
        self.initContainer()

    def setup_ui_btn(self):
        # cam ON/OFF btn
        self.cam_btn = QPushButton("Start Camera")
        self.cam_btn.setFixedHeight(40)
        self.cam_btn.setFont(QFont("Arial", 12))
        
        # stop btn
        self.stop_btn = QPushButton("Stop Camera")
        self.stop_btn.setFixedHeight(40)
        self.stop_btn.setFont(QFont("Arial", 12))
        self.stop_btn.setEnabled(False)
        # add btn to control
        self.controls_layout.addWidget(self.cam_btn)
        self.controls_layout.addWidget(self.stop_btn)

    def initContainer(self):
        self.setLayout(self.main_container)
        # save the control btn inside a widget
        controls_widget = QWidget()
        controls_widget.setLayout(self.controls_layout)
        # then add to top main container
        self.main_container.addWidget(self.webcam_container, 4)
        self.main_container.addWidget(controls_widget, 1)
    
    def start_camera(self):
        if self.webcam_container.start_webcam():
            self.cam_btn.setText("Camera ON")
            self.cam_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
    
    def stop_camera(self):
        self.webcam_container.stop_webcam()
        self.cam_btn.setText("Start Camera")
        self.cam_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

# bottom layout
class SSCV_LeftBottomContainer(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        # chart left
        self.plotly_chart = SSCVIncidentReportChart()
        # table right
        self.table = QTableWidget()
        layout.addWidget(self.plotly_chart, 2)
        layout.addWidget(self.table)
        self.setLayout(layout)

class SSCV_LeftMainContainer(QWidget):
    violation_alert_sgn = pyqtSignal(list, str)
    def __init__(self):
        super().__init__()
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(5)
        self.setLayout(self.main_layout)

        # top and bottom left container
        self.top_container = SSCV_LeftTopContainer()
        self.botton_container = SSCV_LeftBottomContainer()
        # forward signal from top left container to main
        self.top_container.violation_alert_sgn.connect(self.violation_alert_sgn.emit)
        
        # add container with stretch factors
        self.main_layout.addWidget(self.top_container, 4)
        self.main_layout.addWidget(self.botton_container, 1)
    