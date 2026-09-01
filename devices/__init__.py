"""
Модули для всех поддерживаемых BLE-устройств.
Каждый класс наследуется от BaseDevice и реализует свою логику.
"""

from .base_device import BaseDevice
from .fitness_tracker import FitnessTrackerDevice
from .smart_glasses import SmartGlassesDevice
from .home_sensor import HomeSensorDevice
from .headphones import HeadphonesDevice
from .cycling_sensor import CyclingSensorDevice
from .smart_watch import SmartWatchDevice
from .smart_bulb import SmartBulbDevice
from .smart_lock import SmartLockDevice

__all__ = [
    "BaseDevice",
    "FitnessTrackerDevice",
    "SmartGlassesDevice",
    "HomeSensorDevice",
    "HeadphonesDevice",
    "CyclingSensorDevice",
    "SmartWatchDevice",
    "SmartBulbDevice",
    "SmartLockDevice",
]