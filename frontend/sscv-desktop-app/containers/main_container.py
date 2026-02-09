# file safeshieldcv/frontend/sscv-desktop-app/containers/main_container.py
# src 1: https://www.tutorialspoint.com/pyqt/pyqt_major_classes.htm
# src 2: https://www.pythontutorial.net/pyqt/
import os
from PyQt6.QtWidgets import QWidget, QHBoxLayout
from PyQt6.QtCore import pyqtSignal

from containers.left_panel_container import SSCV_LeftMainContainer
from containers.right_panel_container import SSCV_RightMainContainer

class SafeShieldCV(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        # main layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)
        # add widgets
        left_panel = SSCV_LeftMainContainer()
        right_panel = SSCV_RightMainContainer()
        main_layout.addWidget(left_panel, 7)
        main_layout.addWidget(right_panel, 3)
    
    def initUI(self):
        """Basic app widgets"""
        # set window title
        self.setWindowTitle("SSCV")
        self.setGeometry(100, 100, 1280, 720)
        self.center()
    
    def center(self):
        qrect = self.frameGeometry()
        center_screen = self.screen().availableGeometry().center()
        qrect.moveCenter(center_screen)
        self.move(qrect.topLeft())