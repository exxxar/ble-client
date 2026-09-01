import time
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox
from PyQt6.QtCore import Qt
from devices.base_device import BaseDevice
from ui.widgets.gauge_widget import GaugeWidget
from ui.widgets.real_time_plot import RealTimePlot


class CyclingSensorDevice(BaseDevice):
    DEVICE_NAME = "Wahoo KICKR"
    SERVICE_UUID = "f0001816-0451-4000-b000-000000000000"
    CHAR_UUID = "f0002a5b-0451-4000-b000-000000000000"
    ICON = "🚴"

    # Окружность колеса (стандарт 700c) в метрах
    WHEEL_CIRCUMFERENCE = 2.1

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Заголовок
        title = QLabel(f"{self.ICON} {self.DEVICE_NAME}")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #ff9933;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Два gauge: скорость и каденс
        gauges = QHBoxLayout()
        self.speed_gauge = GaugeWidget(
            title="Скорость",
            min_val=0, max_val=60,
            unit=" км/ч",
            color="#ff9933"
        )
        self.cadence_gauge = GaugeWidget(
            title="Каденс",
            min_val=0, max_val=150,
            unit=" об/мин",
            color="#66ccff"
        )
        gauges.addWidget(self.speed_gauge)
        gauges.addWidget(self.cadence_gauge)
        layout.addLayout(gauges)

        # Цифровые значения
        values = QHBoxLayout()
        self.speed_label = QLabel("0.0 км/ч")
        self.speed_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #ff9933;")
        self.speed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.cadence_label = QLabel("0 об/мин")
        self.cadence_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #66ccff;")
        self.cadence_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        values.addWidget(self.speed_label)
        values.addWidget(self.cadence_label)
        layout.addLayout(values)

        # График скорости
        self.speed_plot = RealTimePlot(
            title="Скорость",
            y_label="км/ч",
            max_points=60,
            color=(255, 153, 51)
        )
        self.speed_plot.set_range(0, 60)
        layout.addWidget(self.speed_plot)

        # Статистика поездки
        stats = QGroupBox("📊 Статистика поездки")
        stats_layout = QHBoxLayout(stats)
        self.distance_label = self._stat_item("Дистанция", "0.00 км")
        self.avg_speed_label = self._stat_item("Ср. скорость", "0.0 км/ч")
        self.max_speed_label = self._stat_item("Макс. скорость", "0.0 км/ч")
        self.calories_label = self._stat_item("Калории", "~0 ккал")

        stats_layout.addWidget(self.distance_label)
        stats_layout.addWidget(self.avg_speed_label)
        stats_layout.addWidget(self.max_speed_label)
        stats_layout.addWidget(self.calories_label)
        layout.addWidget(stats)

        # Состояние
        self._last_wheel_rev = None
        self._last_crank_rev = None
        self._last_time = None
        self._total_distance = 0.0
        self._speeds = []
        self._start_time = time.time()

    def _stat_item(self, title, value):
        box = QGroupBox(title)
        box_layout = QVBoxLayout(box)
        label = QLabel(value)
        label.setStyleSheet("font-size: 20px; font-weight: bold; color: #fff;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setObjectName(f"stat_{title}")
        box_layout.addWidget(label)
        return box

    def on_notification(self, data: bytes):
        if len(data) < 11:
            return

        # Формат CSC Measurement:
        # [flags(1), wheel_rev(4), wheel_time(2), crank_rev(2), crank_time(2)]
        flags = data[0]
        wheel_rev = int.from_bytes(data[1:5], 'little')
        wheel_time = int.from_bytes(data[5:7], 'little')  # 1/1024 сек
        crank_rev = int.from_bytes(data[7:9], 'little')
        crank_time = int.from_bytes(data[9:11], 'little')

        current_time = time.time()

        speed_kmh = 0.0
        cadence_rpm = 0.0

        # Считаем скорость (если есть предыдущее значение)
        if self._last_wheel_rev is not None and self._last_time is not None:
            wheel_delta = wheel_rev - self._last_wheel_rev
            time_delta = current_time - self._last_time

            if time_delta > 0 and wheel_delta >= 0:
                # Расстояние в метрах
                distance = wheel_delta * self.WHEEL_CIRCUMFERENCE
                self._total_distance += distance

                # Скорость в км/ч
                speed_kmh = (distance / time_delta) * 3.6
                speed_kmh = max(0, min(speed_kmh, 100))  # ограничение
                self._speeds.append(speed_kmh)

        # Считаем каденс
        if self._last_crank_rev is not None and self._last_time is not None:
            crank_delta = crank_rev - self._last_crank_rev
            time_delta = current_time - self._last_time

            if time_delta > 0 and crank_delta >= 0:
                cadence_rpm = (crank_delta / time_delta) * 60
                cadence_rpm = max(0, min(cadence_rpm, 200))

        # Сохраняем текущие значения
        self._last_wheel_rev = wheel_rev
        self._last_crank_rev = crank_rev
        self._last_time = current_time

        # Обновляем UI
        self.speed_gauge.set_value(speed_kmh)
        self.cadence_gauge.set_value(cadence_rpm)

        self.speed_label.setText(f"{speed_kmh:.1f} км/ч")
        self.cadence_label.setText(f"{int(cadence_rpm)} об/мин")

        self.speed_plot.add_point(speed_kmh)

        # Статистика
        self.distance_label.findChild(QLabel, "stat_Дистанция").setText(
            f"{self._total_distance / 1000:.2f} км")

        if self._speeds:
            avg_speed = sum(self._speeds) / len(self._speeds)
            max_speed = max(self._speeds)
            self.avg_speed_label.findChild(QLabel, "stat_Ср. скорость").setText(
                f"{avg_speed:.1f} км/ч")
            self.max_speed_label.findChild(QLabel, "stat_Макс. скорость").setText(
                f"{max_speed:.1f} км/ч")

            # Калории: примерно 0.3 ккал на км (упрощённо)
            calories = int(self._total_distance / 1000 * 30)
            self.calories_label.findChild(QLabel, "stat_Калории").setText(
                f"~{calories} ккал")