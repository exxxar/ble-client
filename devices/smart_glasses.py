import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QListWidget, QGroupBox, QFileDialog)
from PyQt6.QtCore import Qt
from devices.base_device import BaseDevice
from ui.widgets.media_player import MediaPlayer


class SmartGlassesDevice(BaseDevice):
    DEVICE_NAME = "Ray-Ban Meta"
    SERVICE_UUID = "f0001843-0451-4000-b000-000000000000"
    CHAR_UUID = "f0002b1a-0451-4000-b000-000000000000"
    ICON = "🕶️"

    def init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel(f"{self.ICON} {self.DEVICE_NAME}")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #aa66ff;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Медиаплеер
        self.player = MediaPlayer()
        layout.addWidget(self.player)

        # Плейлист
        playlist_group = QGroupBox("📁 Пресеты (папка presets/)")
        playlist_layout = QVBoxLayout(playlist_group)

        self.file_list = QListWidget()
        self.file_list.itemDoubleClicked.connect(self._on_file_selected)
        playlist_layout.addWidget(self.file_list)

        btn_layout = QHBoxLayout()
        self.btn_refresh = QPushButton("🔄 Обновить")
        self.btn_open_folder = QPushButton("📂 Открыть папку")
        self.btn_refresh.clicked.connect(self._load_presets)
        self.btn_open_folder.clicked.connect(self._open_presets_folder)
        btn_layout.addWidget(self.btn_refresh)
        btn_layout.addWidget(self.btn_open_folder)
        playlist_layout.addLayout(btn_layout)

        layout.addWidget(playlist_group)

        # Информация о текущем медиа
        self.info_label = QLabel("Выберите файл из плейлиста")
        self.info_label.setStyleSheet("color: #aaa; padding: 10px;")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info_label)

        self._presets_dir = "presets"
        self._files = []
        self._load_presets()

    def _load_presets(self):
        self.file_list.clear()
        self._files = []

        if not os.path.exists(self._presets_dir):
            os.makedirs(self._presets_dir, exist_ok=True)

        for f in os.listdir(self._presets_dir):
            if f.lower().endswith(('.mp3', '.mp4', '.wav', '.avi', '.mkv')):
                self._files.append(os.path.join(self._presets_dir, f))
                self.file_list.addItem(f)

        if not self._files:
            self.info_label.setText("Папка presets/ пуста. Добавьте аудио/видео файлы.")

    def _open_presets_folder(self):
        os.makedirs(self._presets_dir, exist_ok=True)
        os.startfile(os.path.abspath(self._presets_dir))

    def _on_file_selected(self, item):
        idx = self.file_list.row(item)
        if 0 <= idx < len(self._files):
            file_path = self._files[idx]
            self.player.play_file(file_path, item.text())
            self.info_label.setText(f"▶ Воспроизведение: {item.text()}")

    def on_notification(self, data: bytes):
        # Очки отправляют метаданные медиа: "filename|size|type"
        try:
            text = data.decode('utf-8', errors='ignore')
            parts = text.split('|')
            if len(parts) >= 3:
                filename, size, media_type = parts[0], parts[1], parts[2]
                self.info_label.setText(
                    f"📸 Очки передают: {filename} ({size} байт, {media_type})")
        except Exception:
            pass