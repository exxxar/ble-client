from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QListWidget, QLabel)
from PyQt6.QtCore import Qt
from core.ble_manager import BLEManager
from core.async_worker import AsyncWorker


class ConnectionTab(QWidget):
    def __init__(self, ble: BLEManager, worker: AsyncWorker, parent=None):
        super().__init__(parent)
        self.ble = ble
        self.worker = worker
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("🔗 Подключение к BLE-устройству")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Список устройств
        self.device_list = QListWidget()
        self.device_list.setMinimumHeight(300)
        layout.addWidget(QLabel("Найденные устройства:"))
        layout.addWidget(self.device_list)

        # Кнопки
        btn_layout = QHBoxLayout()
        self.btn_scan = QPushButton("🔍 Сканировать")
        self.btn_connect = QPushButton("🔗 Подключиться")
        self.btn_disconnect = QPushButton("🔌 Отключиться")
        self.btn_disconnect.setEnabled(False)

        for btn in (self.btn_scan, self.btn_connect, self.btn_disconnect):
            btn.setMinimumHeight(50)

        btn_layout.addWidget(self.btn_scan)
        btn_layout.addWidget(self.btn_connect)
        btn_layout.addWidget(self.btn_disconnect)
        layout.addLayout(btn_layout)

    def _connect_signals(self):
        self.btn_scan.clicked.connect(self._on_scan)
        self.btn_connect.clicked.connect(self._on_connect)
        self.btn_disconnect.clicked.connect(self._on_disconnect)

        self.ble.device_discovered.connect(self._on_device_found)
        self.ble.scan_finished.connect(self._on_scan_finished)
        self.ble.connected.connect(self._on_connected)
        self.ble.disconnected.connect(self._on_disconnected)

    def _on_scan(self):
        self.device_list.clear()
        self.worker.submit(self.ble.scan())

    def _on_device_found(self, name, address):
        self.device_list.addItem(f"{name}  [{address}]")

    def _on_scan_finished(self):
        pass

    def _on_connect(self):
        item = self.device_list.currentItem()
        if not item:
            return
        text = item.text()
        address = text.split('[')[-1].rstrip(']')
        self.worker.submit(self.ble.connect(address))

    def _on_disconnect(self):
        self.worker.submit(self.ble.disconnect())

    def _on_connected(self, address):
        self.btn_connect.setEnabled(False)
        self.btn_disconnect.setEnabled(True)

    def _on_disconnected(self):
        self.btn_connect.setEnabled(True)
        self.btn_disconnect.setEnabled(False)