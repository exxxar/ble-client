import struct
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox
from PyQt6.QtCore import Qt
from devices.base_device import BaseDevice
from ui.widgets.real_time_plot import RealTimePlot


class HomeSensorDevice(BaseDevice):
    DEVICE_NAME = "Xiaomi Temp"
    SERVICE_UUID = "f0001809-0451-4000-b000-000000000000"
    CHAR_UUID = "f0002a1c-0451-4000-b000-000000000000"
    ICON = "🌡️"

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Заголовок
        title = QLabel(f"{self.ICON} {self.DEVICE_NAME}")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #66ff99;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Большая цифра температуры
        self.temp_label = QLabel("--.-°C")
        self.temp_label.setStyleSheet("font-size: 96px; font-weight: bold; color: #66ff99;")
        self.temp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.temp_label)

        # Статистика
        stats = QHBoxLayout()
        self.min_label = self._stat_box("МИН", "--.-°C", "#66ccff")
        self.avg_label = self._stat_box("СРЕД", "--.-°C", "#ffcc66")
        self.max_label = self._stat_box("МАКС", "--.-°C", "#ff6666")
        stats.addWidget(self.min_label)
        stats.addWidget(self.avg_label)
        stats.addWidget(self.max_label)
        layout.addLayout(stats)

        # График температуры
        self.plot = RealTimePlot(
            title="Температура в реальном времени",
            y_label="°C",
            max_points=120,
            color=(102, 255, 153)
        )
        self.plot.set_range(15, 35)
        layout.addWidget(self.plot)

        # Комфорт-зона
        comfort = QGroupBox("Комфортная зона")
        comfort_layout = QVBoxLayout(comfort)
        self.comfort_label = QLabel("—")
        self.comfort_label.setStyleSheet("font-size: 18px; padding: 10px;")
        self.comfort_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        comfort_layout.addWidget(self.comfort_label)
        layout.addWidget(comfort)

        self._values = []

    def _stat_box(self, title, value, color):
        box = QGroupBox(title)
        box_layout = QVBoxLayout(box)
        label = QLabel(value)
        label.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {color};")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setObjectName(f"stat_{title}")
        box_layout.addWidget(label)
        return box

    def _get_comfort(self, temp):
        if temp < 16:
            return "❄️ Холодно", "#66ccff"
        elif temp < 20:
            return "🌡️ Прохладно", "#88ddaa"
        elif temp < 25:
            return "✅ Комфортно", "#66ff66"
        elif temp < 28:
            return "🌡️ Тепло", "#ffcc66"
        else:
            return "🔥 Жарко", "#ff6666"

    def on_notification(self, data: bytes):
        if len(data) < 5:
            return

        # Формат: [flags (1), temp_int32 (4)] — temp_int32 = temp * 100
        temp_int = struct.unpack('<i', data[1:5])[0]
        temp = temp_int / 100.0

        self._values.append(temp)

        # Обновляем UI
        self.temp_label.setText(f"{temp:.1f}°C")
        self.plot.add_point(temp)

        # Статистика
        if self._values:
            min_v = min(self._values)
            max_v = max(self._values)
            avg_v = sum(self._values) / len(self._values)

            self.min_label.findChild(QLabel, "stat_МИН").setText(f"{min_v:.1f}°C")
            self.avg_label.findChild(QLabel, "stat_СРЕД").setText(f"{avg_v:.1f}°C")
            self.max_label.findChild(QLabel, "stat_МАКС").setText(f"{max_v:.1f}°C")

            # Комфорт
            comfort_text, comfort_color = self._get_comfort(temp)
            self.comfort_label.setText(comfort_text)
            self.comfort_label.setStyleSheet(
                f"font-size: 18px; padding: 10px; color: {comfort_color}; font-weight: bold;")

            self.log_metric("temperature", temp, unit="°C", raw_hex=data.hex(' '))
            self.publish_metric("temperature", temp, unit="°C",
                                device_class="temperature", icon="mdi:thermometer")
            if self.notifier:
                self.notifier.check_temperature(self.DEVICE_NAME, temp)