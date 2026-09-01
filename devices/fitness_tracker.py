from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from devices.base_device import BaseDevice
from ui.widgets.real_time_plot import RealTimePlot


class FitnessTrackerDevice(BaseDevice):
    DEVICE_NAME = "Polar H10"
    SERVICE_UUID = "f000180d-0451-4000-b000-000000000000"
    CHAR_UUID = "f0002a37-0451-4000-b000-000000000000"
    ICON = "💓"
    DEVICE_TYPE = "fitness_tracker"

    def init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel(f"{self.ICON} {self.DEVICE_NAME}")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #ff6b9d;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.hr_label = QLabel("-- bpm")
        self.hr_label.setStyleSheet("font-size: 72px; font-weight: bold; color: #ff3366;")
        self.hr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.hr_label)

        stats = QHBoxLayout()
        self.min_label = self._stat_box("MIN", "--")
        self.avg_label = self._stat_box("AVG", "--")
        self.max_label = self._stat_box("MAX", "--")
        stats.addWidget(self.min_label)
        stats.addWidget(self.avg_label)
        stats.addWidget(self.max_label)
        layout.addLayout(stats)

        self.plot = RealTimePlot(
            title="Пульс в реальном времени",
            y_label="BPM",
            max_points=60,
            color=(255, 51, 102)
        )
        self.plot.set_range(40, 180)
        layout.addWidget(self.plot)

        self._values = []

    def _stat_box(self, title, value):
        from PyQt6.QtWidgets import QGroupBox
        box = QGroupBox(title)
        box_layout = QVBoxLayout(box)
        label = QLabel(value)
        label.setStyleSheet("font-size: 32px; font-weight: bold; color: #fff;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setObjectName(f"stat_{title.lower()}")
        box_layout.addWidget(label)
        return box

    def on_notification(self, data: bytes):
        if len(data) >= 2 and data[0] == 0x00:
            hr = data[1]
            self._values.append(hr)

            # Обновляем UI
            self.hr_label.setText(f"{hr} bpm")
            self.plot.add_point(hr)

            if self._values:
                self.min_label.findChild(QLabel, "stat_min").setText(str(min(self._values)))
                self.avg_label.findChild(QLabel, "stat_avg").setText(
                    str(int(sum(self._values) / len(self._values))))
                self.max_label.findChild(QLabel, "stat_max").setText(str(max(self._values)))

            # 🆕 Интеграция с сервисами
            raw_hex = data.hex(' ')
            self.log_metric("heart_rate", hr, unit="bpm", raw_hex=raw_hex)
            self.publish_metric("heart_rate", hr, unit="bpm",
                                device_class=None, icon="mdi:heart-pulse")
            if self.notifier:
                self.notifier.check_heart_rate(self.DEVICE_NAME, hr)