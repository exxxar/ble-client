from PyQt6.QtWidgets import QWidget
from services.data_logger import DataLogger
from services.notifier import Notifier
from services.mqtt_service import MQTTService


class BaseDevice(QWidget):
    """Базовый класс для вкладки устройства"""

    DEVICE_NAME = "Unknown"
    SERVICE_UUID = ""
    CHAR_UUID = ""
    ICON = "📱"
    DEVICE_TYPE = "generic"  # для логирования

    def __init__(self, ble_manager, async_worker, parent=None):
        super().__init__(parent)
        self.ble = ble_manager
        self.worker = async_worker
        self.is_active = False

        # Сервисы (устанавливаются из MainWindow)
        self.data_logger: DataLogger = None
        self.notifier: Notifier = None
        self.mqtt: MQTTService = None

        self.init_ui()

    def init_ui(self):
        pass

    def on_activated(self):
        self.is_active = True
        if self.CHAR_UUID and self.ble.is_connected:
            self.worker.submit(self.ble.subscribe(self.CHAR_UUID))

    def on_deactivated(self):
        self.is_active = False

    def on_notification(self, data: bytes):
        """Обработка входящих данных — переопределить в наследниках"""
        pass

    def send_command(self, hex_cmd: str):
        """Отправить команду"""
        if not self.CHAR_UUID:
            return
        try:
            data = bytes.fromhex(hex_cmd.replace(' ', ''))
            self.worker.submit(self.ble.write(self.CHAR_UUID, data))
        except ValueError as e:
            self.ble.log.emit(f"❌ Неверная команда: {e}")

    # === Методы для сервисов ===

    def log_metric(self, metric: str, value, unit: str = "", raw_hex: str = ""):
        """Записать метрику в CSV"""
        if self.data_logger and self.data_logger.is_logging:
            self.data_logger.log(
                device_name=self.DEVICE_NAME,
                device_type=self.DEVICE_TYPE,
                metric=metric,
                value=value,
                unit=unit,
                raw_hex=raw_hex
            )

    def publish_metric(self, metric: str, value, unit: str = "",
                       device_class: str = None, icon: str = None):
        """Опубликовать метрику в MQTT"""
        if self.mqtt and self.mqtt.is_connected:
            # Регистрируем сенсор (один раз)
            self.mqtt.register_sensor(
                device_name=self.DEVICE_NAME,
                metric=metric,
                unit=unit,
                device_class=device_class,
                icon=icon
            )
            # Публикуем значение
            self.mqtt.publish_value(self.DEVICE_NAME, metric, value)