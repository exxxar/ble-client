import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import QTimer
import numpy as np
from collections import deque


class RealTimePlot(QWidget):
    """График в реальном времени с скользящим окном"""

    def __init__(self, title="График", y_label="Значение",
                 max_points=100, color=(0, 170, 255), parent=None):
        super().__init__(parent)
        self.max_points = max_points
        self.data = deque(maxlen=max_points)
        self.timestamps = deque(maxlen=max_points)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Настройка графика
        pg.setConfigOptions(antialias=True)
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('#1e1e2e')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel('left', y_label)
        self.plot_widget.setLabel('bottom', 'Время', 'с')
        self.plot_widget.setTitle(title)

        # Кривая
        pen = pg.mkPen(color=color, width=2)
        self.curve = self.plot_widget.plot(pen=pen)

        layout.addWidget(self.plot_widget)

        # Таймер обновления
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_plot)
        self.timer.start(100)  # 10 FPS

    def add_point(self, value):
        """Добавить новую точку"""
        import time
        self.data.append(value)
        self.timestamps.append(time.time())

    def set_range(self, y_min, y_max):
        self.plot_widget.setYRange(y_min, y_max)

    def clear(self):
        self.data.clear()
        self.timestamps.clear()

    def _update_plot(self):
        if len(self.data) < 2:
            return
        # Нормализуем время (от 0 до N секунд)
        t0 = self.timestamps[0]
        x = [t - t0 for t in self.timestamps]
        self.curve.setData(x, list(self.data))