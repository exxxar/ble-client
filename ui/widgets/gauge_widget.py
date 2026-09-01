from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QConicalGradient, QColor, QPen, QFont
from PyQt6.QtCore import Qt, QRectF


class GaugeWidget(QWidget):
    """Круговой индикатор (спидометр/батарея)"""

    def __init__(self, title="", min_val=0, max_val=100,
                 unit="", color="#00aaff", parent=None):
        super().__init__(parent)
        self.title = title
        self.min_val = min_val
        self.max_val = max_val
        self.unit = unit
        self.value = min_val
        self.color = QColor(color)
        self.setMinimumSize(200, 200)

    def set_value(self, value):
        self.value = max(self.min_val, min(self.max_val, value))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        size = min(w, h) - 20
        rect = QRectF((w - size) / 2, (h - size) / 2, size, size)

        # Фон (серая дуга)
        pen_bg = QPen(QColor(60, 60, 80), 20)
        pen_bg.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_bg)
        painter.drawArc(rect, 225 * 16, -270 * 16)

        # Значение (цветная дуга)
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        angle = int(270 * 16 * ratio)

        pen_val = QPen(self.color, 20)
        pen_val.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_val)
        painter.drawArc(rect, 225 * 16, -angle)

        # Текст значения
        painter.setPen(QColor(255, 255, 255))
        font = QFont("Arial", int(size / 6), QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter,
                         f"{int(self.value)}{self.unit}")

        # Заголовок
        font_title = QFont("Arial", int(size / 15))
        painter.setFont(font_title)
        painter.setPen(QColor(180, 180, 200))
        title_rect = QRectF(0, h - 30, w, 30)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, self.title)