# file safeshieldcv/frontend/sscv-desktop-app/containers/right_panel_container.py

import os
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from widgets.color_widget import SSCVColor

class SSCV_RightTopContainer(QWidget):
    
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)


class SSCV_RightMidContainer(QWidget):
     """Mid Container to display evidence image"""
     def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

class SSCV_RightBotContainer(QWidget):
    """Bottom container to preview generated PPE violation report"""
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
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
        self.main_layout.addWidget(self.mid_container, 2)
        self.main_layout.addWidget(self.bot_container, 4)