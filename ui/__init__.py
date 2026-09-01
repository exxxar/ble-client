"""
UI компоненты BLE-клиента.
Содержит главное окно, вкладки и переиспользуемые виджеты.
"""

from .main_window import MainWindow
from .connection_tab import ConnectionTab
from .log_panel import LogPanel

__all__ = [
    "MainWindow",
    "ConnectionTab",
    "LogPanel",
]