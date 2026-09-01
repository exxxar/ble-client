import sys
import asyncio
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QListWidget, QTextEdit, 
                             QLabel, QLineEdit, QTabWidget, QGroupBox, QSpinBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from bleak import BleakScanner, BleakClient
import struct

class BLEWorker(QThread):
    """Поток для BLE-операций"""
    device_found = pyqtSignal(str, str)  # name, address
    scan_finished = pyqtSignal()
    connected = pyqtSignal(bool)
    notification_received = pyqtSignal(str, str)  # char_uuid, data_hex
    log_message = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.client = None
        self.loop = None
        self.running = True
        
    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
    
    async def scan(self):
        self.log_message.emit("🔍 Сканирование...")
        devices = await BleakScanner.discover(timeout=5.0)
        for device in devices:
            self.device_found.emit(device.name or "Unknown", device.address)
        self.scan_finished.emit()
    
    async def connect(self, address):
        try:
            self.client = BleakClient(address)
            await self.client.connect()
            self.connected.emit(True)
            self.log_message.emit(f"✅ Подключено к {address}")
        except Exception as e:
            self.log_message.emit(f"❌ Ошибка: {e}")
            self.connected.emit(False)
    
    async def disconnect(self):
        if self.client:
            await self.client.disconnect()
            self.connected.emit(False)
            self.log_message.emit("🔌 Отключено")
    
    async def subscribe(self, char_uuid):
        def handler(sender, data):
            self.notification_received.emit(char_uuid, data.hex(' '))
        
        await self.client.start_notify(char_uuid, handler)
        self.log_message.emit(f"📡 Подписка на {char_uuid}")
    
    async def write(self, char_uuid, data):
        await self.client.write_gatt_char(char_uuid, data, response=True)
        self.log_message.emit(f"📤 Отправлено: {data.hex(' ')}")

class BLEClientGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BLE Client для эмулятора устройств")
        self.setGeometry(100, 100, 900, 700)
        
        self.worker = BLEWorker()
        self.worker.start()
        
        self.init_ui()
        self.connect_signals()
    
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Вкладки
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # Вкладка 1: Сканирование и подключение
        scan_tab = QWidget()
        scan_layout = QVBoxLayout(scan_tab)
        
        self.device_list = QListWidget()
        scan_layout.addWidget(QLabel("Найденные устройства:"))
        scan_layout.addWidget(self.device_list)
        
        btn_layout = QHBoxLayout()
        self.btn_scan = QPushButton("🔍 Сканировать")
        self.btn_connect = QPushButton("🔗 Подключиться")
        self.btn_disconnect = QPushButton("🔌 Отключиться")
        self.btn_disconnect.setEnabled(False)
        
        btn_layout.addWidget(self.btn_scan)
        btn_layout.addWidget(self.btn_connect)
        btn_layout.addWidget(self.btn_disconnect)
        scan_layout.addLayout(btn_layout)
        
        tabs.addTab(scan_tab, "Подключение")
        
        # Вкладка 2: Управление лампочкой
        bulb_tab = QWidget()
        bulb_layout = QVBoxLayout(bulb_tab)
        
        # Вкл/Выкл
        power_group = QGroupBox("Питание")
        power_layout = QHBoxLayout(power_group)
        self.btn_bulb_on = QPushButton("💡 Включить")
        self.btn_bulb_off = QPushButton("🌑 Выключить")
        power_layout.addWidget(self.btn_bulb_on)
        power_layout.addWidget(self.btn_bulb_off)
        bulb_layout.addWidget(power_group)
        
        # Яркость
        brightness_group = QGroupBox("Яркость")
        brightness_layout = QHBoxLayout(brightness_group)
        self.spin_brightness = QSpinBox()
        self.spin_brightness.setRange(0, 100)
        self.spin_brightness.setValue(100)
        self.btn_set_brightness = QPushButton("Установить")
        brightness_layout.addWidget(self.spin_brightness)
        brightness_layout.addWidget(QLabel("%"))
        brightness_layout.addWidget(self.btn_set_brightness)
        bulb_layout.addWidget(brightness_group)
        
        # Цвет
        color_group = QGroupBox("Цвет (RGB)")
        color_layout = QHBoxLayout(color_group)
        self.edit_r = QLineEdit("255")
        self.edit_g = QLineEdit("200")
        self.edit_b = QLineEdit("100")
        self.btn_set_color = QPushButton("Установить цвет")
        color_layout.addWidget(QLabel("R:"))
        color_layout.addWidget(self.edit_r)
        color_layout.addWidget(QLabel("G:"))
        color_layout.addWidget(self.edit_g)
        color_layout.addWidget(QLabel("B:"))
        color_layout.addWidget(self.edit_b)
        color_layout.addWidget(self.btn_set_color)
        bulb_layout.addWidget(color_group)
        
        tabs.addTab(bulb_tab, "💡 Лампочка")
        
        # Вкладка 3: Управление замком
        lock_tab = QWidget()
        lock_layout = QVBoxLayout(lock_tab)
        
        # PIN
        pin_group = QGroupBox("Аутентификация")
        pin_layout = QHBoxLayout(pin_group)
        self.edit_pin = QLineEdit("1234")
        self.btn_auth = QPushButton("🔑 Войти")
        pin_layout.addWidget(QLabel("PIN:"))
        pin_layout.addWidget(self.edit_pin)
        pin_layout.addWidget(self.btn_auth)
        lock_layout.addWidget(pin_group)
        
        # Управление
        lock_control = QGroupBox("Управление")
        lock_control_layout = QHBoxLayout(lock_control)
        self.btn_lock_open = QPushButton("🔓 Открыть")
        self.btn_lock_close = QPushButton("🔒 Закрыть")
        lock_control_layout.addWidget(self.btn_lock_open)
        lock_control_layout.addWidget(self.btn_lock_close)
        lock_layout.addWidget(lock_control)
        
        tabs.addTab(lock_tab, "🔒 Замок")
        
        # Лог
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(QLabel("📋 Лог:"))
        layout.addWidget(self.log_text)
        
        # UUID характеристики (для всех вкладок)
        uuid_layout = QHBoxLayout()
        uuid_layout.addWidget(QLabel("UUID характеристики:"))
        self.edit_uuid = QLineEdit()
        self.btn_subscribe = QPushButton("📡 Подписаться")
        uuid_layout.addWidget(self.edit_uuid)
        uuid_layout.addWidget(self.btn_subscribe)
        layout.addLayout(uuid_layout)
    
    def connect_signals(self):
        self.btn_scan.clicked.connect(self.on_scan)
        self.btn_connect.clicked.connect(self.on_connect)
        self.btn_disconnect.clicked.connect(self.on_disconnect)
        self.btn_subscribe.clicked.connect(self.on_subscribe)
        
        # Лампочка
        self.btn_bulb_on.clicked.connect(lambda: self.send_command("0101"))
        self.btn_bulb_off.clicked.connect(lambda: self.send_command("0100"))
        self.btn_set_brightness.clicked.connect(self.on_set_brightness)
        self.btn_set_color.clicked.connect(self.on_set_color)
        
        # Замок
        self.btn_auth.clicked.connect(self.on_auth)
        self.btn_lock_open.clicked.connect(lambda: self.send_command("20"))
        self.btn_lock_close.clicked.connect(lambda: self.send_command("21"))
        
        # Worker signals
        self.worker.device_found.connect(self.on_device_found)
        self.worker.scan_finished.connect(self.on_scan_finished)
        self.worker.connected.connect(self.on_connected)
        self.worker.notification_received.connect(self.on_notification)
        self.worker.log_message.connect(self.log)
    
    def log(self, message):
        self.log_text.append(f"[{QTime.currentTime().toString('HH:mm:ss')}] {message}")
    
    def on_scan(self):
        self.device_list.clear()
        asyncio.run_coroutine_threadsafe(self.worker.scan(), self.worker.loop)
    
    def on_device_found(self, name, address):
        self.device_list.addItem(f"{name} [{address}]")
    
    def on_scan_finished(self):
        self.log("✅ Сканирование завершено")
    
    def on_connect(self):
        selected = self.device_list.currentItem()
        if not selected:
            self.log("❌ Выберите устройство")
            return
        
        address = selected.text().split('[')[1].rstrip(']')
        asyncio.run_coroutine_threadsafe(self.worker.connect(address), self.worker.loop)
    
    def on_connected(self, success):
        self.btn_connect.setEnabled(not success)
        self.btn_disconnect.setEnabled(success)
    
    def on_disconnect(self):
        asyncio.run_coroutine_threadsafe(self.worker.disconnect(), self.worker.loop)
    
    def on_subscribe(self):
        uuid = self.edit_uuid.text().strip()
        if not uuid:
            self.log("❌ Введите UUID")
            return
        asyncio.run_coroutine_threadsafe(self.worker.subscribe(uuid), self.worker.loop)
    
    def send_command(self, hex_cmd):
        uuid = self.edit_uuid.text().strip()
        if not uuid:
            self.log("❌ Введите UUID характеристики")
            return
        
        data = bytes.fromhex(hex_cmd)
        asyncio.run_coroutine_threadsafe(self.worker.write(uuid, data), self.worker.loop)
    
    def on_set_brightness(self):
        brightness = self.spin_brightness.value()
        hex_cmd = f"02{brightness:02X}"
        self.send_command(hex_cmd)
    
    def on_set_color(self):
        try:
            r = int(self.edit_r.text())
            g = int(self.edit_g.text())
            b = int(self.edit_b.text())
            hex_cmd = f"03{r:02X}{g:02X}{b:02X}"
            self.send_command(hex_cmd)
        except ValueError:
            self.log("❌ Неверный формат RGB")
    
    def on_auth(self):
        pin = self.edit_pin.text()
        hex_cmd = "10" + pin.encode().hex()
        self.send_command(hex_cmd)
    
    def on_notification(self, char_uuid, data_hex):
        self.log(f"📥 [{char_uuid}] {data_hex}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BLEClientGUI()
    window.show()
    sys.exit(app.exec())