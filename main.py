import sys
import os
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
os.environ["QT_LOGGING_RULES"] = "qt.multimedia.ffmpeg=false"

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("BLE Device Client")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()