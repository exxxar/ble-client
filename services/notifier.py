from PyQt6.QtCore import QObject, pyqtSignal
from plyer import notification
import platform


class Notifier(QObject):
    """Системные уведомления с настраиваемыми порогами"""

    notification_sent = pyqtSignal(str, str)  # title, message

    def __init__(self):
        super().__init__()
        self.enabled = True
        self.cooldown_seconds = 60  # Минимум секунд между уведомлениями одного типа
        self._last_notification = {}  # key -> timestamp

        # Пороги по умолчанию
        self.thresholds = {
            "heart_rate_high": 160,  # bpm
            "heart_rate_low": 40,  # bpm
            "temperature_high": 30,  # °C
            "temperature_low": 16,  # °C
            "battery_low": 20,  # %
            "lock_failed_attempts": 3,  # попытки
        }

    def configure(self, enabled=True, cooldown=60, thresholds=None):
        """Настроить уведомления"""
        self.enabled = enabled
        self.cooldown_seconds = cooldown
        if thresholds:
            self.thresholds.update(thresholds)

    def notify(self, title: str, message: str, key: str = None,
               icon: str = None, urgent: bool = False):
        """
        Отправить уведомление

        :param title: заголовок
        :param message: текст
        :param key: уникальный ключ (для cooldown)
        :param icon: путь к иконке (опционально)
        :param urgent: срочное уведомление
        """
        if not self.enabled:
            return

        # Проверка cooldown
        if key:
            import time
            now = time.time()
            last = self._last_notification.get(key, 0)
            if now - last < self.cooldown_seconds:
                return
            self._last_notification[key] = now

        try:
            notification.notify(
                title=title,
                message=message,
                app_name="BLE Device Client",
                app_icon=icon,
                timeout=10,
            )
            self.notification_sent.emit(title, message)
        except Exception as e:
            # Fallback: просто логируем
            print(f"[Notifier] {title}: {message} (ошибка: {e})")

    # === Специализированные методы для устройств ===

    def check_heart_rate(self, device_name: str, bpm: int):
        """Проверить пульс и уведомить при превышении"""
        if bpm > self.thresholds["heart_rate_high"]:
            self.notify(
                title=f"💓 Высокий пульс — {device_name}",
                message=f"Пульс {bpm} bpm превышает порог {self.thresholds['heart_rate_high']} bpm!",
                key=f"hr_high_{device_name}",
                urgent=True
            )
        elif bpm < self.thresholds["heart_rate_low"] and bpm > 0:
            self.notify(
                title=f"💓 Низкий пульс — {device_name}",
                message=f"Пульс {bpm} bpm ниже порога {self.thresholds['heart_rate_low']} bpm!",
                key=f"hr_low_{device_name}",
                urgent=True
            )

    def check_temperature(self, device_name: str, temp: float):
        """Проверить температуру"""
        if temp > self.thresholds["temperature_high"]:
            self.notify(
                title=f"🌡️ Высокая температура — {device_name}",
                message=f"Температура {temp:.1f}°C превышает порог!",
                key=f"temp_high_{device_name}"
            )
        elif temp < self.thresholds["temperature_low"]:
            self.notify(
                title=f"🌡️ Низкая температура — {device_name}",
                message=f"Температура {temp:.1f}°C ниже порога!",
                key=f"temp_low_{device_name}"
            )

    def check_battery(self, device_name: str, percent: int):
        """Проверить заряд батареи"""
        if percent <= self.thresholds["battery_low"]:
            self.notify(
                title=f"🔋 Низкий заряд — {device_name}",
                message=f"Осталось {percent}%. Подключите зарядку!",
                key=f"battery_{device_name}",
                urgent=True
            )

    def check_lock_security(self, device_name: str, failed_attempts: int):
        """Проверить безопасность замка"""
        if failed_attempts >= self.thresholds["lock_failed_attempts"]:
            self.notify(
                title=f"🔒 ⚠️ ВНИМАНИЕ — {device_name}",
                message=f"Превышено число попыток ввода PIN ({failed_attempts})!",
                key=f"lock_security_{device_name}",
                urgent=True
            )