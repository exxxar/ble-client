from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QTabWidget,
                             QStatusBar, QLabel, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, QCoreApplication
from core.ble_manager import BLEManager
from core.async_worker import AsyncWorker
from core.device_registry import DEVICE_REGISTRY
from ui.connection_tab import ConnectionTab
from ui.log_panel import LogPanel
from ui.services_tab import ServicesTab
from services import DataLogger, ChartExporter, MQTTService, Notifier


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔵 BLE Device Client")
        self.resize(1000, 700)
        self.setMinimumSize(800, 600)

        # Core
        self.ble = BLEManager()
        self.worker = AsyncWorker()
        self.worker.start()

        # Сервисы
        self.data_logger = DataLogger()
        self.chart_exporter = ChartExporter()
        self.mqtt_service = MQTTService()
        self.notifier = Notifier()

        self.device_tabs = {}

        self._init_ui()
        self._connect_signals()
        self._apply_theme()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Заголовок
        header = QLabel("🔵 BLE Device Client")
        header.setStyleSheet("font-size: 28px; font-weight: bold; padding: 10px; color: #66ccff;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Вкладки
        self.tabs = QTabWidget()

        # Вкладка подключения
        self.conn_tab = ConnectionTab(self.ble, self.worker)
        self.tabs.addTab(self.conn_tab, "🔗 Подключение")

        # Вкладки устройств
        for name, info in DEVICE_REGISTRY.items():
            device = info["class"](self.ble, self.worker)
            # Передаём сервисы в устройство
            device.data_logger = self.data_logger
            device.notifier = self.notifier
            device.mqtt = self.mqtt_service
            self.device_tabs[name] = device
            self.tabs.addTab(device, f"{info['icon']} {name}")

        # 🆕 Вкладка сервисов
        self.services_tab = ServicesTab(
            self.data_logger, self.chart_exporter,
            self.mqtt_service, self.notifier, self.device_tabs
        )
        self.tabs.addTab(self.services_tab, "⚙️ Сервисы")

        # Лог
        self.log_panel = LogPanel(self.ble)
        self.tabs.addTab(self.log_panel, "📋 Лог")

        self.tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tabs)

        # Статус-бар
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self._update_status()

    def _connect_signals(self):
        self.ble.connected.connect(self._on_ble_connected)
        self.ble.disconnected.connect(self._on_ble_disconnected)
        self.ble.notification.connect(self._on_notification)

        # Сигналы сервисов
        self.mqtt_service.connected.connect(lambda: self.ble.log.emit("✅ MQTT подключён"))
        self.mqtt_service.error.connect(lambda msg: self.ble.log.emit(msg))
        self.data_logger.log_saved.connect(lambda msg: self.ble.log.emit(msg))
        self.chart_exporter.export_complete.connect(lambda msg: self.ble.log.emit(msg))

    def _on_ble_connected(self, address):
        self._update_status()
        # Публикуем доступность в MQTT
        for name in self.device_tabs:
            self.mqtt_service.publish_availability(name, True)

    def _on_ble_disconnected(self):
        self._update_status()
        for name in self.device_tabs:
            self.mqtt_service.publish_availability(name, False)

    def _on_tab_changed(self, index):
        current = self.tabs.currentWidget()
        for name, device in self.device_tabs.items():
            if device == current:
                device.on_activated()
            elif device.is_active:
                device.on_deactivated()

    def _on_notification(self, char_uuid, data):
        for name, device in self.device_tabs.items():
            if device.CHAR_UUID == char_uuid:
                device.on_notification(data)
                break

    def _update_status(self):
        if self.ble.is_connected:
            mqtt_status = "🟢 MQTT" if self.mqtt_service.is_connected else "⚪ MQTT"
            log_status = "🔴 REC" if self.data_logger.is_logging else "⚪ REC"
            self.status.showMessage(f"🟢 BLE подключено | {mqtt_status} | {log_status}")
        else:
            self.status.showMessage("⚪ Отключено")

    def _apply_theme(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e2e; color: #fff; }
            QTabWidget::pane { border: 1px solid #444; background: #1e1e2e; }
            QTabBar::tab { 
                background: #2a2a3e; color: #aaa; 
                padding: 10px 20px; margin: 2px;
                border-top-left-radius: 5px; border-top-right-radius: 5px;
            }
            QTabBar::tab:selected { background: #3a3a5e; color: #fff; }
            QGroupBox { 
                color: #fff; border: 1px solid #444; 
                border-radius: 5px; margin-top: 10px; padding-top: 15px;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QPushButton { 
                background-color: #3a3a5e; color: #fff; 
                border: none; padding: 8px 15px; border-radius: 5px;
            }
            QPushButton:hover { background-color: #4a4a7e; }
            QPushButton:pressed { background-color: #2a2a4e; }
            QLineEdit, QListWidget, QTextEdit, QSpinBox { 
                background-color: #2a2a3e; color: #fff; 
                border: 1px solid #444; padding: 5px; border-radius: 3px;
            }
            QLabel { color: #fff; }
            QSlider::groove:horizontal { background: #444; height: 8px; border-radius: 4px; }
            QSlider::handle:horizontal { background: #66ccff; width: 18px; margin: -5px 0; border-radius: 9px; }
            QCheckBox { color: #fff; spacing: 8px; }
        """)

    def closeEvent(self, event):
        from PyQt6.QtWidgets import QMessageBox
        from PyQt6.QtCore import QTimer

        reply = QMessageBox.question(
            self, 'Выход', 'Завершить работу?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            event.ignore()
            return

        event.accept()  # Закрываем окно сразу

        # Отключаем уведомления (не блокируется)
        self.notifier.enabled = False

        # Останавливаем логгер
        if self.data_logger.is_logging:
            try:
                self.data_logger.stop_session()
            except Exception:
                pass

        # Отключаем MQTT синхронно (без ожидания ответа)
        try:
            self.mqtt_service.disconnect()
        except Exception:
            pass

        # Останавливаем BLE — неблокирующе
        try:
            if self.ble.is_connected:
                # Отправляем команду отключения в поток
                future = self.worker.submit(self.ble.disconnect())
                # Ждём максимум 2 секунды
                try:
                    future.result(timeout=2.0)
                except Exception:
                    pass
        except Exception:
            pass

        # Корректно останавливаем async worker
        try:
            self.worker.stop()
            # Ждём завершения потока максимум 3 секунды
            if not self.worker.wait(3000):
                # Если не завершился — принудительно завершаем
                self.worker.terminate()
                self.worker.wait(1000)
        except Exception:
            pass

        # Принудительный выход через 5 секунд (на случай зависания)
        QTimer.singleShot(5000, QCoreApplication.quit)