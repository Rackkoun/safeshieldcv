# safeshieldcv/frontend/sscv-desktop-app/containers/left_panel_container.py
from pathlib import Path
import requests
from PyQt6.QtCore import pyqtSignal, QTimer, QThread
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QTableWidget,
    QHeaderView, QAbstractItemView, QTableWidgetItem
)
from PyQt6.QtGui import QFont
from widgets.color_widget import SSCVColor
from widgets.webcam_widget import WebcamProcessing
# import frontend config
from configs.sscv_config import get_config
from services.sscv_stats_service import SSCVStatisticServices
from widgets.chart_report_incident_widget import SSCVIncidentReportChart


class SSCVIncidentStatsWorker(QThread):
    """Worker clas to fetch data in bg without freezing the ui"""
    data_fetched_sgn = pyqtSignal(list, list) # (incidents, stats)
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client

    def run(self):
        try:
            # fetch both in background
            incidents = self.api_client.get_incidents()
            stats = self.api_client.get_daily_stats()
            self.data_fetched_sgn.emit(incidents, stats)
        except Exception as e:
            print(f"[THREAD ERROR] {e}")
class SSCV_VideoProcessingContainer(SSCVColor):
    """Class to handle webcam feed"""
    # add signal for violation detection
    violation_detected_sgn = pyqtSignal(list, str)
    def __init__(self):
        super().__init__("black")
        self.setContentsMargins(0, 0, 0, 0)
        # path to model
        model_path = Path(__file__).resolve().parents[1] / "models" / "sscv_yolo26n_v2.onnx"
        # print(f"[SSCV_VID_PROC] model_path: {model_path}")
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
        # print(f"[DEBUG] Violation detected in container: {violations_display}, file: {filename}")
        # emit signal to main window to update right panel
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
        self.current_stats = []
        self.config = get_config()
        self.stats_api_client = SSCVStatisticServices(self.config.api_url)
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        # chart left
        self.plotly_chart = SSCVIncidentReportChart()
        # table right
        self.table = QTableWidget()
        self.setup_table()
        layout.addWidget(self.plotly_chart)
        layout.addWidget(self.table)
        self.setLayout(layout)
        # auto-refresh
        self.table.itemSelectionChanged.connect(self.on_row_selected)
        # use worker to trigger the bg refreshing
        self.worker = SSCVIncidentStatsWorker(self.stats_api_client)
        self.worker.data_fetched_sgn.connect(self.on_data_received)
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.start_refresh_async)
        # refresh every 5 secs
        self.refresh_timer.start(5000)
    
    def setup_table(self):
        table_headers = ["ID", "Missing Items", "Date", "Time", "Email Sent", "Recipients"]
        self.table.setColumnCount(len(table_headers))
        self.table.setHorizontalHeaderLabels(table_headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setRowCount(0)
        self.table.setStyleSheet("""
            QTableWidget::item:selected {
                background-color: #FBBC04;
                color: white;
            }
        """)
    
    def start_refresh_async(self):
        # start bg thread
        if not self.worker.isRunning():
            self.worker.start()
    
    def on_data_received(self, incidents, stats):
        # Only update chart if stats have changed
        if stats != self.current_stats:
            self.current_stats = stats
            self.refresh_chart(stats)
        self.refresh_table(incidents)
    
    def refresh_table(self, incidents):
        # incidents = self.stats_api_client.get_incidents()
        self.table.setRowCount(len(incidents))

        for row, incident in enumerate(incidents):
            incident_ref = f"INC-{incident['id']:06d}"
            missings = ", ".join(incident["missing_items"])
            date = incident["reported_date"]
            # remove micros secs
            time = incident["reported_time"].split(".")[0]
            email_sent = "✅" if incident["email_sent"] else "❌"
            recipients = str(len(incident["email_recipients"]))

            self.table.setItem(row, 0, QTableWidgetItem(incident_ref))
            self.table.setItem(row, 1, QTableWidgetItem(missings))
            self.table.setItem(row, 2, QTableWidgetItem(date))
            self.table.setItem(row, 3, QTableWidgetItem(time))
            self.table.setItem(row, 4, QTableWidgetItem(email_sent))
            self.table.setItem(row, 5, QTableWidgetItem(recipients))
    
    def refresh_chart(self, stats):
        self.plotly_chart.update_chart(stats)
    
    def refresh_data(self):
        self.refresh_table()
        self.refresh_chart()

    def on_row_selected(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            return
        selected_row = selected_items[0].row()
        target_date = self.table.item(selected_row, 2).text()

        # Find index in current_stats that matches the date
        highlight_idx = -1
        for i, entry in enumerate(self.current_stats):
            entry_date = entry["date"].split("T")[0] if "T" in entry["date"] else entry["date"]
            if entry_date == target_date:
                highlight_idx = i
                break

        if highlight_idx != -1:
            self.plotly_chart.highlight_bar(highlight_idx)

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
    