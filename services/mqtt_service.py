import json
import paho.mqtt.client as mqtt
from PyQt6.QtCore import QObject, pyqtSignal, QTimer


class MQTTService(QObject):
    """MQTT интеграция с Home Assistant через MQTT Discovery"""

    connected = pyqtSignal()
    disconnected = pyqtSignal()
    error = pyqtSignal(str)
    published = pyqtSignal(str, str)  # topic, payload

    def __init__(self):
        super().__init__()
        self.client = mqtt.Client(protocol=mqtt.MQTTv311)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish

        self._config = {
            "host": "homeassistant.local",
            "port": 1883,
            "username": "",
            "password": "",
            "discovery_prefix": "homeassistant",
            "base_topic": "ble_emulator",
            "device_id": "ble_emulator_001",
        }

        self._connected = False
        self._registered_devices = set()

    def configure(self, host, port=1883, username="", password="",
                  discovery_prefix="homeassistant", base_topic="ble_emulator"):
        """Настроить подключение"""
        self._config.update({
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "discovery_prefix": discovery_prefix,
            "base_topic": base_topic,
        })

        if username:
            self.client.username_pw_set(username, password)

    def connect_async(self):
        """Асинхронное подключение"""
        try:
            self.client.connect(
                self._config["host"],
                self._config["port"],
                keepalive=60
            )
            self.client.loop_start()
        except Exception as e:
            self.error.emit(f"❌ Ошибка подключения MQTT: {e}")

    def disconnect(self):
        """Отключиться"""
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception:
            pass

    @property
    def is_connected(self):
        return self._connected

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._connected = True
            self.connected.emit()
        else:
            self.error.emit(f"❌ MQTT ошибка подключения: код {rc}")

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False
        self.disconnected.emit()

    def _on_publish(self, client, userdata, mid):
        pass

    def register_sensor(self, device_name: str, metric: str,
                        unit: str = "", device_class: str = None,
                        icon: str = None):
        """
        Зарегистрировать сенсор в Home Assistant через MQTT Discovery

        :param device_name: имя устройства (например, "Polar H10")
        :param metric: метрика (например, "heart_rate")
        :param unit: единица измерения
        :param device_class: класс устройства HA (temperature, humidity и т.д.)
        :param icon: MDI иконка (например, "mdi:heart-pulse")
        """
        if not self._connected:
            return

        key = f"{device_name}_{metric}"
        if key in self._registered_devices:
            return

        device_id = f"{self._config['device_id']}_{device_name.lower().replace(' ', '_')}"
        object_id = f"{device_id}_{metric}"

        config_topic = (
            f"{self._config['discovery_prefix']}/sensor/"
            f"{object_id}/config"
        )

        config_payload = {
            "name": f"{device_name} {metric.replace('_', ' ').title()}",
            "state_topic": f"{self._config['base_topic']}/{device_id}/{metric}/state",
            "unique_id": object_id,
            "device": {
                "identifiers": [device_id],
                "name": device_name,
                "model": "BLE Emulator",
                "manufacturer": "Custom",
                "sw_version": "1.0.0",
            },
        }

        if unit:
            config_payload["unit_of_measurement"] = unit
        if device_class:
            config_payload["device_class"] = device_class
        if icon:
            config_payload["icon"] = icon

        self._publish(config_topic, json.dumps(config_payload), retain=True)
        self._registered_devices.add(key)

    def publish_value(self, device_name: str, metric: str, value):
        """Опубликовать значение сенсора"""
        if not self._connected:
            return

        device_id = f"{self._config['device_id']}_{device_name.lower().replace(' ', '_')}"
        topic = f"{self._config['base_topic']}/{device_id}/{metric}/state"

        payload = {
            "value": value,
            "timestamp": int(__import__('time').time() * 1000),
        }

        self._publish(topic, json.dumps(payload))

    def publish_availability(self, device_name: str, online: bool):
        """Опубликовать статус доступности устройства"""
        if not self._connected:
            return

        device_id = f"{self._config['device_id']}_{device_name.lower().replace(' ', '_')}"
        topic = f"{self._config['base_topic']}/{device_id}/availability"
        self._publish(topic, "online" if online else "offline", retain=True)

    def _publish(self, topic, payload, retain=False):
        try:
            info = self.client.publish(topic, payload, retain=retain)
            self.published.emit(topic, payload[:100])
        except Exception as e:
            self.error.emit(f"❌ MQTT publish error: {e}")

    def unregister_all(self):
        """Удалить все зарегистрированные сенсоры из HA"""
        if not self._connected:
            return

        for key in list(self._registered_devices):
            device_name, metric = key.rsplit('_', 1)
            device_id = f"{self._config['device_id']}_{device_name.lower().replace(' ', '_')}"
            object_id = f"{device_id}_{metric}"
            config_topic = (
                f"{self._config['discovery_prefix']}/sensor/{object_id}/config"
            )
            self._publish(config_topic, "", retain=True)

        self._registered_devices.clear()