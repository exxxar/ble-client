from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QSlider, QGroupBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor
from devices.base_device import BaseDevice


class SmartBulbDevice(BaseDevice):
    DEVICE_NAME = "Yeelight Bulb"
    SERVICE_UUID = "f0002000-0451-4000-b000-000000000000"
    CHAR_UUID = "f0002001-0451-4000-b000-000000000000"
    ICON = "💡"

    def init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel(f"{self.ICON} {self.DEVICE_NAME}")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffcc00;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Превью цвета
        self.preview = QWidget()
        self.preview.setMinimumHeight(150)
        self.preview.setStyleSheet("background-color: rgb(255, 200, 100); border-radius: 10px;")
        layout.addWidget(self.preview)

        # Питание
        power = QHBoxLayout()
        self.btn_on = QPushButton("💡 ВКЛ")
        self.btn_off = QPushButton("🌑 ВЫКЛ")
        self.btn_on.setMinimumHeight(50)
        self.btn_off.setMinimumHeight(50)
        self.btn_on.clicked.connect(lambda: self.send_command("0101"))
        self.btn_off.clicked.connect(lambda: self.send_command("0100"))
        power.addWidget(self.btn_on)
        power.addWidget(self.btn_off)
        layout.addLayout(power)

        # Яркость
        bright_group = QGroupBox("Яркость")
        bright_layout = QHBoxLayout(bright_group)
        self.bright_slider = QSlider(Qt.Orientation.Horizontal)
        self.bright_slider.setRange(0, 100)
        self.bright_slider.setValue(100)
        self.bright_label = QLabel("100%")
        self.bright_slider.valueChanged.connect(self._on_brightness_changed)
        bright_layout.addWidget(self.bright_slider)
        bright_layout.addWidget(self.bright_label)
        layout.addWidget(bright_group)

        # Цвет RGB
        color_group = QGroupBox("Цвет (RGB)")
        color_layout = QVBoxLayout(color_group)

        self.sliders = {}
        for name, default, color in [("R", 255, "#ff4444"),
                                     ("G", 200, "#44ff44"),
                                     ("B", 100, "#4444ff")]:
            row = QHBoxLayout()
            row.addWidget(QLabel(f"<b style='color:{color}'>{name}:</b>"))
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, 255)
            slider.setValue(default)
            slider.valueChanged.connect(self._on_color_changed)
            self.sliders[name] = slider
            row.addWidget(slider)
            color_layout.addLayout(row)

        layout.addWidget(color_group)

        # Пресеты цветов
        presets = QHBoxLayout()
        preset_colors = [
            ("Красный", "03FF0000"), ("Зелёный", "0300FF00"),
            ("Синий", "030000FF"), ("Белый", "03FFFFFF"),
            ("Тёплый", "03FFAA55"), ("Холодный", "0355AAFF"),
        ]
        for name, cmd in preset_colors:
            btn = QPushButton(name)
            btn.clicked.connect(lambda _, c=cmd: self.send_command(c))
            presets.addWidget(btn)
        layout.addLayout(presets)

    def _on_brightness_changed(self, value):
        self.bright_label.setText(f"{value}%")
        hex_val = f"{value:02X}"
        self.send_command(f"02{hex_val}")

    def _on_color_changed(self, value):
        r = self.sliders["R"].value()
        g = self.sliders["G"].value()
        b = self.sliders["B"].value()
        self.preview.setStyleSheet(f"background-color: rgb({r}, {g}, {b}); border-radius: 10px;")
        self.send_command(f"03{r:02X}{g:02X}{b:02X}")

    def on_notification(self, data: bytes):
        if len(data) >= 5:
            is_on = data[0] != 0
            brightness = data[1]
            r, g, b = data[2], data[3], data[4]

            # Обновляем UI
            self.bright_slider.blockSignals(True)
            self.bright_slider.setValue(brightness)
            self.bright_slider.blockSignals(False)
            self.bright_label.setText(f"{brightness}%")

            self.sliders["R"].blockSignals(True)
            self.sliders["G"].blockSignals(True)
            self.sliders["B"].blockSignals(True)
            self.sliders["R"].setValue(r)
            self.sliders["G"].setValue(g)
            self.sliders["B"].setValue(b)
            self.sliders["R"].blockSignals(False)
            self.sliders["G"].blockSignals(False)
            self.sliders["B"].blockSignals(False)

            self.preview.setStyleSheet(f"background-color: rgb({r}, {g}, {b}); border-radius: 10px;")