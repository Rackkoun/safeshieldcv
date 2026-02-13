# file safeshieldcv/frontend/sscv-desktop-app/containers/right_panel_container.py

import os
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QListWidget,
    QLineEdit, QGroupBox, QFileDialog, QMessageBox, QProgressBar,
    QListWidgetItem, QPushButton, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QPixmap
from widgets.color_widget import SSCVColor

class SSCV_RightTopContainer(QWidget):
    
    def __init__(self):
        # https://emojipedia.org/
        super().__init__()
        layout = QVBoxLayout()
        # set policy
        self.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed
        )
        self.setMinimumHeight(120)
        # summary label
        self.summary_label = QLabel(" No Violations Detected")
        self.summary_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #27ae60;")
        layout.addWidget(self.summary_label)
        # current violations list
        self.violations_list = QLabel("")
        layout.addWidget(self.violations_list)
        self.setLayout(layout)
    
    def update_violations(self, violations):
        if violations:
            self.summary_label.setText(f"🔴 Active Violations: {len(violations)}")
            self.summary_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #e74c3c;")
            self.violations_list.setText("\n".join([f"• {v}" for v in violations]))
        else:
            self.summary_label.setText(f"🟢 No Violations Detected")
            self.summary_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #27ae60;")
            self.violations_list.setText("")
            


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
       title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
       layout.addWidget(title)
       # image list with scroll
       self.image_list = QListWidget()
       self.image_list.itemClicked.connect(self.on_image_selected)
       
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
       layout.addWidget(self.image_list, 2)
       layout.addWidget(self.current_image_label, 3)
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
        #    self
    
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
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    
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
        recipients_layout.addWidget(self.recipients_input)
        config_layout.addLayout(recipients_layout)
        # location
        location_layout = QHBoxLayout()
        location_layout.addWidget(QLabel("Location:"))
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Contruction Zone A")
        location_layout.addWidget(self.location_input)
        config_layout.addLayout(location_layout)
        # add to main layout
        layout.addWidget(config_group)

        # report preview group
        preview_group = QGroupBox("Report Preview")
        preview_layout = QVBoxLayout()
        self.subject_preview = QLineEdit()
        # self.subject_preview.setReadOnly(True)
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
        # self.body_preview.setReadOnly(True)
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
        button_layout.addWidget(self.generate_btn)
        # send btn
        self.send_btn = QPushButton("Send Report")
        button_layout.addWidget(self.send_btn)
        # cancel btn
        self.cancel_btn = QPushButton("Cancel")
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        self.setLayout(layout)


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