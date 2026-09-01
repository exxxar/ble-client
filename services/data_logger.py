import csv
import os
import datetime
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal


class DataLogger(QObject):
    """Универсальный логгер данных в CSV"""

    log_saved = pyqtSignal(str)  # путь к файлу
    log_error = pyqtSignal(str)

    def __init__(self, export_dir="exports/csv"):
        super().__init__()
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

        self._current_file = None
        self._writer = None
        self._file_handle = None
        self._session_start = None
        self._is_logging = False
        self._row_count = 0

    @property
    def is_logging(self):
        return self._is_logging

    def start_session(self, session_name=None):
        """Начать новую сессию логирования"""
        if self._is_logging:
            self.stop_session()

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        name = session_name or f"session_{timestamp}"
        filename = self.export_dir / f"{name}.csv"

        try:
            self._file_handle = open(filename, 'w', newline='', encoding='utf-8')
            self._writer = csv.writer(self._file_handle)

            # Заголовок CSV
            self._writer.writerow([
                "timestamp", "epoch_ms", "device", "device_type",
                "metric", "value", "unit", "raw_hex"
            ])

            self._current_file = filename
            self._session_start = datetime.datetime.now()
            self._is_logging = True
            self._row_count = 0

            self.log_saved.emit(f"✅ Сессия начата: {filename.name}")
            return filename
        except Exception as e:
            self.log_error.emit(f"❌ Ошибка создания файла: {e}")
            return None

    def stop_session(self):
        """Остановить сессию"""
        if not self._is_logging:
            return

        self._is_logging = False
        if self._file_handle:
            self._file_handle.close()
            self._file_handle = None

        duration = datetime.datetime.now() - self._session_start if self._session_start else datetime.timedelta()
        self.log_saved.emit(
            f"⏹️ Сессия завершена: {self._current_file.name} "
            f"({self._row_count} записей, {duration.seconds} сек)"
        )

    def log(self, device_name: str, device_type: str,
            metric: str, value, unit: str = "", raw_hex: str = ""):
        """Записать одну строку данных"""
        if not self._is_logging or not self._writer:
            return

        now = datetime.datetime.now()
        epoch_ms = int(now.timestamp() * 1000)

        self._writer.writerow([
            now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            epoch_ms,
            device_name,
            device_type,
            metric,
            value,
            unit,
            raw_hex
        ])

        # Периодически сбрасываем буфер
        self._row_count += 1
        if self._row_count % 10 == 0:
            self._file_handle.flush()

    def get_session_file(self):
        return self._current_file

    def list_sessions(self):
        """Список всех сессий"""
        return sorted(self.export_dir.glob("*.csv"), reverse=True)

    def delete_old_sessions(self, days=7):
        """Удалить старые сессии"""
        cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
        deleted = 0
        for f in self.export_dir.glob("*.csv"):
            if datetime.datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
                f.unlink()
                deleted += 1
        return deleted