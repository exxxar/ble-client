from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QGroupBox, QTextEdit)
from PyQt6.QtCore import Qt
from devices.base_device import BaseDevice


class SmartLockDevice(BaseDevice):
    DEVICE_NAME = "Aqara Lock"
    SERVICE_UUID = "f0003000-0451-4000-b000-000000000000"
    CHAR_UUID = "f0003001-0451-4000-b000-000000000000"
    ICON = "🔒"

    def init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel(f"{self.ICON} {self.DEVICE_NAME}")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #66ccff;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Статус замка
        self.status_label = QLabel("🔒 ЗАКРЫТ")
        self.status_label.setStyleSheet("font-size: 48px; font-weight: bold; color: #ff6666;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setMinimumHeight(100)
        layout.addWidget(self.status_label)

        # Аутентификация
        auth_group = QGroupBox("🔑 Аутентификация")
        auth_layout = QHBoxLayout(auth_group)
        self.pin_input = QLineEdit()
        self.pin_input.setPlaceholderText("Введите PIN (по умолчанию: 1234)")
        self.pin_input.setMaxLength(10)
        self.btn_auth = QPushButton("Войти")
        self.btn_auth.clicked.connect(self._on_auth)
        auth_layout.addWidget(self.pin_input)
        auth_layout.addWidget(self.btn_auth)
        layout.addWidget(auth_group)

        # Управление
        control = QHBoxLayout()
        self.btn_open = QPushButton("🔓 Открыть")
        self.btn_close = QPushButton("🔒 Закрыть")
        self.btn_open.setMinimumHeight(60)
        self.btn_close.setMinimumHeight(60)
        self.btn_open.clicked.connect(lambda: self.send_command("20"))
        self.btn_close.clicked.connect(lambda: self.send_command("21"))
        control.addWidget(self.btn_open)
        control.addWidget(self.btn_close)
        layout.addLayout(control)

        # Лог событий
        layout.addWidget(QLabel("📋 Лог событий:"))
        self.event_log = QTextEdit()
        self.event_log.setReadOnly(True)
        self.event_log.setMaximumHeight(200)
        layout.addWidget(self.event_log)

        self._authenticated = False

    def _on_auth(self):
        pin = self.pin_input.text()
        if not pin:
            pin = "1234"
        hex_cmd = "10" + pin.encode().hex()
        self.send_command(hex_cmd)

    def _add_event(self, text, color="#fff"):
        import datetime
        time = datetime.datetime.now().strftime("%H:%M:%S")
        self.event_log.append(f'<span style="color:{color}">[{time}] {text}</span>')

    def on_notification(self, data: bytes):
        if len(data) >= 2:
            code = data[0]
            is_locked = data[1] != 0

            # Обновляем статус
            if is_locked:
                self.status_label.setText("🔒 ЗАКРЫТ")
                self.status_label.setStyleSheet("font-size: 48px; font-weight: bold; color: #ff6666;")
            else:
                self.status_label.setText("🔓 ОТКРЫТ")
                self.status_label.setStyleSheet("font-size: 48px; font-weight: bold; color: #66ff66;")

            # Логируем ответ
            if code == 0x00:
                self._add_event("✓ Операция успешна", "#66ff66")
            elif code == 0xE1:
                self._add_event("✗ PIN не указан", "#ff6666")
            elif code == 0xE2:
                self._add_event("✗ Неверный PIN", "#ff6666")
            elif code == 0xE3:
                self._add_event("⚠ Замок заблокирован!", "#ffaa00")
            elif code == 0xE4:
                self._add_event("✗ Требуется аутентификация", "#ff6666")

            self.log_metric("lock_state", 1 if is_locked else 0, raw_hex=data.hex(' '))
            self.publish_metric("lock_state", "locked" if is_locked else "unlocked",
                                icon="mdi:lock")
            if self.notifier and len(data) >= 2:
                if data[0] in (0xE2, 0xE3):  # Неверный PIN или блокировка
                    self.notifier.check_lock_security(self.DEVICE_NAME, 3)