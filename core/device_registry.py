from devices.fitness_tracker import FitnessTrackerDevice
from devices.smart_glasses import SmartGlassesDevice
from devices.home_sensor import HomeSensorDevice
from devices.headphones import HeadphonesDevice
from devices.cycling_sensor import CyclingSensorDevice
from devices.smart_watch import SmartWatchDevice
from devices.smart_bulb import SmartBulbDevice
from devices.smart_lock import SmartLockDevice


# Реестр всех поддерживаемых устройств
DEVICE_REGISTRY = {
    "Polar H10": {
        "class": FitnessTrackerDevice,
        "icon": "💓",
        "description": "Фитнес-браслет с пульсометром",
    },
    "Ray-Ban Meta": {
        "class": SmartGlassesDevice,
        "icon": "🕶️",
        "description": "Умные очки с камерой",
    },
    "Xiaomi Temp": {
        "class": HomeSensorDevice,
        "icon": "🌡️",
        "description": "Датчик температуры и влажности",
    },
    "AirPods Pro": {
        "class": HeadphonesDevice,
        "icon": "🎧",
        "description": "Беспроводные наушники",
    },
    "Wahoo KICKR": {
        "class": CyclingSensorDevice,
        "icon": "🚴",
        "description": "Велодатчик скорости и каденса",
    },
    "Galaxy Watch": {
        "class": SmartWatchDevice,
        "icon": "⌚",
        "description": "Умные часы",
    },
    "Yeelight Bulb": {
        "class": SmartBulbDevice,
        "icon": "💡",
        "description": "Умная RGB лампочка",
    },
    "Aqara Lock": {
        "class": SmartLockDevice,
        "icon": "🔒",
        "description": "Умный замок с PIN",
    },
}


def get_device_by_name(name):
    """Определить устройство по имени из рекламы"""
    for key, info in DEVICE_REGISTRY.items():
        if key.lower() in name.lower():
            return info["class"]()
    return None