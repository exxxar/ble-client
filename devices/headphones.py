from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox
from PyQt6.QtCore import Qt
from devices.base_device import BaseDevice
from ui.widgets.gauge_widget import GaugeWidget
from ui.widgets.real_time_plot import RealTimePlot


class HeadphonesDevice(BaseDevice):
    DEVICE_NAME = "AirPods Pro"
    SERVICE_UUID = "f000180f-0451-4000-b000-000000000000"
    CHAR_UUID = "f0002a19-0451-4000-b000-000000000000"
    ICON = "🎧"

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Заголовок
        title = QLabel(f"{self.ICON} {self.DEVICE_NAME}")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Gauge батареи
        gauge_layout = QHBoxLayout()
        self.battery_gauge = GaugeWidget(
            title="Заряд",
            min_val=0, max_val=100,
            unit="%",
            color="#66ff66"
        )
        gauge_layout.addWidget(self.battery_gauge)
        layout.addLayout(gauge_layout)

        # Цифровое значение
        self.battery_label = QLabel("--%")
        self.battery_label.setStyleSheet("font-size: 48px; font-weight: bold;")
        self.battery_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.battery_label)

        # Статус
        self.status_label = QLabel("⚪ Статус: неизвестно")
        self.status_label.setStyleSheet("font-size: 18px; padding: 10px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # График разряда
        self.plot = RealTimePlot(
            title="История заряда",
            y_label="%",
            max_points=60,
            color=(102, 255, 102)
        )
        self.plot.set_range(0, 100)
        layout.addWidget(self.plot)

        # Прогноз
        forecast = QGroupBox("⏱️ Прогноз работы")
        forecast_layout = QVBoxLayout(forecast)
        self.forecast_label = QLabel("—")
        self.forecast_label.setStyleSheet("font-size: 20px; padding: 10px;")
        self.forecast_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        forecast_layout.addWidget(self.forecast_label)
        layout.addWidget(forecast)

        self._values = []
        self._last_battery = None
        self._last_time = None

    def _get_status(self, battery):
        if battery >= 80:
            return "🟢 Полный заряд", "#66ff66"
        elif battery >= 50:
            return "🟡 Хороший заряд", "#ffcc66"
        elif battery >= 20:
            return "🟠 Средний заряд", "#ff9966"
        elif battery >= 10:
            return "🔴 Низкий заряд", "#ff6666"
        else:
            return "⚠️ Критический! Зарядите наушники", "#ff3333"

    def _estimate_time(self, battery):
        """Оценка оставшегося времени (примерно 5 часов при 100%)"""
        hours = battery * 5 / 100
        if hours < 1:
            return f"{int(hours * 60)} минут"
        return f"{hours:.1f} часов"

    def on_notification(self, data: bytes):
        if len(data) < 1:
            return

        battery = data[0]
        self._values.append(battery)

        # Обновляем gauge
        self.battery_gauge.set_value(battery)

        # Цвет gauge в зависимости от заряда
        if battery >= 50:
            self.battery_gauge.color = self.battery_gauge.color.__class__("#66ff66")
        elif battery >= 20:
            self.battery_gauge.color = self.battery_gauge.color.__class__("#ffcc66")
        else:
            self.battery_gauge.color = self.battery_gauge.color.__class__("#ff6666")
        self.battery_gauge.update()

        # Цифровое значение
        self.battery_label.setText(f"{battery}%")
        self.plot.add_point(battery)

        # Статус
        status_text, status_color = self._get_status(battery)
        self.status_label.setText(status_text)
        self.status_label.setStyleSheet(f"font-size: 18px; padding: 10px; color: {status_color};")

        # Прогноз
        self.forecast_label.setText(f"≈ {self._estimate_time(battery)} до разряда")

        self.log_metric("battery", battery, unit="%", raw_hex=data.hex(' '))
        self.publish_metric("battery", battery, unit="%",
                            device_class="battery", icon="mdi:bluetooth")
        if self.notifier:
            self.notifier.check_battery(self.DEVICE_NAME, battery)