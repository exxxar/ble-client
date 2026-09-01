from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QGroupBox, QLineEdit, QSpinBox,
                             QCheckBox, QFileDialog, QComboBox)
from PyQt6.QtCore import Qt
from services import DataLogger, ChartExporter, MQTTService, Notifier


class ServicesTab(QWidget):
    def __init__(self, data_logger, chart_exporter, mqtt_service,
                 notifier, device_tabs, parent=None):
        super().__init__(parent)
        self.data_logger = data_logger
        self.chart_exporter = chart_exporter
        self.mqtt_service = mqtt_service
        self.notifier = notifier
        self.device_tabs = device_tabs
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("⚙️ Управление сервисами")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffcc66;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # === 1. CSV Логгер ===
        csv_group = QGroupBox("📊 Экспорт данных в CSV")
        csv_layout = QVBoxLayout(csv_group)

        self.btn_start_log = QPushButton("▶️ Начать запись")
        self.btn_stop_log = QPushButton("⏹️ Остановить запись")
        self.btn_stop_log.setEnabled(False)

        log_btn_layout = QHBoxLayout()
        log_btn_layout.addWidget(self.btn_start_log)
        log_btn_layout.addWidget(self.btn_stop_log)
        csv_layout.addLayout(log_btn_layout)

        self.log_status = QLabel("⚪ Не записывается")
        csv_layout.addWidget(self.log_status)

        self.btn_open_csv_folder = QPushButton("📂 Открыть папку с CSV")
        csv_layout.addWidget(self.btn_open_csv_folder)

        layout.addWidget(csv_group)

        # === 2. Экспорт графиков ===
        chart_group = QGroupBox("📈 Экспорт графиков в PNG")
        chart_layout = QVBoxLayout(chart_group)

        chart_row = QHBoxLayout()
        chart_row.addWidget(QLabel("Устройство:"))
        self.device_combo = QComboBox()
        for name in self.device_tabs:
            self.device_combo.addItem(name)
        chart_row.addWidget(self.device_combo)

        self.btn_export_chart = QPushButton("📸 Экспортировать график")
        chart_row.addWidget(self.btn_export_chart)
        chart_layout.addLayout(chart_row)

        self.btn_export_all = QPushButton("📁 Экспортировать все графики")
        chart_layout.addWidget(self.btn_export_all)

        self.btn_open_charts_folder = QPushButton("📂 Открыть папку с графиками")
        chart_layout.addWidget(self.btn_open_charts_folder)

        layout.addWidget(chart_group)

        # === 3. MQTT ===
        mqtt_group = QGroupBox("🏠 MQTT / Home Assistant")
        mqtt_layout = QVBoxLayout(mqtt_group)

        mqtt_row1 = QHBoxLayout()
        mqtt_row1.addWidget(QLabel("Хост:"))
        self.mqtt_host = QLineEdit("homeassistant.local")
        mqtt_row1.addWidget(self.mqtt_host)
        mqtt_row1.addWidget(QLabel("Порт:"))
        self.mqtt_port = QSpinBox()
        self.mqtt_port.setRange(1, 65535)
        self.mqtt_port.setValue(1883)
        mqtt_row1.addWidget(self.mqtt_port)
        mqtt_layout.addLayout(mqtt_row1)

        mqtt_row2 = QHBoxLayout()
        mqtt_row2.addWidget(QLabel("Логин:"))
        self.mqtt_user = QLineEdit()
        mqtt_row2.addWidget(self.mqtt_user)
        mqtt_row2.addWidget(QLabel("Пароль:"))
        self.mqtt_pass = QLineEdit()
        self.mqtt_pass.setEchoMode(QLineEdit.EchoMode.Password)
        mqtt_row2.addWidget(self.mqtt_pass)
        mqtt_layout.addLayout(mqtt_row2)

        mqtt_btn_row = QHBoxLayout()
        self.btn_mqtt_connect = QPushButton("🔗 Подключить MQTT")
        self.btn_mqtt_disconnect = QPushButton("🔌 Отключить")
        self.btn_mqtt_disconnect.setEnabled(False)
        mqtt_btn_row.addWidget(self.btn_mqtt_connect)
        mqtt_btn_row.addWidget(self.btn_mqtt_disconnect)
        mqtt_layout.addLayout(mqtt_btn_row)

        self.mqtt_status = QLabel("⚪ Отключено")
        mqtt_layout.addWidget(self.mqtt_status)

        layout.addWidget(mqtt_group)

        # === 4. Уведомления ===
        notify_group = QGroupBox("🔔 Уведомления Windows")
        notify_layout = QVBoxLayout(notify_group)

        self.chk_enable_notify = QCheckBox("Включить уведомления")
        self.chk_enable_notify.setChecked(True)
        notify_layout.addWidget(self.chk_enable_notify)

        notify_layout.addWidget(QLabel("<b>Пороги срабатывания:</b>"))

        thresholds_layout = QHBoxLayout()

        # Пульс
        thr_hr = QVBoxLayout()
        thr_hr.addWidget(QLabel("💓 Пульс (bpm):"))
        self.spin_hr_high = QSpinBox()
        self.spin_hr_high.setRange(100, 220)
        self.spin_hr_high.setValue(160)
        thr_hr.addWidget(self.spin_hr_high)
        thresholds_layout.addLayout(thr_hr)

        # Температура
        thr_temp = QVBoxLayout()
        thr_temp.addWidget(QLabel("🌡️ Темп. макс (°C):"))
        self.spin_temp_high = QSpinBox()
        self.spin_temp_high.setRange(20, 50)
        self.spin_temp_high.setValue(30)
        thr_temp.addWidget(self.spin_temp_high)
        thresholds_layout.addLayout(thr_temp)

        # Батарея
        thr_batt = QVBoxLayout()
        thr_batt.addWidget(QLabel("🔋 Батарея мин (%):"))
        self.spin_batt_low = QSpinBox()
        self.spin_batt_low.setRange(5, 50)
        self.spin_batt_low.setValue(20)
        thr_batt.addWidget(self.spin_batt_low)
        thresholds_layout.addLayout(thr_batt)

        # Cooldown
        thr_cd = QVBoxLayout()
        thr_cd.addWidget(QLabel("⏱️ Cooldown (сек):"))
        self.spin_cooldown = QSpinBox()
        self.spin_cooldown.setRange(10, 3600)
        self.spin_cooldown.setValue(60)
        thr_cd.addWidget(self.spin_cooldown)
        thresholds_layout.addLayout(thr_cd)

        notify_layout.addLayout(thresholds_layout)

        self.btn_test_notify = QPushButton("🔔 Тест уведомления")
        notify_layout.addWidget(self.btn_test_notify)

        layout.addWidget(notify_group)

        layout.addStretch()

    def _connect_signals(self):
        # CSV
        self.btn_start_log.clicked.connect(self._on_start_log)
        self.btn_stop_log.clicked.connect(self._on_stop_log)
        self.btn_open_csv_folder.clicked.connect(
            lambda: self._open_folder(self.data_logger.export_dir))

        # Charts
        self.btn_export_chart.clicked.connect(self._on_export_chart)
        self.btn_export_all.clicked.connect(self._on_export_all_charts)
        self.btn_open_charts_folder.clicked.connect(
            lambda: self._open_folder(self.chart_exporter.export_dir))

        # MQTT
        self.btn_mqtt_connect.clicked.connect(self._on_mqtt_connect)
        self.btn_mqtt_disconnect.clicked.connect(self._on_mqtt_disconnect)

        # Notifier
        self.chk_enable_notify.toggled.connect(
            lambda v: self.notifier.configure(enabled=v))
        self.spin_hr_high.valueChanged.connect(
            lambda v: self.notifier.configure(thresholds={"heart_rate_high": v}))
        self.spin_temp_high.valueChanged.connect(
            lambda v: self.notifier.configure(thresholds={"temperature_high": v}))
        self.spin_batt_low.valueChanged.connect(
            lambda v: self.notifier.configure(thresholds={"battery_low": v}))
        self.spin_cooldown.valueChanged.connect(
            lambda v: self.notifier.configure(cooldown=v))
        self.btn_test_notify.clicked.connect(self._on_test_notify)

        # Сигналы от сервисов
        self.data_logger.log_saved.connect(self._on_log_saved)
        self.mqtt_service.connected.connect(self._on_mqtt_connected)
        self.mqtt_service.disconnected.connect(self._on_mqtt_disconnected)

    def _open_folder(self, path):
        import os
        os.makedirs(path, exist_ok=True)
        os.startfile(str(path))

    # === CSV ===
    def _on_start_log(self):
        filename = self.data_logger.start_session()
        if filename:
            self.btn_start_log.setEnabled(False)
            self.btn_stop_log.setEnabled(True)
            self.log_status.setText(f"🔴 Запись: {filename.name}")

    def _on_stop_log(self):
        self.data_logger.stop_session()
        self.btn_start_log.setEnabled(True)
        self.btn_stop_log.setEnabled(False)
        self.log_status.setText("⚪ Не записывается")

    def _on_log_saved(self, msg):
        self.log_status.setText(msg)

    # === Charts ===
    def _on_export_chart(self):
        device_name = self.device_combo.currentText()
        device = self.device_tabs.get(device_name)
        if not device or not hasattr(device, 'plot') and not hasattr(device, 'hr_plot') and not hasattr(device,
                                                                                                        'speed_plot'):
            return

        # Ищем график в устройстве
        plot = getattr(device, 'plot', None) or getattr(device, 'hr_plot', None) or getattr(device, 'speed_plot', None)
        if plot:
            self.chart_exporter.export_plot(plot, filename=f"{device_name.replace(' ', '_')}")

    def _on_export_all_charts(self):
        plots = {}
        for name, device in self.device_tabs.items():
            plot = getattr(device, 'plot', None) or getattr(device, 'hr_plot', None) or getattr(device, 'speed_plot',
                                                                                                None)
            if plot:
                plots[name.replace(' ', '_')] = plot

        if plots:
            self.chart_exporter.export_multiple(plots, session_name="all_devices")

    # === MQTT ===
    def _on_mqtt_connect(self):
        self.mqtt_service.configure(
            host=self.mqtt_host.text(),
            port=self.mqtt_port.value(),
            username=self.mqtt_user.text(),
            password=self.mqtt_pass.text()
        )
        self.mqtt_service.connect_async()
        self.mqtt_status.setText("🟡 Подключение...")

    def _on_mqtt_disconnect(self):
        self.mqtt_service.disconnect()

    def _on_mqtt_connected(self):
        self.btn_mqtt_connect.setEnabled(False)
        self.btn_mqtt_disconnect.setEnabled(True)
        self.mqtt_status.setText("🟢 Подключено к MQTT")

    def _on_mqtt_disconnected(self):
        self.btn_mqtt_connect.setEnabled(True)
        self.btn_mqtt_disconnect.setEnabled(False)
        self.mqtt_status.setText("⚪ Отключено")

    # === Notifier ===
    def _on_test_notify(self):
        self.notifier.notify(
            title="🔔 Тест уведомления",
            message="Если вы видите это — уведомления работают!",
            key="test"
        )