# file frontend/sscv-desktop-app/widgets/email_dialog_widget.py
# @author: Rackkoun
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QListWidget, QListWidgetItem, QTextEdit
)

class EmailReportDialog(QDialog):
    """Dialog UI for reviewing and sendingPPE violation email reports"""

    def __init__(self, subject, body, image_paths, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PPE Violation Report - Review & Send")
        self.setMinimumSize(600, 500)
        self.image_paths = image_paths
        self.init_ui(subject, body)
    
    def init_ui(self, subject, body):
        layout = QVBoxLayout()
        
        # Email recipients
        recipients_layout = QHBoxLayout()
        recipients_layout.addWidget(QLabel("To:"))
        self.recipients_input = QLineEdit()
        self.recipients_input.setPlaceholderText("supervisor1@gmail.com, supervisor2@gmail.com")
        recipients_layout.addWidget(self.recipients_input)
        layout.addLayout(recipients_layout)
        
        # Email subject
        subject_layout = QHBoxLayout()
        subject_layout.addWidget(QLabel("Subject:"))
        self.subject_input = QLineEdit()
        self.subject_input.setText(subject)
        subject_layout.addWidget(self.subject_input)
        layout.addLayout(subject_layout)
        
        # Email body
        layout.addWidget(QLabel("Message:"))
        self.body_input = QTextEdit()
        self.body_input.setText(body)
        self.body_input.setMaximumHeight(150)
        layout.addWidget(self.body_input)
        
        # Attachments
        layout.addWidget(QLabel("Attachments:"))
        self.attachments_list = QListWidget()
        for img_path in self.image_paths:
            item = QListWidgetItem(str(img_path))
            self.attachments_list.addItem(item)
        layout.addWidget(self.attachments_list)
        
        # Add attachment button
        add_btn = QPushButton("Add Attachment")
        add_btn.clicked.connect(self.add_attachment)
        layout.addWidget(add_btn)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.send_btn = QPushButton("Send Report")
        self.send_btn.clicked.connect(self.accept)
        self.send_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.send_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def add_attachment(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Images", "", "Images (*.png *.jpg *.jpeg)"
        )
        for file in files:
            self.image_paths.append(file)
            self.attachments_list.addItem(file)
    
    def get_email_data(self):
        return {
            'recipients': [email.strip() for email in self.recipients_input.text().split(',')],
            'subject': self.subject_input.text(),
            'body': self.body_input.toPlainText(),
            'attachments': self.image_paths
        }