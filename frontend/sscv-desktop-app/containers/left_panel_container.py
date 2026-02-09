# safeshieldcv/frontend/sscv-desktop-app/containers/left_panel_container.py
from pathlib import Path
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLabel
from widgets.color_widget import SSCVColor


class SSCV_LeftTopContainer(SSCVColor):
    """Container class to handle webcam processing"""

    def __init__(self):
        super().__init__("black")
        self.main_container = QVBoxLayout()
        self.main_container.setContentsMargins(0, 0, 0, 0)
        self.main_container.setSpacing(5)

        self.initContainer()

    def initContainer(self):
        self.setLayout(self.main_container)

# bottom layout
class SSCV_LeftBottomContainer(SSCVColor):
    def __init__(self):
        super().__init__("lightblue")
        self.setContentsMargins(0, 0, 0, 0)

class SSCV_LeftMainContainer(QWidget):
    def __init__(self):
        super().__init__()
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(5)
        self.setLayout(self.main_layout)

        # top and bottom left container
        self.top_container = SSCV_LeftTopContainer()
        self.botton_container = SSCV_LeftBottomContainer()
        
        # add container with stretch factors
        self.main_layout.addWidget(self.top_container, 4)
        self.main_layout.addWidget(self.botton_container, 1)