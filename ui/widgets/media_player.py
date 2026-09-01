from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QSlider)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import Qt, QUrl


class MediaPlayer(QWidget):
    """Универсальный медиаплеер (аудио + видео)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        # Видео-виджет
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(300)
        self.video_widget.setStyleSheet("background-color: #1e1e2e;")
        layout.addWidget(self.video_widget)

        # Информация о файле
        self.file_label = QLabel("Нет файла")
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_label.setStyleSheet("color: #ccc; font-size: 14px; padding: 5px;")
        layout.addWidget(self.file_label)

        # Контролы
        controls = QHBoxLayout()

        self.btn_play = QPushButton("▶ Play")
        self.btn_pause = QPushButton("⏸ Pause")
        self.btn_stop = QPushButton("⏹ Stop")

        for btn in (self.btn_play, self.btn_pause, self.btn_stop):
            btn.setMinimumHeight(40)
            controls.addWidget(btn)

        layout.addLayout(controls)

        # Слайдер позиции
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        layout.addWidget(self.slider)

        # Плеер
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)

        # Сигналы
        self.btn_play.clicked.connect(self.player.play)
        self.btn_pause.clicked.connect(self.player.pause)
        self.btn_stop.clicked.connect(self.player.stop)
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)

    def play_file(self, file_path, title=""):
        """Воспроизвести файл"""
        url = QUrl.fromLocalFile(file_path)
        self.player.setSource(url)
        self.file_label.setText(title or file_path.split('/')[-1])
        self.player.play()

    def stop(self):
        self.player.stop()

    def _on_position_changed(self, pos):
        if self.player.duration() > 0:
            self.slider.setValue(int(pos / self.player.duration() * 100))

    def _on_duration_changed(self, duration):
        self.slider.setRange(0, 100)