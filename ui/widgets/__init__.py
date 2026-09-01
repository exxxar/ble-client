"""
Переиспользуемые UI-виджеты:
- RealTimePlot — график в реальном времени
- GaugeWidget — круговой индикатор
- MediaPlayer — аудио/видео плеер
"""

from .real_time_plot import RealTimePlot
from .gauge_widget import GaugeWidget
from .media_player import MediaPlayer

__all__ = [
    "RealTimePlot",
    "GaugeWidget",
    "MediaPlayer",
]