# file safeshieldcv/frontend/sscv-desktop-app/containers/main_container.py
# src 1: https://www.tutorialspoint.com/pyqt/pyqt_major_classes.htm
# src 2: https://www.pythontutorial.net/pyqt/
import os
from pathlib import Path
from PyQt6.QtWidgets import QWidget, QHBoxLayout
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QIcon

from containers.left_panel_container import SSCV_LeftMainContainer
from containers.right_panel_container import SSCV_RightMainContainer

class SafeShieldCV(QWidget):
    # main signal for comminication between panels
    violation_alert_sgn = pyqtSignal(list, str) #(missing items, filename)

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
        # connect violation signal
        left_panel.violation_alert_sgn.connect(self.handle_violation_update)
        main_layout.addWidget(left_panel, 7)
        main_layout.addWidget(right_panel, 3)
    
    def initUI(self):
        """Basic app widgets"""
        # set window title
        self.setWindowTitle("SSCV")
        logo_path = Path(__file__).resolve().parents[1] / "logo" / "sscv_logo.png"
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))
        self.setGeometry(100, 100, 1280, 720)
        self.center()
        self.setStyleSheet("""

            QWidget {
                background-color: #2B2B2B;
                color: white;
            }

            QPushButton {
                background-color: #EDB304;
                color: black;
                border-radius: 4px;
                padding: 6px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #FBBC04;
            }
            QPushButton:disabled {

                background-color: #7F8C8D;
                color: #2B2B2B;

            }
            QTableWidget {
                background-color: #111111;
                gridline-color: #333333;
            }

            QHeaderView::section {
                background-color: #EDB304;
                color: #2B2B2B;
                font-weight: bold;
            }

            QTableWidget::item:selected {
                background-color: #FBBC04;
                color: #2B2B2B;
            }

        """)
    
    def center(self):
        qrect = self.frameGeometry()
        center_screen = self.screen().availableGeometry().center()
        qrect.moveCenter(center_screen)
        self.move(qrect.topLeft())
    
    def handle_violation_update(self, missing_items, filename):
        """Update right panel with violation info"""
        right_panel = self.findChild(SSCV_RightMainContainer)
        if right_panel:
            right_panel.top_container.update_violations(missing_items)
            # display image in middel panel if available
            if filename and os.path.exists(filename):
                # add image to list
                # right_panel.mid_container.display_image(filename)
                from PyQt6.QtWidgets import QListWidgetItem
                from PyQt6.QtCore import Qt

                mid = right_panel.mid_container

                if filename not in mid.images:
                    mid.images.append(filename)

                    item = QListWidgetItem(os.path.basename(filename))
                    item.setData(Qt.ItemDataRole.UserRole, filename)
                    mid.image_list.addItem(item)

                mid.display_image(filename)
    
    # def handle_report_generated(self, report_data):
    #     # handle report generated
    #     print(f"Report generated:{report_data['subject']}")