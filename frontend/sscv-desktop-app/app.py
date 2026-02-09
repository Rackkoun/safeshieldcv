# file safeshieldcv/frontend/sscv-desktop-app/
import sys
from PyQt6.QtWidgets import QApplication
from containers.main_container import SafeShieldCV

def main():
    app = QApplication(sys.argv)
    window = SafeShieldCV()
    window.show()
    app.exit(app.exec())
