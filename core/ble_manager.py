import asyncio
from bleak import BleakScanner, BleakClient
from PyQt6.QtCore import QObject, pyqtSignal


class BLEManager(QObject):
    """Централизованный менеджер BLE-соединений"""

    device_discovered = pyqtSignal(str, str)  # name, address
    scan_finished = pyqtSignal()
    connected = pyqtSignal(str)  # address
    disconnected = pyqtSignal()
    notification = pyqtSignal(str, bytes)  # char_uuid, data
    log = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.client: BleakClient | None = None
        self._subscriptions = {}  # char_uuid -> callback

    async def scan(self, timeout=5.0):
        self.log.emit("🔍 Сканирование BLE-устройств...")
        try:
            devices = await BleakScanner.discover(timeout=timeout)
            for d in devices:
                name = d.name or "Unknown"
                self.device_discovered.emit(name, d.address)
            self.log.emit(f"✅ Найдено устройств: {len(devices)}")
        except Exception as e:
            self.log.emit(f"❌ Ошибка сканирования: {e}")
        finally:
            self.scan_finished.emit()

    async def connect(self, address):
        try:
            self.log.emit(f"🔗 Подключение к {address}...")
            self.client = BleakClient(address)
            await self.client.connect()
            self.log.emit(f"✅ Подключено к {address}")
            self.connected.emit(address)
            return True
        except Exception as e:
            self.log.emit(f"❌ Ошибка подключения: {e}")
            return False

    async def disconnect(self):
        if self.client and self.client.is_connected:
            try:
                # Отписываемся от всех уведомлений
                for char_uuid in list(self._subscriptions.keys()):
                    try:
                        await self.client.stop_notify(char_uuid)
                    except Exception:
                        pass
                self._subscriptions.clear()

                # Отключаемся с таймаутом
                await asyncio.wait_for(self.client.disconnect(), timeout=3.0)
                self.log.emit("🔌 Отключено")
            except asyncio.TimeoutError:
                self.log.emit("⚠️ Таймаут отключения")
            except Exception as e:
                self.log.emit(f"⚠️ Ошибка отключения: {e}")
            finally:
                self.client = None
                self.disconnected.emit()

    async def subscribe(self, char_uuid):
        if not self.client or not self.client.is_connected:
            self.log.emit("❌ Нет соединения")
            return

        def handler(sender, data):
            self.notification.emit(char_uuid, bytes(data))

        await self.client.start_notify(char_uuid, handler)
        self._subscriptions[char_uuid] = handler
        self.log.emit(f"📡 Подписка на {char_uuid}")

    async def write(self, char_uuid, data: bytes, response=True):
        if not self.client or not self.client.is_connected:
            self.log.emit("❌ Нет соединения")
            return False
        try:
            await self.client.write_gatt_char(char_uuid, data, response=response)
            self.log.emit(f"📤 → {data.hex(' ')}")
            return True
        except Exception as e:
            self.log.emit(f"❌ Ошибка записи: {e}")
            return False

    async def read(self, char_uuid):
        if not self.client or not self.client.is_connected:
            return None
        try:
            data = await self.client.read_gatt_char(char_uuid)
            return bytes(data)
        except Exception as e:
            self.log.emit(f"❌ Ошибка чтения: {e}")
            return None

    def get_services(self):
        if not self.client:
            return []
        return list(self.client.services)

    @property
    def is_connected(self):
        return self.client is not None and self.client.is_connected