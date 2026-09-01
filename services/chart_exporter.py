import os
import datetime
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal
import pyqtgraph as pg
from pyqtgraph.exporters import ImageExporter


class ChartExporter(QObject):
    """Экспорт графиков pyqtgraph в PNG/SVG"""

    export_complete = pyqtSignal(str)  # путь к файлу
    export_error = pyqtSignal(str)

    def __init__(self, export_dir="exports/charts"):
        super().__init__()
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def export_plot(self, plot_widget, filename=None,
                    width=1200, height=600, format="png"):
        """
        Экспортировать PlotWidget в файл

        :param plot_widget: pyqtgraph.PlotWidget
        :param filename: имя файла (без расширения)
        :param width: ширина в пикселях
        :param height: высота в пикселях
        :param format: 'png' или 'svg'
        """
        if plot_widget is None:
            self.export_error.emit("❌ Нет графика для экспорта")
            return None

        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = filename or f"chart_{timestamp}"
            filepath = self.export_dir / f"{filename}.{format}"

            exporter = ImageExporter(plot_widget.plotItem)
            exporter.parameters()['width'] = width
            exporter.parameters()['height'] = height
            exporter.export(str(filepath))

            self.export_complete.emit(f"✅ График сохранён: {filepath.name}")
            return filepath
        except Exception as e:
            self.export_error.emit(f"❌ Ошибка экспорта: {e}")
            return None

    def export_multiple(self, plots: dict, session_name=None):
        """
        Экспортировать несколько графиков в папку сессии

        :param plots: dict {имя: plot_widget}
        :param session_name: имя папки
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = self.export_dir / (session_name or f"session_{timestamp}")
        session_dir.mkdir(parents=True, exist_ok=True)

        exported = []
        for name, plot_widget in plots.items():
            filepath = session_dir / f"{name}.png"
            try:
                exporter = ImageExporter(plot_widget.plotItem)
                exporter.parameters()['width'] = 1200
                exporter.parameters()['height'] = 600
                exporter.export(str(filepath))
                exported.append(filepath)
            except Exception as e:
                self.export_error.emit(f"❌ Ошибка экспорта {name}: {e}")

        if exported:
            self.export_complete.emit(
                f"✅ Экспортировано {len(exported)} графиков в {session_dir.name}/"
            )
        return exported