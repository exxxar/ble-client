from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QGroupBox, QTextEdit)
from PyQt6.QtCore import Qt
from devices.base_device import BaseDevice
from ui.widgets.real_time_plot import RealTimePlot
from ui.widgets.gauge_widget import GaugeWidget


class SmartWatchDevice(BaseDevice):
    DEVICE_NAME = "Galaxy Watch"
    SERVICE_UUID = "f0009000-0451-4000-b000-000000000000"
    CHAR_UUID = "f0009001-0451-4000-b000-000000000000"
    ICON = "⌚"

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Заголовок
        title = QLabel(f"{self.ICON} {self.DEVICE_NAME}")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #aa88ff;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Верхняя часть: пульс + шаги
        top = QHBoxLayout()

        # Пульс (gauge)
        self.hr_gauge = GaugeWidget(
            title="Пульс",
            min_val=40, max_val=180,
            unit=" bpm",
            color="#ff3366"
        )
        top.addWidget(self.hr_gauge)

        # Шаги (gauge, цель 10000)
        self.steps_gauge = GaugeWidget(
            title="Шаги",
            min_val=0, max_val=10000,
            unit="",
            color="#66ff66"
        )
        top.addWidget(self.steps_gauge)

        layout.addLayout(top)

        # Цифровые значения
        values = QHBoxLayout()
        self.hr_label = QLabel("-- bpm")
        self.hr_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #ff3366;")
        self.hr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.steps_label = QLabel("0")
        self.steps_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #66ff66;")
        self.steps_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        values.addWidget(self.hr_label)
        values.addWidget(self.steps_label)
        layout.addLayout(values)

        # График пульса
        self.hr_plot = RealTimePlot(
            title="Пульс в реальном времени",
            y_label="BPM",
            max_points=60,
            color=(255, 51, 102)
        )
        self.hr_plot.set_range(40, 180)
        layout.addWidget(self.hr_plot)

        # Зоны пульса
        zones = QGroupBox("💪 Пульсовая зона")
        zones_layout = QVBoxLayout(zones)
        self.zone_label = QLabel("—")
        self.zone_label.setStyleSheet("font-size: 20px; padding: 10px;")
        self.zone_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        zones_layout.addWidget(self.zone_label)
        layout.addWidget(zones)

        # Отправка уведомлений на часы
        notify_group = QGroupBox("📱 Отправить уведомление на часы")
        notify_layout = QVBoxLayout(notify_group)

        input_row = QHBoxLayout()
        self.msg_input = QLineEdit()
        self.msg_input.setPlaceholderText("Введите текст сообщения...")
        self.msg_input.setMinimumHeight(40)
        self.btn_send = QPushButton("📤 Отправить")
        self.btn_send.setMinimumHeight(40)
        self.btn_send.clicked.connect(self._on_send_message)

        input_row.addWidget(self.msg_input)
        input_row.addWidget(self.btn_send)
        notify_layout.addLayout(input_row)

        # Быстрые сообщения
        quick = QHBoxLayout()
        quick_messages = [
            ("📞 Звонок", "Звонки от мамы"),
            ("💬 SMS", "Где ты?"),
            ("📧 Email", "Новое письмо"),
            ("⏰ Напоминание", "Встреча в 15:00"),
        ]
        for icon, text in quick_messages:
            btn = QPushButton(f"{icon} {text}")
            btn.clicked.connect(lambda _, t=text: self._send_quick(t))
            quick.addWidget(btn)
        notify_layout.addLayout(quick)

        layout.addWidget(notify_group)

        # Лог полученных уведомлений
        layout.addWidget(QLabel("📋 История:"))
        self.history = QTextEdit()
        self.history.setReadOnly(True)
        self.history.setMaximumHeight(150)
        layout.addWidget(self.history)

        # Состояние
        self._hr_values = []

    def _get_hr_zone(self, hr):
        """Определение пульсовой зоны (для возраста ~30 лет, макс ~190)"""
        if hr < 100:
            return "🟢 Разминка (<100 bpm)", "#66ff66"
        elif hr < 130:
            return "🟡 Жиросжигание (100-130 bpm)", "#ffcc66"
        elif hr < 155:
            return "🟠 Аэробная (130-155 bpm)", "#ff9966"
        elif hr < 175:
            return "🔴 Анаэробная (155-175 bpm)", "#ff6666"
        else:
            return "⚠️ Максимальная (>175 bpm)", "#ff3333"

    def _send_quick(self, text):
        """Отправить быстрое сообщение"""
        data = text.encode('utf-8')
        self.worker.submit(self.ble.write(self.CHAR_UUID, data, response=False))
        self._add_history(f"📤 → {text}", "#66ccff")

    def _on_send_message(self):
        text = self.msg_input.text().strip()
        if not text:
            return
        self._send_quick(text)
        self.msg_input.clear()

    def _add_history(self, text, color="#fff"):
        import datetime
        time = datetime.datetime.now().strftime("%H:%M:%S")
        self.history.append(f'<span style="color:{color}">[{time}] {text}</span>')

    def on_notification(self, data: bytes):
        if len(data) < 6:
            return

        # Формат: [flags(1), hr(1), steps(4)]
        hr = data[1]
        steps = int.from_bytes(data[2:6], 'little')

        self._hr_values.append(hr)

        # Обновляем gauge и цифры
        self.hr_gauge.set_value(hr)
        self.steps_gauge.set_value(steps)

        self.hr_label.setText(f"{hr} bpm")
        self.steps_label.setText(f"{steps}")

        self.hr_plot.add_point(hr)

        # Пульсовая зона
        zone_text, zone_color = self._get_hr_zone(hr)
        self.zone_label.setText(zone_text)
        self.zone_label.setStyleSheet(
            f"font-size: 20px; padding: 10px; color: {zone_color}; font-weight: bold;")

        # Логируем только значимые изменения шагов
        if not hasattr(self, '_last_steps'):
            self._last_steps = steps
        elif steps != self._last_steps:
            self._add_history(f"👟 Шаги: {steps}", "#66ff66")
            self._last_steps = steps