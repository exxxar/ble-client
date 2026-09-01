from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QLabel
from core.ble_manager import BLEManager
import datetime


class LogPanel(QWidget):
    def __init__(self, ble: BLEManager, parent=None):
        super().__init__(parent)
        self.ble = ble
        self._init_ui()
        self.ble.log.connect(self._append)

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # ✅ СНАЧАЛА создаём log_text
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)

        # Потом кнопку, которая ссылается на log_text
        header = QHBoxLayout()
        header.addWidget(QLabel("📋 Лог событий"))
        self.btn_clear = QPushButton("🗑️ Очистить")
        self.btn_clear.clicked.connect(self.log_text.clear)  # теперь log_text уже существует
        header.addWidget(self.btn_clear)
        layout.addLayout(header)

        # Добавляем log_text в layout
        layout.addWidget(self.log_text)

    def _append(self, message):
        time = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.log_text.append(f"[{time}] {message}")