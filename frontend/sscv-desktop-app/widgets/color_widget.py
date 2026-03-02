# file safeshieldcv/frontend/sscv-desktop-app/widgets/color_widget.py
from PyQt6.QtWidgets import QWidget, QLabel
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtCore import Qt

class SSCVColor(QWidget):
    """Help class to visualize layout area"""
    def __init__(self, color):
        
        super().__init__()
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color))
        self.setPalette(palette)
        # label for displaying imgs
        self.img_label = QLabel(self)
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_label.setStyleSheet("background-color: transparent;")